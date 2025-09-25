# src/api/auth.py
from src.services.auth_service import handle_auth_callback, delete_session_data, handle_refresh_access_token
from src.core.session import create_session, get_session, delete_session
from src.database.init import get_async_db

from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx, urllib.parse, os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
SCOPE = "openid email profile https://www.googleapis.com/auth/youtube.readonly"
COOKIE_TTL = 3600 * 24 * 7

@router.get("/login", name='login')
async def login(request: Request):
    # check session
    session_id = request.cookies.get("session_id")
    session_data = await get_session(session_id) if session_id else None
    print("check session data: ", session_data)
    if session_data:
        # redirect to dashboard if still have session
        print("redirect to dashboard (login)")
        return RedirectResponse("http://localhost:5173/dashboard")
    
    print("create auth code")
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

@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_async_db)):
    try:
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state")

        session = await get_session(state)
        if not session or not session.get("status"):
            raise HTTPException(status_code=400, detail="Invalid state")
        
        await delete_session(state)
        print("delete auth code")
        print("exchange auth code to token")
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_res = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            })

        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange token")
        
        tokens = token_res.json()
        if "access_token" not in tokens:
            raise HTTPException(status_code=400, detail="access_token missing from response")

        # Continue to service
        session_id, _ = await handle_auth_callback({"tokens": tokens}, db)

        # TODO_PROD: change secure to True when deploying
        response = RedirectResponse("http://localhost:5173/dashboard")
        response.set_cookie(
            "session_id", 
            session_id, 
            httponly=True, 
            secure=False, 
            max_age=COOKIE_TTL, 
            expires=COOKIE_TTL
            )
        return response
    
    except HTTPException as http_exc:
        logger.warning(f"OAuth callback failed: {http_exc.detail}")
        return JSONResponse(status_code=http_exc.status_code, content={"error": http_exc.detail})
    
    except Exception as e:
        logger.error(f"Unexpected error in /callback: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
    
@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_async_db)):
    """
    delete cookie, redis session, and refresh token in postgresql. also request revoke token access to google
    """
    session_id = request.cookies.get("session_id")

    response = JSONResponse(content={"logout_status": True, "message": "Logged out successfully"})
    
    if session_id:
        is_success, message = await delete_session_data(db, session_id, response)
        response.status_code = 200 if is_success else 400
        response.content = {
            "logout_status": is_success,
            "message": message
        }
    else:
        response.status_code = 400
        response.content = {
            "logout_status": False,
            "message": "No session_id found in cookie."
        }

    return response

@router.post("/refresh")
async def refresh_access_token(request: Request, db: AsyncSession = Depends(get_async_db)):
    """
    request new access token using refresh token in the middle of requesting to resource/google
    """
    # get session from cookie
    session_id = request.cookies.get("session_id")

    if not session_id:
        return JSONResponse({"error": "No session cookie"}, status_code=401)

    response = await handle_refresh_access_token(db, session_id)
    return response