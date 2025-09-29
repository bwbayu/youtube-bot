from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from src.database.crud_content import (
    get_user_by_id, get_video_by_id,
    get_count_videos, get_videos,
    get_comments, get_count_comments
)
from src.schemas.comment import CommentCreate
from dateutil.parser import parse as parse_datetime
from typing import List
from datetime import datetime
import httpx, os, logging

logger = logging.getLogger(__name__)
API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_PLAYLIST_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
BASE_COMMENT_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

async def get_user_data(db: AsyncSession, user_id: str):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def fetch_latest_video(playlist_id: str, access_token: str, max_result: int = 1):
    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_PLAYLIST_URL, params={
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": max_result,
            "key": API_KEY
        }, headers={"Authorization": f"Bearer {access_token}"})

    if res.status_code == 403:
        raise HTTPException(403, "YouTube quota exceeded")
    if res.status_code == 404:
        raise HTTPException(404, "Playlist not found")

    return res.json().get("items", [])

async def fetch_comments(video_id: str, access_token: str, last_fetch: datetime | None, max_result: int = 100):
    comments = []
    params = {
        "part": "snippet,replies",
        "videoId": video_id,
        "maxResults": max_result,
        "key": API_KEY
    }

    prev_page_token = None

    async with httpx.AsyncClient() as client:
        while True:
            res = await client.get(BASE_COMMENT_URL, params=params, headers={"Authorization": f"Bearer {access_token}"})
            if res.status_code == 403:
                raise HTTPException(403, "YouTube quota exceeded")
            if res.status_code == 404:
                raise HTTPException(404, "Video not found")

            data = res.json()
            for item in data.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                published = parse_datetime(comment["publishedAt"])
                updated = parse_datetime(comment["updatedAt"])
                if last_fetch and max(published, updated) <= last_fetch:
                    continue

                comments.append(CommentCreate(
                    comment_id=item["id"],
                    video_id=video_id,
                    author_display_name=comment["authorDisplayName"],
                    text=comment["textDisplay"],
                    published_at=comment["publishedAt"],
                    updated_at=comment["updatedAt"]
                ))

                for reply in item.get("replies", {}).get("comments", []):
                    rs = reply["snippet"]
                    published_r = parse_datetime(rs["publishedAt"])
                    updated_r = parse_datetime(rs["updatedAt"])
                    if last_fetch and max(published_r, updated_r) <= last_fetch:
                        continue

                    comments.append(CommentCreate(
                        comment_id=reply["id"],
                        video_id=video_id,
                        author_display_name=rs["authorDisplayName"],
                        text=rs["textDisplay"],
                        published_at=rs["publishedAt"],
                        updated_at=rs["updatedAt"]
                    ))

            next_token = data.get("nextPageToken")
            if not next_token or next_token == prev_page_token:
                break

            prev_page_token = next_token
            params["pageToken"] = next_token

    return comments

async def get_videos_handler(db: AsyncSession, playlist_id: str, page: int, limit: int):
    total = await get_count_videos(db, playlist_id)
    videos = await get_videos(db, playlist_id, page, limit)
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    return {
        "items": videos,
        "total": total,
        "page": page,
        "page_size": limit,
        "has_next": page * limit < total
    }

async def get_video_comments(db: AsyncSession, video_id: str, page: int, limit: int):
    video = await get_video_by_id(db, video_id)
    comments = await get_comments(db, video_id, page, limit)
    total = await get_count_comments(db, video_id)

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not comments:
        raise HTTPException(status_code=404, detail="No comments found")

    return {
        "videoDetail": video,
        "items": comments,
        "total": total,
        "page": page,
        "page_size": limit,
        "has_next": page * limit < total
    }
