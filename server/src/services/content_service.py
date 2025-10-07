from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from src.database.crud_content import (
    get_user_by_id, get_video_by_id,
    get_count_videos, get_videos,
    get_comments, get_count_comments,
    update_moderation_status_comment,
    get_all_comments,
    update_comments_prediction_batch,
    insert_comments,
    update_last_fetch_comment
)
from src.schemas.comment import CommentCreate
from dateutil.parser import parse as parse_datetime
from typing import List
from datetime import datetime
import httpx, os, logging

from transformers import BertTokenizer, AutoModelForSequenceClassification
from src.utils.preprocessing import normalize_text
from torch.utils.data import DataLoader
import torch.nn.functional as F
from datasets import Dataset
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "..", "models", "best_indobert.pt")

model_name = "indobenchmark/indobert-lite-base-p2"
device = "cuda" if torch.cuda.is_available() else "cpu"
try:
    model_indobert = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    model_indobert.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    tokenizer_indobert = BertTokenizer.from_pretrained(model_name)
except Exception as e:
    print(f"Error loading model or tokenizer: {e}")
    raise e

logger = logging.getLogger(__name__)
API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_PLAYLIST_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
BASE_COMMENT_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
YOUTUBE_MODERATION_URL = "https://www.googleapis.com/youtube/v3/comments/setModerationStatus"

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

async def get_video_comments(db: AsyncSession, video_id: str, access_token: str, page: int, limit: int):
    video = await get_video_by_id(db, video_id)
    # fetch from youtube
    new_comments = await fetch_comments(video_id, access_token, video.last_fetch_comment)
    await insert_comments(db, new_comments or [])
    await update_last_fetch_comment(db, video_id)
    # fetch from database
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

def _chunkify(data: List[str], size: int) -> List[List[str]]:
    return [data[i:i + size] for i in range(0, len(data), size)]

async def update_moderation_status_batch(
        client: httpx.AsyncClient, 
        access_token: str,
        ids: List[str], 
        moderation_status: str = "heldForReview",
        ban_author: bool = False
        ) -> bool:
        try:
            params = {
                "id": ",".join(ids),
                "moderationStatus": moderation_status,
            }
            if moderation_status == "rejected":
                params["banAuthor"] = "true" if ban_author else "false"

            response: httpx.Response = await client.post(
                YOUTUBE_MODERATION_URL,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code == 204:
                logger.info(f"✅ Moderated {len(ids)} comments.")
                return True
            else:
                logger.warning(f"⚠️ Failed batch of {len(ids)} - {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Exception during batch: {e}", exc_info=True)
            return False

async def delete_comments_by_ids(
    db: AsyncSession,
    access_token: str,
    comment_ids: list[str],
    moderation_status: str = "heldForReview", # rejected
    ban_author: bool = False
) -> int:
    if not comment_ids:
        raise HTTPException(status_code=400, detail="Empty comment_ids list")

    success_ids: List[str] = []
    # Update on YouTube
    async with httpx.AsyncClient() as client:
        for chunk in _chunkify(comment_ids, 100):  # Try 100 first
            if await update_moderation_status_batch(client, access_token, chunk, moderation_status, ban_author):
                success_ids.extend(chunk)
            else:
                for chunk50 in _chunkify(chunk, 50):  # Try 50 fallback
                    if await update_moderation_status_batch(client, access_token, chunk50, moderation_status, ban_author):
                        success_ids.extend(chunk50)
                    else:
                        for chunk25 in _chunkify(chunk50, 25):  # Final fallback
                            if await update_moderation_status_batch(client, access_token, chunk25, moderation_status, ban_author):
                                success_ids.extend(chunk25)
                            else:
                                logger.error(f"❌ Final fallback failed for: {chunk25}")
    
    if not success_ids:
        raise HTTPException(status_code=500, detail="All moderation attempts failed.")
    
    # Update on DB
    row_count = await update_moderation_status_comment(db, success_ids, moderation_status)

    return row_count

async def predict_comment(
    db: AsyncSession,
    video_id: str
) -> list[str]:
    if not video_id:
        raise HTTPException(status_code=400, detail="Video_id is required")
    
    # fetch all comment
    comments = await get_all_comments(db, video_id)
    if not comments:
        return []
    
    # text processing
    texts = [normalize_text(c.text) for c in comments]
    comment_ids = [c.comment_id for c in comments]
    comments_dataset = Dataset.from_dict({"text": texts})
    
    # model inference
    model_indobert.to(device)
    model_indobert.eval()
    dataloader = DataLoader(comments_dataset, batch_size=64)
    results: list[dict] = []

    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            batch_inputs = tokenizer_indobert(batch['text'], return_tensors='pt', truncation=True, padding=True, max_length=512)
            batch_inputs = {k: v.to(device) for k, v in batch_inputs.items()}
            
            outputs = model_indobert(**batch_inputs)
            probs = F.softmax(outputs.logits, dim=1)
            preds = torch.argmax(probs, dim=1).tolist()
            confs = torch.max(probs, dim=1).values.tolist()

            start_idx = i * dataloader.batch_size
            end_idx = start_idx + len(preds)
            for idx, pred, conf in zip(comment_ids[start_idx:end_idx], preds, confs):
                results.append({
                    "comment_id": idx,
                    "is_judi": bool(pred),
                    "confidence": conf
                })
    
    # update data after prediction
    await update_comments_prediction_batch(db, results)
    # return only predicted as judi
    return {"predictions": [r for r in results if r["is_judi"]]}