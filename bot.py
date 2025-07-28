from telebot import TeleBot, types
from database import engine, Base, get_session
from models import User, Transaction
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


load_dotenv()


# Инициализация
TOKEN = os.getenv("TOKEN")
bot = TeleBot(TOKEN)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    session = get_session()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id, name=message.from_user.first_name)
        session.add(user)
        session.commit()
    bot.send_message(message.chat.id, "👋 Привет! Я бот для учета расходов.\n\n"
                                      "Доступные команды:\n"
                                      "/add – добавить транзакцию\n"
                                      "/stats – статистика")
    session.close()

# Добавление транзакции
@bot.message_handler(commands=['add'])
def add_transaction(message):
    bot.send_message(message.chat.id, "Введите сумму:")
    bot.register_next_step_handler(message, get_amount)

def get_amount(message):
    try:
        amount = float(message.text)
        bot.send_message(message.chat.id, "Введите категорию:")
        bot.register_next_step_handler(message, get_category, amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число!")

def get_category(message, amount):
    category = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("income", "expense")
    bot.send_message(message.chat.id, "Это доход или расход?", reply_markup=markup)
    bot.register_next_step_handler(message, save_transaction, amount, category)

def save_transaction(message, amount, category):
    type_ = message.text.lower()
    session = get_session()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()

    transaction = Transaction(user_id=user.id, amount=amount, category=category, type=type_)
    session.add(transaction)
    session.commit()
    session.close()

    bot.send_message(message.chat.id, "✅ Транзакция добавлена!", reply_markup=types.ReplyKeyboardRemove())

# Статистика
@bot.message_handler(commands=['stats'])
def stats(message):
    session = get_session()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.send_message(message.chat.id, "Вы не зарегистрированы.")
        session.close()
        return

    start_date = datetime.utcnow() - timedelta(days=30)
    transactions = session.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.created_at >= start_date
    ).all()

    income = sum(t.amount for t in transactions if t.type == "income")
    expense = sum(t.amount for t in transactions if t.type == "expense")
    balance = income - expense

    bot.send_message(message.chat.id,
        f"📊 Статистика за 30 дней:\n"
        f"Доход: {income}\n"
        f"Расход: {expense}\n"
        f"Баланс: {balance}"
    )
    session.close()

bot.polling()
