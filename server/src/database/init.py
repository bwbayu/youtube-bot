# src/database/init.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRESQL_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(Base):
    print("Creating tables if not exist...")
    Base.metadata.create_all(bind=engine)
    print("Database schema initialized.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()