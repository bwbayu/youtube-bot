# src/services/content_services.py
from src.database.crud_content import *
from src.schemas.comment import CommentCreate

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import httpx, os, logging
from dotenv import load_dotenv

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
    params={
        "part": "snippet,replies",
        "videoId": video_id,
        "maxResults": max_result,
        "key": API_KEY
    }

    try:
        async with httpx.AsyncClient as client:
            while True:
                res = await client.get(BASE_COMMENT_URL, 
                                       params, 
                                       headers={"Authorization": f"Bearer {access_token}"})

                if res.status_code == 403:
                    raise HTTPException(403, "YouTube quota exceeded while fetching comments")
                if res.status_code == 404:
                    raise HTTPException(404, "Video not found")
                
                data = res.json()
                for item in data.get("items", []):
                    comment = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append(CommentCreate(
                        comment_id=item["id"],
                        video_id=video_id,
                        author_display_name=comment["authorDisplayName"],
                        text=comment["textDisplay"],
                        published_at=comment["publishedAt"],
                        updated_at=comment["updatedAt"],
                        moderation_status=comment["moderationStatus"]
                    ))

                    # Add replies as flat comments
                    for reply in item.get("replies", {}).get("comments", []):
                        rs = reply["snippet"]
                        comments.append(CommentCreate(
                            comment_id=reply["id"],
                            video_id=video_id,
                            author_display_name=rs["authorDisplayName"],
                            text=rs["textDisplay"],
                            published_at=rs["publishedAt"],
                            updated_at=rs["updatedAt"],
                            moderation_status=rs["moderationStatus"]
                        ))

                    if "nextPageToken" in data:
                        params["pageToken"] = data["nextPageToken"]
                    else:
                        break

        return comments
    except Exception as e:
        logger.error(f"Error in fetch_comments: {e}", exc_info=True)
        return None