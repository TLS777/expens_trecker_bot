from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
engine = create_engine("sqlite:///finance.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()