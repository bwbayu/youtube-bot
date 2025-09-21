# src/database.py
import os
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from dotenv import load_dotenv
from typing import Annotated
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("POSTGRESQL_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# lifespan context manager: open and close db connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Connecting to database...")
    init_db()

    # simpan session factory di state app
    app.state.db = SessionLocal

    yield

    # Shutdown
    print("Application shutdown: Closing database connections...")
    engine.dispose()  # penting untuk release pool
    del app.state.db

db_dependency = Annotated[Session, Depends(get_db())]

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True) # sub from token id
    name = Column(String, nullable=False) # name from token id
    email = Column(String, nullable=False) # email from token id
    channel_id = Column(String) # from channel data
    custom_url = Column(String) # from channel data

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime) # now + refresh_token_expires_in (from decode token id)