from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.init import get_async_db
from src.handlers.auth_handler import (
    login_handler,
    callback_handler,
    logout_handler,
    refresh_handler
)

router = APIRouter()

@router.get("/login")
async def login(request: Request):
    return await login_handler(request)

@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_async_db)):
    return await callback_handler(request, db)

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_async_db)):
    return await logout_handler(request, response, db)

@router.post("/refresh")
async def refresh_access_token(request: Request, db: AsyncSession = Depends(get_async_db)):
    return await refresh_handler(request, db)
