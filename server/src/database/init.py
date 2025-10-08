# src/database/init.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRESQL_URL")
engine = create_async_engine(DATABASE_URL) # create async engine
AsyncSessionLocal = sessionmaker( # create async session
    bind=engine,
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False
    )

async def init_db(Base): # create database and schema if not available
    print("Creating tables if not exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema initialized.")


async def get_async_db(): # get database session
    async with AsyncSessionLocal() as session:
        yield session