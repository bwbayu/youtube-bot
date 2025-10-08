from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.init import get_async_db
from src.handlers.content_handler import (
    get_user_handler,
    fetch_latest_video_handler,
    get_user_videos_handler,
    get_video_detail_handler,
    delete_comments_handler,
    inference_model_handler
)

router = APIRouter()

@router.get("/users")
async def get_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    # route to get users data
    return await get_user_handler(request, db)

@router.get("/fetch-latest-videos")
async def fetch_latest_videos(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    playlist_id: str = ""
):
    # route to get latest video from channel data
    return await fetch_latest_video_handler(request, db, playlist_id)

@router.get("/user_videos")
async def get_user_videos(
    db: AsyncSession = Depends(get_async_db),
    playlist_id: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    # route to get history video from database
    return await get_user_videos_handler(db, playlist_id, page, page_size)

@router.get("/video/{video_id}")
async def get_video_detail(
    request: Request,
    video_id: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    # route to get detail video data and all of the comments
    return await get_video_detail_handler(request, video_id, page, limit, db)

@router.post("/comments/delete")
async def delete_comments(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    # route to perform comment deletion by updating moderation status to google and database
    return await delete_comments_handler(request, db)

@router.post("/predict")
async def inference_model(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    # route for model inference to comments data
    return await inference_model_handler(request, db)
