from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.init import get_async_db
from src.handlers.content_handler import (
    get_user_handler,
    fetch_latest_video_handler,
    get_user_videos_handler,
    get_video_detail_handler
)

router = APIRouter()

@router.get("/users")
async def get_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    return await get_user_handler(request, db)

@router.get("/fetch-latest-videos")
async def fetch_latest_videos(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    playlist_id: str = ""
):
    return await fetch_latest_video_handler(request, db, playlist_id)

@router.get("/user_videos")
async def get_user_videos(
    db: AsyncSession = Depends(get_async_db),
    playlist_id: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    return await get_user_videos_handler(db, playlist_id, page, page_size)

@router.get("/video/{video_id}")
async def get_video_detail(
    video_id: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    return await get_video_detail_handler(video_id, page, limit, db)
