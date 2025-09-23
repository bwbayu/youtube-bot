# src/services/auth_service.py
from src.core.session import create_session
from src.core.utils import encrypt_token
from src.database.crud import save_user, store_refresh_token
from src.schemas.user import UserCreate

from datetime import datetime, timedelta
from fastapi import HTTPException
import logging
import httpx
import jwt

logger = logging.getLogger(__name__)

async def get_channel_info(access_token: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url='https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails&mine=true',
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                logger.warning(f"Failed to get channel info: {response.text}")
                return None

            item = response.json().get("items", [])[0]
            return {
                "channel_id": item.get("id"),
                "playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
                "channel_name": item["snippet"]["title"],
                "custom_url": item["snippet"].get("customUrl"),
            }
    except Exception as e:
        logger.error(f"Error in get_channel_info: {e}", exc_info=True)
        return None

async def handle_auth_callback(session_data: dict, db):
    # Decode ID token
    tokens = session_data["tokens"]

    try:
        user_decode = jwt.decode(tokens['id_token'], options={"verify_signature": False})
        user_info = {
            "user_id": user_decode["sub"],
            "email": user_decode["email"],
            "name": user_decode["name"]
        }
    except Exception as e:
        logger.error(f"Failed to decode ID token: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid ID token")

    # Create Redis session
    try:
        session_id = create_session({
            "user_id": user_info['user_id'],
            "access_token": tokens['access_token']
        }, tokens['expires_in'])
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create session")

    # Get channel info
    try:
        channel_data = await get_channel_info(tokens["access_token"]) or {}
        user_data = UserCreate(**{**user_info, **channel_data})
    except Exception as e:
        logger.error(f"Failed to build user data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Invalid channel info")
    
    try:
        save_user(db, user_data)
    except Exception as e:
        logger.error(f"Failed to save user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save user")
    
    # Store refresh token
    try:
        refresh_token_data = {
            "session_id": session_id,
            "user_id": user_info["user_id"],
            "refresh_token_encrypted": encrypt_token(tokens['refresh_token']),
            "expires_at": datetime.now() + timedelta(seconds=tokens.get("refresh_token_expires_in", 604800))
        }
        store_refresh_token(db, refresh_token_data)
    except Exception as e:
        logger.error(f"Failed to store refresh token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store refresh token")


    return session_id, user_data
