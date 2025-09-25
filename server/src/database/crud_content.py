# src/database/crud_content.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database.models import User

async def get_user_by_id(db: AsyncSession, user_id: str):
    """
    Get user by user id
    """
    # QUESTION: what if user doesn't exist
    # ANSWER : handle None in handler
    stmt = select(User).filter_by(user_id=user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()