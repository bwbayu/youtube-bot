# src/services/content_services.py
from src.database.crud_content import get_user_by_id

from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_data(db: AsyncSession, user_id: str):
    user = await get_user_by_id(db, user_id)

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    return user