# src/main.py
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.middleware.require_login import RequireLoginMiddleware
from src.database.init import engine, init_db, AsyncSessionLocal
from src.database.models import Base
from src.api import auth, content

# lifespan context manager: open and close db connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Connecting to database...")
    await init_db(Base)
    app.state.db = AsyncSessionLocal
    yield
    # Shutdown
    print("Application shutdown: Closing database connections...")
    await engine.dispose()
    del app.state.db

app = FastAPI(lifespan=lifespan)
# Middleware
app.add_middleware(RequireLoginMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth")
app.include_router(content.router, prefix="/content")

# health check
@app.get("/health")
def health_check():
    return {"status": "ok"}