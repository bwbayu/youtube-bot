# src/middleware/require_login.py
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from fastapi import Request
import httpx, os, logging
from dotenv import load_dotenv

from src.database.init import get_async_db
from src.database.crud import (
    update_session_id, get_refresh_token_by_session
)
from src.core.session import get_session, create_session
from src.core.utils import decrypt_token

load_dotenv()
logger = logging.getLogger(__name__)


PUBLIC_PATHS = ["/health",
                "/auth/login", "/auth/callback", 
                ]
COOKIE_TTL = 3600 * 24 * 1

class RequireLoginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # get session id from cookie
        session_id = request.cookies.get("session_id")
        session_data = None

        if request.url.path in PUBLIC_PATHS and not session_id:
            return await call_next(request)
                
        if session_id:
            # get session data from redis
            try:
                session_data = await get_session(session_id)
            except Exception as e:
                logger.error(f"Redis session error: {e}", exc_info=True)
            
            if session_data:
                # forward the request with data user_id in the request
                request.state.user_id = session_data['user_id']
                request.state.access_token = session_data['access_token']
                return await call_next(request)

            # Session data not found, try to use refresh token from DB
            try:
                async for db in get_async_db():
                    token_data = await get_refresh_token_by_session(db, session_id)
                    
                    if not token_data or token_data.expires_at < datetime.now():
                        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
                    
                    # request new access token using refresh token
                    decrypted_token = decrypt_token(token_data.refresh_token_encrypted)
                    new_access_token = await self.refresh_access_token(decrypted_token)

                    # create new session using new access token
                    new_session_id = await create_session({
                        "user_id": token_data.user_id,
                        "access_token": new_access_token
                    }, 3600)

                    success = await update_session_id(db, token_data.user_id, session_id, new_session_id)

                    if not success:
                        # refresh token data doesn't exist
                        logger.error("Failed to update session_id in refresh token store")
                        return JSONResponse({"error": "Failed to update session"}, status_code=500)

                    # set new cookie
                    # TODO_PROD: change secure to True when deploying
                    response = RedirectResponse("http://localhost:5173/dashboard")
                    response.set_cookie(
                        "session_id", 
                        new_session_id, 
                        httponly=True, 
                        secure=False, 
                        max_age=COOKIE_TTL, 
                        expires=COOKIE_TTL
                        )
                    return response
            except Exception as e:
                logger.error(f"Unhandled middleware error: {e}", exc_info=True)
                return JSONResponse({"error": "Unhandled error"}, status_code=500)
        else:
            # there is no cookie and can't use refresh token to create new session
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    async def refresh_access_token(self, refresh_token: str):
        """
        request new access token using refresh token
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("https://oauth2.googleapis.com/token", data={
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                })

            if response.status_code != 200:
                raise Exception(response.json())

            return response.json()["access_token"]
        except Exception as e:
            logger.error(f"Error during access token refresh: {e}", exc_info=True)
            raise