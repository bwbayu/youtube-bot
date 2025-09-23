# src/api/auth.py
from src.core.session import create_session, get_session, delete_session
from src.services.auth_service import handle_auth_callback
from src.database.init import get_db

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import httpx, urllib.parse, os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
SCOPE = "openid email profile https://www.googleapis.com/auth/youtube.readonly"

@router.get("/login")
async def login():
    state = create_session({"status": True}, 300)
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
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state")

        session = get_session(state)
        if not session or not session.get("status"):
            raise HTTPException(status_code=400, detail="Invalid state")
        
        delete_session(state)

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
        response = RedirectResponse("http://localhost:5173/home")
        response.set_cookie("session_id", session_id, httponly=True, secure=False)
        return response
    
    except HTTPException as http_exc:
        logger.warning(f"OAuth callback failed: {http_exc.detail}")
        return JSONResponse(status_code=http_exc.status_code, content={"error": http_exc.detail})
    
    except Exception as e:
        logger.error(f"Unexpected error in /callback: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})