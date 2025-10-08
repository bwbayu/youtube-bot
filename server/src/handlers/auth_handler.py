# src/handlers/auth_handler.py
from httpx import AsyncClient
import urllib.parse
import os
import logging
from fastapi import Request, Response, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.session import get_session, create_session, delete_session
from src.services.auth_service import (
    handle_auth_callback,
    delete_session_data,
    handle_refresh_access_token
)

logger = logging.getLogger(__name__)
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
SCOPE = "openid email profile https://www.googleapis.com/auth/youtube.force-ssl"
COOKIE_TTL = 3600 * 24 * 1

async def login_handler(request: Request):
    """
    handler for login with google auth to get auth token
    if user already login will use session that already stored
    if not, then it will redirect to google login
    """
    session_id = request.cookies.get("session_id")
    session_data = await get_session(session_id) if session_id else None
    if session_data:
        return RedirectResponse("http://localhost:5173/dashboard")
    
    state = await create_session({"status": True}, 300)
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPE)}"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(auth_url)

async def callback_handler(request: Request, db: AsyncSession):
    """
    handler after user login and get auth token, where auth token will be used to get access and refresh token also token id
    token id is encrypted jwt token contain user info, after that, access token will be used to create session, and session
    will be stored in redis, while refresh token will be stored in postgresql, then session_id will be stored in cookie as a flag
    that this user still login
    """
    try:
        # get auth token
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            return JSONResponse(status_code=400, content={"error": "Missing code or state"})

        # check state auth
        session = await get_session(state)
        if not session or not session.get("status"):
            return JSONResponse(status_code=400, content={"error": "Invalid state"})
        
        await delete_session(state)

        # request to google to get refresh, access token and token id
        async with AsyncClient() as client:
            token_res = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            })
        if token_res.status_code != 200:
            # fallback when response status code is not 200
            return JSONResponse(status_code=400, content={"error": "Failed to exchange token"})

        tokens = token_res.json() # get data
        if "access_token" not in tokens:
            # fallback when access_token is not in response data
            return JSONResponse(status_code=400, content={"error": "Missing access_token in token response"})

        # stored access and refresh token to database and fetch channel data
        session_id, _ = await handle_auth_callback({"tokens": tokens}, db)

        # define endpoint for redirect after login
        response = RedirectResponse("http://localhost:5173/dashboard")

        # set cookie with session_id
        response.set_cookie(
            "session_id", session_id,
            httponly=True, secure=False,
            max_age=COOKIE_TTL, expires=COOKIE_TTL
        )
        return response

    except HTTPException as e:
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error("Unexpected error in callback handler", exc_info=True)
        return JSONResponse({"error": "Internal server error"}, status_code=500)

async def logout_handler(request: Request, response: Response, db: AsyncSession):
    """
    handler when user logout, session data in redis that contain access token and refresh token in postgresql will be deleted
    """
    # get session
    session_id = request.cookies.get("session_id")
    if session_id:
        # if session still available, perform delete on session data (access token) and refresh token data
        is_success, message = await delete_session_data(db, session_id, response)
        status_code = 200 if is_success else 400
        return JSONResponse(
            content={"logout_status": is_success, "message": message},
            status_code=status_code
        )
    
    # fallback when session is not found in cookie
    return JSONResponse(
        content={"logout_status": False, "message": "No session_id found in cookie."},
        status_code=400
    )

async def refresh_handler(request: Request, db: AsyncSession):
    """
    handler when session data is already expired and automatically get new one with refresh token if refresh token haven't expired
    """
    # get session data
    session_id = request.cookies.get("session_id")
    if not session_id:
        return JSONResponse({"error": "No session cookie"}, status_code=401)
    
    try:
        # get new access token using refresh token and create new session data
        new_session_id = await handle_refresh_access_token(db, session_id)

        response = JSONResponse({"message": "Session refreshed"})
        # set cookie again with new session_id
        response.set_cookie(
            key="session_id",
            value=new_session_id,
            httponly=True,
            secure=False,
            max_age=COOKIE_TTL,
            expires=COOKIE_TTL
        )
        return response
    except HTTPException as e:
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error("Unexpected error in refresh handler", exc_info=True)
        return JSONResponse({"error": "Internal server error"}, status_code=500)
