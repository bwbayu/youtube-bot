# src/services/auth_service.py
from src.database.crud import save_user, store_refresh_token, delete_refresh_token_by_session, get_refresh_token_by_session, update_session_id
from src.core.session import create_session, delete_session
from src.core.utils import encrypt_token, decrypt_token
from src.schemas.user import UserCreate

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Response
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import httpx
import jwt
import os

load_dotenv()
logger = logging.getLogger(__name__)
COOKIE_TTL = 3600 * 24 * 7

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

            items = response.json().get("items", [])
            if not items:
                return None

            item = items[0]
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
        session_id = await create_session({
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
        await save_user(db, user_data)
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

        await store_refresh_token(db, refresh_token_data)
    except Exception as e:
        logger.error(f"Failed to store refresh token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store refresh token")


    return session_id, user_data

async def delete_session_data(db: AsyncSession, session_id: str, response: Response):
    try:
        # delete session in redis
        await delete_session(session_id)

        # delete cookie data
        response.delete_cookie("session_id")

        # delete refresh token data
        token_data = await get_refresh_token_by_session(db, session_id)
        if token_data:
            decrypted_token = decrypt_token(token_data.refresh_token_encrypted)
            await delete_refresh_token_by_session(db, session_id)

            # request revoke refresh token
            success = await revoke_token(decrypted_token)
            if success:
                return True, "Logged out successfully"
            else:
                message = "Revocation failed, but session and refresh token were deleted."
                logger.warning(message)
                return False, message
        else:
            # handle refresn token data doesn't exist
            message = "No refresh token found for session, but session deleted."
            logger.warning(message)
            return True, message

    except Exception as e:
        logger.error(f"Failed during logout: {e}", exc_info=True)
        return False, f"Logout failed due to internal error: {str(e)}"
            
async def revoke_token(decrypted_token: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            revoke_res = await client.post(
                f"https://oauth2.googleapis.com/revoke?token={decrypted_token}",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        if revoke_res.status_code == 200:
            logger.info("Token revoked successfully.")
            return True
        else:
            logger.warning(f"Failed to revoke token: {revoke_res.status_code} - {revoke_res.text}")
            return False

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during token revoke: {e}", exc_info=True)
        return False

    except Exception as e:
        logger.error(f"Unexpected error during token revoke: {e}", exc_info=True)
        return False

async def renew_access_token(decrypted_refresh_token: str):
    try:
        async with httpx.AsyncClient() as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": decrypted_refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        if token_res.status_code != 200:
            logger.warning(f"Failed to refresh access token: {token_res.text}")
            return None

        return token_res.json().get("access_token")

    except httpx.HTTPError as e:
        logger.error(f"HTTP error while refreshing token: {e}", exc_info=True)
        return None

    except Exception as e:
        logger.error(f"Unexpected error while refreshing token: {e}", exc_info=True)
        return None

async def handle_refresh_access_token(db: AsyncSession, session_id: str):
    # TODO_LATER: CHECK FUNCTIONALITY
    # session data not exist
    if not session_id:
        return JSONResponse({"error": "No session cookie"}, status_code=401)
    
    # get refresh token data
    token_data = await get_refresh_token_by_session(db, session_id)

    if not token_data or token_data.expires_at < datetime.now():
        # handle refresn token data doesn't exist
        return JSONResponse({"error": "Refresh token expired"}, status_code=401)
    
    try:
        decrypted_refresh_token = decrypt_token(token_data.refresh_token_encrypted)
        # request new access token using refresh token
        new_access_token = await renew_access_token(decrypted_refresh_token)

        if not new_access_token:
            return JSONResponse({"error": "Failed to refresh token"}, status_code=401)
        
        # create new session using new access token
        new_session_id = await create_session({
            "user_id": token_data.user_id,
            "access_token": new_access_token,
        }, 3600)

        # update session id in refresh token data
        success = await update_session_id(db, token_data.user_id, session_id, new_session_id)
        
        if not success:
            # refresh token data doesn't exist
            logger.error("Failed to update session_id in refresh token store")
            return JSONResponse({"error": "Failed to update session"}, status_code=500)
        # create response
        response = JSONResponse({
            "message": "Session refreshed"
        })
        response.set_cookie(
            key="session_id",
            value=new_session_id,
            httponly=True,
            secure=False,  # TODO_PROD: True in production
            max_age=COOKIE_TTL,
            expires=COOKIE_TTL
        )
        return response
    except Exception as e:
        logger.error(f"Refresh failed: {e}", exc_info=True)
        return JSONResponse({"error": "Internal error"}, status_code=500)