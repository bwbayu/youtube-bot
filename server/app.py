# app.py
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
import httpx, os, urllib.parse
from dotenv import load_dotenv
from datetime import datetime

from src.session import create_session, get_session, delete_session, store_refresh_token
from src.utils import hash_refresh_token
from src.database import db_dependency
from src.database import lifespan
import jwt

load_dotenv()

# Load env
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/callback" 
SCOPE = "openid email profile https://www.googleapis.com/auth/youtube.readonly"

app = FastAPI(lifespan=lifespan)
async_client = httpx.AsyncClient()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/auth/login")
async def login():
    # set temp session state
    session_data = {
        "status": True
    }
    state = create_session(session_data=session_data, session_ttl=300)

    # create auth url
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

    # redirect to google auth url
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        return JSONResponse({"error": "Missing code or state"}, status_code=400)
    
    # Validasi state
    session = get_session(state)
    if not session or not session.get("status"):
        return JSONResponse({"error": "Invalid state"}, status_code=400)
    
    # Delete temp session
    delete_session(state)

    # send request to get token data
    response = await async_client.post(
        "https://oauth2.googleapis.com/token", 
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })
    tokens = response.json()
    # get user data
    user_decode = jwt.decode(tokens['id_token'], options={"verify_signature": False})
    user_info = {k: v for k, v in user_decode.items() if k in {'sub', 'email', 'name'}}
    
    # validate access token
    if "access_token" not in tokens:
        return {"error": "Token exchange failed", "detail": tokens}
    
    # create session
    session_data = {
        "user_id": user_info['sub'],
        "access_token": tokens['access_token']
    }

    # add session to redis
    session_id = create_session(session_data, tokens['expires_in'])

    # add refresh token data
    refresh_token_data = {
        "session_id": session_id,
        "user_id": user_info['sub'],
        "token_hash": hash_refresh_token(tokens['refresh_token']),
        "expires_at": datetime.now() + (tokens['refresh_token_expires_in'] if tokens['refresh_token_expires_in'] else 604800) # 7 days
    }
    ref_token_response = store_refresh_token(db_dependency, refresh_token_data)

    # get channel data
    channel_data = await get_channel_info(tokens['access_token'])

    # TODO: add session to redis and sql and create cookies
    return {"status": "login", "channel_data": channel_data, 'tokens': tokens, 'user_info': user_info}

async def get_channel_info(access_token: str):
    response = await async_client.get(
        url='https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails&mine=true',
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code != 200:
        return None
    
    items = response.json().get('items', [])
    if not items:
        return None
    
    item = items[0]
    channel_data = {
        "channel_id": item.get("id"),
        "playlist_id": item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads"),
        "name": item.get("snippet", {}).get("title"),
        "custom_url": item.get("snippet", {}).get("customUrl"),
    }
    return channel_data
