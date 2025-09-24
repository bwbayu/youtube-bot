# src/services/auth_service.py
from src.database.crud import save_user, store_refresh_token, delete_refresh_token_by_session, get_refresh_token_by_session, update_session_id
from src.core.session import create_session, delete_session
from src.core.utils import encrypt_token, decrypt_token
from src.schemas.user import UserCreate

from fastapi import HTTPException, Response
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
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
        print("create session auth service")
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

async def delete_session_data(db: Session, session_id: str, response: Response):
    try:
        # delete session in redis
        delete_session(session_id)

        # delete cookie data
        response.delete_cookie("session_id")

        # delete refresh token data
        token_data = get_refresh_token_by_session(db, session_id)
        if token_data:
            decrypted_token = decrypt_token(token_data.refresh_token_encrypted)
            delete_refresh_token_by_session(db, session_id)

            # request revoke refresh token
            success = await revoke_token(decrypted_token)
            if success:
                return True, "Logged out successfully"
            else:
                message = "Revocation failed, but session and refresh token were deleted."
                logger.warning(message)
                return False, message
        else:
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
    # TODO: add try catch
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

        return token_res

async def handle_refresh_access_token(db: Session, session_id: str):
    # session data not exist
    if not session_id:
        return {"error": "No session cookie"}, 401
    
    # get refresh token data
    token_data = get_refresh_token_by_session(db, session_id)

    if not token_data or token_data.expires_at < datetime.now():
        return {"error": "Refresh token expired"}, 401
    
    try:
        decrypted_refresh_token = decrypt_token(token_data.refresh_token_encrypted)
        # request new access token using refresh token
        renew_acc_token_res = renew_access_token(decrypted_refresh_token)

        if renew_acc_token_res.status_code != 200:
            return {"error": "Failed to refresh token"}, 401
        
        new_access_token = renew_acc_token_res.json()["access_token"]
        
        # create new session using new access token
        new_session_id = create_session({
            "user_id": token_data.user_id,
            "access_token": new_access_token,
        }, 3600)

        # update session id in refresh token data
        update_session_id(db, token_data.user_id, session_id, new_session_id)

        # create response
        response = Response(
            content={
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
        return {"error": "Internal error"}, 500