# src/database/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from sqlalchemy.future import select

from src.database.models import User, RefreshToken
from src.schemas.user import UserCreate

async def save_user(db: AsyncSession, user_data: UserCreate):
    """
    Create new user if not exists
    """
    query = select(User).filter_by(user_id=user_data.user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        user = User(**user_data.model_dump())
        db.add(user)
        await db.commit()

async def store_refresh_token(db: AsyncSession, refresh_token_data: dict):
    """
    save refresh token data for each user
    """
    # check refresh token data based on user id
    stmt = select(RefreshToken).filter_by(user_id=refresh_token_data["user_id"])
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # update refresh token and expires_at
        existing.refresh_token_encrypted = refresh_token_data["refresh_token_encrypted"]
        existing.expires_at = refresh_token_data["expires_at"]
        existing.session_id = refresh_token_data["session_id"]
    else:
        # refresh token data doesn't exist
        refresh_token_obj = RefreshToken(**refresh_token_data)
        db.add(refresh_token_obj)

    await db.commit()

async def update_session_id(db: AsyncSession, user_id: str, old_session_id: str, new_session_id: str):
    """
    update session id on refresh token table when session is expired
    """
    stmt = select(RefreshToken).filter_by(user_id=user_id, session_id=old_session_id)
    result = await db.execute(stmt)
    token_data = result.scalar_one_or_none()

    if not token_data:
        return False

    token_data.session_id = new_session_id
    token_data.expires_at = datetime.now() + timedelta(days=1)
    await db.commit()
    return True

async def get_refresh_token_by_session(db: AsyncSession, session_id: str):
    """
    get refresh token data by session id
    """
    stmt = select(RefreshToken).filter_by(session_id=session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def delete_refresh_token_by_session(db: AsyncSession, session_id: str):
    """
    delete refresh token data by session id when user logout
    """
    stmt = select(RefreshToken).filter_by(session_id=session_id)
    result = await db.execute(stmt)
    ref_token = result.scalar_one_or_none()
    if ref_token:
        await db.delete(ref_token)
        await db.commit()