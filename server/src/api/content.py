# src/api/content.py
from src.database.crud_content import (
    get_video_by_id,
    insert_video,
    insert_comments,
    update_last_fetch_comment,
)
from src.services.content_service import (
    fetch_latest_video, 
    fetch_comments, 
    get_user_data, 
    get_videos_handler, 
    get_video_comments
)
from src.schemas.video import VideoCreate, VideoFetchSummary, VideoListResponse
from src.database.init import get_async_db
from src.schemas.user import UserResponse
from src.schemas.comment import CommentListResponse

from fastapi import APIRouter, Request, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# QUESTION: what is the difference between using response_model and not
# ANSWER: validate response data, serialize sqlalchemy model to dict, consistency
@router.get("/users", response_model=UserResponse)
async def get_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    user_id = getattr(request.state, "user_id")
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # get user data by user id
    user = await get_user_data(db, user_id)

    if isinstance(user, JSONResponse):
        # if user not found
        return user

    # construct user data
    user_data = {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "channel_id": user.channel_id,
        "custom_url": user.custom_url,
        "playlist_id": user.playlist_id,
    }

    return user_data


@router.get("/fetch-latest-videos", response_model=list[VideoFetchSummary])
async def get_latest_video(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    playlist_id: str = "",
):
    access_token = getattr(request.state, "access_token", None)
    if not access_token:
        logger.warning("Missing access token on request state")
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    videos = await fetch_latest_video(playlist_id, access_token)

    results: list[VideoFetchSummary] = []
    for item in videos:
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        video_id = content.get("videoId")

        if not video_id:
            logger.warning("Skipping playlist item without videoId")
            continue

        stored_video = await get_video_by_id(db, video_id)
        if not stored_video:
            video_payload = VideoCreate(
                video_id=video_id,
                channel_id=snippet.get("channelId"),
                playlist_id=playlist_id or snippet.get("playlistId", ""),
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                published_at=snippet.get("publishedAt"),
            )
            stored_video = await insert_video(db, video_payload)

        try:
            comments = await fetch_comments(
                video_id,
                access_token,
                stored_video.last_fetch_comment if stored_video else None,
            )
            await insert_comments(db, comments)
            await update_last_fetch_comment(db, video_id)
            results.append(
                VideoFetchSummary(
                    video_id=video_id, 
                    title=stored_video.title,
                    published_at=stored_video.published_at,
                    new_comment_count=len(comments or [])
                    )
            )
        except Exception as e:
            logger.exception("Failed to sync comments for video %s", video_id)
            results.append(VideoFetchSummary(video_id=video_id, error=str(e)))

    return results

@router.get("/user_videos", response_model=VideoListResponse)
async def get_user_videos(
    db: AsyncSession = Depends(get_async_db),
    playlist_id: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    if not playlist_id:
        raise HTTPException(status_code=400, detail="playlist_id is required")
    
    return await get_videos_handler(db, playlist_id, page, page_size)


@router.get("/video/{video_id}", response_model=CommentListResponse)
async def get_video_detail(
    video_id: str = Path(..., description="Video ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of comments per page"),
    db: AsyncSession = Depends(get_async_db)
):
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    # get comment data
    return await get_video_comments(db, video_id, page, limit)