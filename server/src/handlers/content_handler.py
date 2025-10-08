import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.video import VideoCreate, VideoFetchSummary
from src.services.content_service import (
    get_user_data,
    fetch_latest_video,
    fetch_comments,
    get_videos_handler,
    get_video_comments,
    delete_comments_by_ids,
    predict_comment
)
from src.database.crud_content import (
    get_video_by_id,
    insert_video,
    insert_comments,
    update_last_fetch_comment
)

logger = logging.getLogger(__name__)

async def get_user_handler(request: Request, db: AsyncSession):
    """
    handler to get user data using user_id data stored in request
    """
    try:
        # get user_id from request
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            # fallback when there is no user_id
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        
        # get user data
        return await get_user_data(db, user_id)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        logger.error("Failed to fetch user", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

async def fetch_latest_video_handler(request: Request, db: AsyncSession, playlist_id: str):
    """
    handler to get latest video based on playlist id, also get the comments and stored the video and comment data to postgresql
    """
    # get access token that already been set by middleware if user already login
    access_token = getattr(request.state, "access_token", None)
    if not access_token:
        # fallback when access_token data is not available -> means user not logged in
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    try:
        # get latest video
        videos = await fetch_latest_video(playlist_id, access_token)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        logger.error("Error fetching latest videos", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

    results = []
    for item in videos or []:
        # get needed data from videos data
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        video_id = content.get("videoId")
        if not video_id:
            continue

        try:
            # check if video is already available in database
            stored_video = await get_video_by_id(db, video_id)
            if not stored_video:
                # if not then create new one
                video_payload = VideoCreate(
                    video_id=video_id,
                    channel_id=snippet.get("channelId"),
                    playlist_id=playlist_id or snippet.get("playlistId", ""),
                    title=snippet.get("title", ""),
                    description=snippet.get("description"),
                    published_at=snippet.get("publishedAt"),
                )
                # perform insert video data
                stored_video = await insert_video(db, video_payload)

            # get related comment from video
            comments = await fetch_comments(video_id, access_token, stored_video.last_fetch_comment)
            # insert bulk comment
            await insert_comments(db, comments or [])
            # update last fetch comment in video table
            await update_last_fetch_comment(db, video_id)

            # return video and comment data for client
            results.append(VideoFetchSummary(
                video_id=video_id,
                title=stored_video.title,
                published_at=stored_video.published_at,
                new_comment_count=len(comments or [])
            ))
        except Exception as e:
            logger.error(f"Failed syncing comments for video {video_id}", exc_info=True)
            results.append(VideoFetchSummary(video_id=video_id, error=str(e)))

    return results

async def get_user_videos_handler(db: AsyncSession, playlist_id: str, page: int, page_size: int):
    """
    handler to get history video from postgre
    """
    if not playlist_id:
        # fallback when playlist_id is not provided
        return JSONResponse(status_code=400, content={"error": "playlist_id is required"})

    try:
        # get video history with pagination
        data = await get_videos_handler(db, playlist_id, page, page_size)
        return data
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        logger.error("Failed to get user videos", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

async def get_video_detail_handler(request: Request, video_id: str, page: int, limit: int, db: AsyncSession):
    """
    handler for detail video page where we get the detail video data like description, url, etc, and comment related to that video
    """
    # get access token data from request that have been set in middleware if user already login
    access_token = getattr(request.state, "access_token", None)
    if not access_token:
        # fallback when access token is not available means user is not logged in
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if not video_id:
        # fallback when video_id is not provided
        return JSONResponse(status_code=400, content={"error": "video_id is required"})

    try:
        # get comment data related to video with pagination
        data = await get_video_comments(db, video_id, access_token, page, limit)
        return data
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        logger.error("Failed to get video detail", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
    
async def delete_comments_handler(request: Request, db: AsyncSession):
    """
    handler to delete comment, one comment or bulk comment
    """
    try:
        # get data from request body
        body = await request.json()
        comment_ids = body.get("comment_ids")
        moderation_status = body.get("moderation_status", "rejected") # rejected | heldForReview
        ban_author = body.get("ban_author", False)

        # validation comment_ids
        if not comment_ids or not isinstance(comment_ids, list):
            return JSONResponse(status_code=400, content={"error": "Invalid comment_ids input"})

        # ban_author can be used when moderation_status is rejected
        if ban_author and moderation_status != "rejected":
            return JSONResponse(
                status_code=400,
                content={"error": "ban_author can only be used with moderation_status='rejected'"}
            )
        
        # get access token from request state that middleware setting
        access_token = getattr(request.state, "access_token", None)
        if not access_token:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        # perform delete comments
        result = await delete_comments_by_ids(db, access_token, comment_ids, moderation_status, ban_author)

        return JSONResponse(status_code=200, content={"success": True, "updated": result})
    except Exception as e:
        logger.error("Failed to delete comments", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

async def inference_model_handler(request: Request, db: AsyncSession):
    """
    handler for model prediction where comment data will be classified into promoting online gambling or not
    """
    try:
        # get video_id data from request body
        body = await request.json()
        video_id = body.get("video_id")

        # validation video_id
        if not video_id:
            return JSONResponse(status_code=400, content={"error": "video_id is required"})
        
        # perform inference model on comment data
        comment_data = await predict_comment(db, video_id)

        return comment_data
    except Exception as e:
        logger.error("Failed to predict comment", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})