# src/api/auth.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from src.core.session import create_session, get_session, delete_session
from src.services.auth_service import handle_auth_callback
from src.database.init import get_db
from sqlalchemy.orm import Session
import httpx, urllib.parse, os

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
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        return JSONResponse({"error": "Missing code or state"}, status_code=400)

    # TODO: add try catch
    session = get_session(state)
    if not session or not session.get("status"):
        return JSONResponse({"error": "Invalid state"}, status_code=400)
    
    # TODO: add try catch
    delete_session(state)

    # Exchange code for tokens
    # TODO: add try catch
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })

    tokens = token_res.json()
    if "access_token" not in tokens:
        return JSONResponse({"error": "Token exchange failed", "detail": tokens}, status_code=400)

    # Continue to service
    # TODO: add try catch
    session_id, user_data = await handle_auth_callback({"tokens": tokens}, db)

    response = JSONResponse({
        "status": "login",
        "user_data": user_data.model_dump()
    })
    # TODO: add try catch
    response.set_cookie("session_id", session_id, httponly=True)
    return response