# src/api/content.py
from src.services.content_service import get_user_data
from src.schemas.user import UserResponse
from src.database.init import get_async_db

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# QUESTION: what is the difference between using response_model and not
# ANSWER: validate response data, serialize sqlalchemy model to dict, consistency
@router.get("/user", response_model=UserResponse)
async def get_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    user_id = getattr(request.state, "user_id")
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # get user data by user id
    user = await get_user_data(db, user_id)

    if isinstance(user, JSONResponse):
        return user

    # construct user data
    user_data = {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "channel_id": user.channel_id,
        "custom_url": user.custom_url
    }

    return user_data