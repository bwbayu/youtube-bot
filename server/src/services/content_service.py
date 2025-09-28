# src/services/content_services.py
from src.schemas.comment import CommentCreate, CommentResponse
from src.schemas.video import VideoResponse
from src.database.crud_content import *

from dateutil.parser import parse as parse_datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from dotenv import load_dotenv
import httpx, os, logging
from typing import List

load_dotenv()
logger = logging.getLogger(__name__)
API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
BASE_PLAYLIST_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
BASE_COMMENT_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

async def get_user_data(db: AsyncSession, user_id: str):
    user = await get_user_by_id(db, user_id)

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    return user

async def fetch_latest_video(playlist_id: str, access_token: str, max_result: int = 1):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BASE_PLAYLIST_URL, params={
                    "part": "snippet,contentDetails",
                    "playlistId": playlist_id,
                    "maxResults": max_result,
                    "key": API_KEY
                }, headers={"Authorization": f"Bearer {access_token}"})

            if response.status_code == 403:
                raise HTTPException(403, "YouTube quota exceeded while fetching video")
            if response.status_code == 404:
                raise HTTPException(404, "Playlist not found")
            
            items = response.json().get("items", [])
            if not items:
                return None
            
            return items
    except Exception as e:
        logger.error(f"Error in fetch_latest_video: {e}", exc_info=True)
        return None
    
async def fetch_comments(video_id: str, access_token: str, last_fetch: datetime | None, max_result: int = 100):
    comments = []
    prev_page_token = None
    params={
        "part": "snippet,replies",
        "videoId": video_id,
        "maxResults": max_result,
        "key": API_KEY
    }

    try:
        async with httpx.AsyncClient() as client:
            while True:
                res = await client.get(BASE_COMMENT_URL, 
                                       params=params, 
                                       headers={"Authorization": f"Bearer {access_token}"})
                
                if res.status_code == 403:
                    raise HTTPException(403, "YouTube quota exceeded while fetching comments")
                if res.status_code == 404:
                    raise HTTPException(404, "Video not found")
                
                data = res.json()
                for item in data.get("items", []):
                    comment = item["snippet"]["topLevelComment"]["snippet"]

                    # Filter by last_fetch (top-level comment)
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

                    # Add replies as flat comments
                    for reply in item.get("replies", {}).get("comments", []):
                        rs = reply["snippet"]
                        # Filter by last_fetch
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
    except Exception as e:
        logger.error(f"Error in fetch_comments: {e}", exc_info=True)
        return None
    
async def get_videos_handler(db: AsyncSession, playlist_id: str, page: int = 1, limit: int = 10) -> List[VideoResponse]:
    # get total video
    total_videos = await get_count_videos(db, playlist_id)

    # get videos data
    videos_data = await get_videos(db, playlist_id, page, limit)
    
    if not videos_data:
            raise HTTPException(status_code=404, detail="Videos not found")
    
    return {
        "items": videos_data,
        "total": total_videos,
        "page": page,
        "page_size": limit,
        "has_next": page * limit < total_videos
    }    
        
async def get_video_comments(db: AsyncSession, video_id: str, page: int = 1, limit: int = 10) -> dict:
    # get video detail
    video_detail = await get_video_by_id(db, video_id)
    # get comment count
    total_comment = await get_count_comments(db, video_id)

    # get comment data
    comments = await get_comments(db, video_id, page, limit)

    if not comments:
        raise HTTPException(status_code=404, detail="Comments not found")
    
    return {
        "videoDetail": video_detail,
        "items": comments,
        "total": total_comment,
        "page": page,
        "page_size": limit,
        "has_next": page * limit < total_comment
    }
