# src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api import auth
from src.database.models import Base
from src.database.init import engine, init_db, SessionLocal

# lifespan context manager: open and close db connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Connecting to database...")
    init_db(Base)

    # simpan session factory di state app
    app.state.db = SessionLocal

    yield

    # Shutdown
    print("Application shutdown: Closing database connections...")
    engine.dispose()  # penting untuk release pool
    del app.state.db

app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(auth.router, prefix="/auth")

# health check
@app.get("/health")
def health_check():
    return {"status": "ok"}