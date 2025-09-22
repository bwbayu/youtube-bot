# src/services/auth_service.py
import jwt
from datetime import datetime, timedelta
from src.core.session import create_session
from src.core.utils import hash_refresh_token
from src.database.crud import save_user, store_refresh_token
from src.schemas.user import UserCreate
import httpx

async def get_channel_info(access_token: str):
    # TODO: add try catch
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url='https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails&mine=true',
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            return None

        item = response.json().get("items", [])[0]
        return {
            "channel_id": item.get("id"),
            "playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
            "channel_name": item["snippet"]["title"],
            "custom_url": item["snippet"].get("customUrl"),
        }

async def handle_auth_callback(session_data: dict, db):
    # Decode ID token
    tokens = session_data["tokens"]
    user_decode = jwt.decode(tokens['id_token'], options={"verify_signature": False})
    user_info = {
        "user_id": user_decode["sub"],
        "email": user_decode["email"],
        "name": user_decode["name"]
    }

    # Create Redis session
    # TODO: add try catch
    session_id = create_session({
        "user_id": user_info['user_id'],
        "access_token": tokens['access_token']
    }, tokens['expires_in'])

    # Get channel info
    # TODO: add try catch
    channel_data = await get_channel_info(tokens["access_token"])
    user_data = UserCreate(**{**user_info, **channel_data})
    # TODO: add try catch
    save_user(db, user_data)
    
    # Store refresh token
    refresh_token_data = {
        "session_id": session_id,
        "user_id": user_info["user_id"],
        "refresh_token_hash": hash_refresh_token(tokens['refresh_token']),
        "expires_at": datetime.now() + timedelta(seconds=tokens.get("refresh_token_expires_in", 604800))
    }
    # TODO: add try catch
    store_refresh_token(db, refresh_token_data)


    return session_id, user_data
