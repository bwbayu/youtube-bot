# src/middleware/require_login.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from datetime import datetime
from fastapi import Request
import httpx
import os
import logging

from src.database.crud import update_session_id, get_refresh_token_by_session
from src.core.session import get_session, create_session
from src.core.utils import decrypt_token
from src.database.init import get_db

load_dotenv()
logger = logging.getLogger(__name__)

class RequireLoginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            session_id = request.cookies.get("session_id")

            # session in cookie is not available or already expired
            if not session_id:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            
            # session data still available
            try:
                session_data = get_session(session_id)
            except Exception as e:
                logger.error(f"Redis session error: {e}", exc_info=True)
                return JSONResponse({"error": "Session check failed"}, status_code=500)
            
            if session_data:
                # forward the request with data user_id in the request
                request.state.user_id = session_data['user_id']
                return await call_next(request)
            
            # Session not found, try to use refresh token from DB
            try:
                db = next(get_db())
                token_data = get_refresh_token_by_session(db, session_id)
            except Exception as e:
                logger.error(f"DB access error: {e}", exc_info=True)
                return JSONResponse({"error": "Internal error"}, status_code=500)

            if not token_data or token_data.expires_at < datetime.now():
                return JSONResponse({"error": "Session expired"}, status_code=401)
            
            # request new access token using refresh token
            try:
                decrypted_token = decrypt_token(token_data.refresh_token_encrypted)
                new_access_token = await self.refresh_access_token(decrypted_token)
            except Exception as e:
                logger.error(f"Refresh token failed: {e}", exc_info=True)
                return JSONResponse({"error": "Unable to refresh session"}, status_code=401)

            # create new session using new access token
            try:
                new_session_id = create_session({
                    "user_id": token_data.user_id,
                    "access_token": new_access_token
                }, 3600)

                update_session_id(db, token_data.user_id, session_id, new_session_id)
            except Exception as e:
                logger.error(f"Failed to update session: {e}", exc_info=True)
                return JSONResponse({"error": "Session update failed"}, status_code=500)

            # update session id on refresh token data
            update_session_id(db, token_data.user_id, session_id, new_session_id)

            # forward the request with data user_id in the request
            request.state.user_id = token_data.user_id
            response = await call_next(request)
            # set new cookie
            # TODO_PROD: change secure to True when deploying
            response.set_cookie("session_id", new_session_id, httponly=True, secure=False)
            return response
        except Exception as e:
            logger.error(f"Unhandled middleware error: {e}", exc_info=True)
            return JSONResponse({"error": "Unhandled error"}, status_code=500)

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