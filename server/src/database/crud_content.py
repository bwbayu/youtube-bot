# src/database/crud_content.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List

from src.database.models import User, Video, Comment
from src.schemas.comment import CommentCreate
from src.schemas.video import VideoCreate

async def get_user_by_id(db: AsyncSession, user_id: str):
    """
    Get user by user id
    """
    # QUESTION: what if user doesn't exist
    # ANSWER : handle None in handler
    query = select(User).filter_by(user_id=user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def insert_video(db: AsyncSession, video_data: VideoCreate) -> Video:
    """
    Insert one fetched video
    """
    query = select(Video).filter_by(video_id=video_data.video_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    # QUESTION: need upsert ?
    if not existing:
        video = Video(**video_data.model_dump())
        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video
    
    # existing
    return existing

async def get_video_by_id(db: AsyncSession, video_id: str):
    """
    get video by video id
    """
    query = select(Video).filter_by(video_id=video_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_videos(db: AsyncSession, playlist_id: str):
    """
    get all video from users (show videos)
    """
    query = select(Video).filter_by(playlist_id=playlist_id)
    result = await db.execute(query)
    return result.scalars().all()

async def update_last_fetch_comment(db: AsyncSession, video_id: str):
    """
    update last_fetch_comment everytime perform fetch comment from video
    """
    # get video data
    video_data = get_video_by_id(db, video_id)
    # QUESTION: what if video data doesn't exist
    if video_data:
        video_data.last_fetch_comment = datetime.now()
        await db.commit()

async def get_comments(db: AsyncSession, video_id: str):
    """
    get all comment from video (show comments)
    """
    query = select(Comment).filter_by(video_id=video_id)
    result = await db.execute(query)
    return result.scalars().all()

async def insert_comments(db: AsyncSession, comments: List[CommentCreate]):
    """
    insert comments
    """
    # QUESTION: what if the comment data only 1 ?
    db.add_all(comments)
    await db.commit()