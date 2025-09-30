# src/database/crud_content.py
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, func, update
from datetime import datetime, timezone
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

async def get_videos(db: AsyncSession, playlist_id: str, page: int = 1, limit: int = 10):
    """
    get all video from users (show videos) with pagination
    """
    offset = (page - 1) * limit
    query = (
        select(Video)
        .filter_by(playlist_id=playlist_id)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_count_videos(db: AsyncSession, playlist_id: str):
    """
    get count user videos
    """
    count_query = select(func.count()).select_from(Video).filter_by(playlist_id=playlist_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    return total

async def update_last_fetch_comment(db: AsyncSession, video_id: str):
    """
    update last_fetch_comment everytime perform fetch comment from video
    """
    # get video data
    video_data = await get_video_by_id(db, video_id)
    # QUESTION: what if video data doesn't exist
    if video_data:
        video_data.last_fetch_comment = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(video_data)

async def get_comments(db: AsyncSession, video_id: str, page: int = 1, limit: int = 10):
    """
    get all comment from video (show comments) with pagination
    """
    offset = (page - 1) * limit
    query = (
        select(Comment)
        .filter_by(video_id=video_id, moderation_status="published")
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_count_comments(db: AsyncSession, video_id: str):
    """
    get count comment from video
    """
    count_query = select(func.count()).select_from(Comment).filter_by(video_id=video_id, moderation_status="published")
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    return total

async def insert_comments(db: AsyncSession, comments: List[CommentCreate]):
    """
    insert comments
    """
    if not comments:
        return

    values = [comment.model_dump() for comment in comments]
    stmt = insert(Comment).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["comment_id"],
        set_={
            "text": stmt.excluded.text,
            "updated_at": stmt.excluded.updated_at,
            "author_display_name": stmt.excluded.author_display_name,
            "is_judi": case(
                (
                    (Comment.text != stmt.excluded.text) |
                    (Comment.author_display_name != stmt.excluded.author_display_name),
                    None
                ),
                else_=Comment.is_judi
            )
        },
        where=(
            (Comment.text != stmt.excluded.text) |
            (Comment.updated_at != stmt.excluded.updated_at) |
            (Comment.author_display_name != stmt.excluded.author_display_name)
        )
    )

    await db.execute(stmt)
    await db.commit()

async def update_moderation_status_comment(
    db: AsyncSession,
    list_comment_id: List[str],
    status: str = 'heldForReview' # rejected
):
    if not list_comment_id:
        return
        
    stmt = (
        update(Comment)
        .where(Comment.comment_id.in_(list_comment_id))
        .values(moderation_status=status)
    )
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount
