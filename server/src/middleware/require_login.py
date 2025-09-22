# src/middleware/require_login.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from dotenv import load_dotenv
import httpx
import os

from src.core.session import get_session, create_session
from src.database.crud import update_session_id, get_refresh_token_by_session
from src.database.init import get_db

load_dotenv()

class RequireLoginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        db = get_db()

        # session in cookie is not available or already expired
        if not session_id:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        # session data still available
        session_data = get_session(session_id)
        if session_data:
            request.state.user_id = session_data['user_id']
            # QUESTION: why this is just return call_next but in the end return response
            return await call_next(request)
        
        # session expired or refresh token data not exist
        token_data = get_refresh_token_by_session(db, session_id)
        if not token_data or token_data.expires_at < datetime.now():
            return JSONResponse({"error": "Session expired"}, status_code=401)
        
        # request new access token using refresh token
        try:
            new_access_token = await self.refresh_access_token("?")
        except:
            return JSONResponse({"error": "Unable to refresh session"}, status_code=401)

        # create new session using new access token
        new_session_id = create_session({
            "user_id": token_data.user_id,
            "access_token": new_access_token
        }, 3600)

        # update session id on refresh token data
        update_session_id(db, token_data.user_id, session_id, new_session_id)

        # set new cookie
        request.state.user_id = token_data.user_id
        response = await call_next(request)
        # QUESTION: what is httponly and secure parameter used for
        response.set_cookie("session_id", new_session_id, httponly=True, secure=True)
        return response

    async def refresh_access_token(self, refresh_token: str):
        """
        request new access token using refresh token
        """
        async with httpx.AsyncClient as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            })

        if response.status_code != 200:
            raise Exception(response.json())
        return response.json()["access_token"]