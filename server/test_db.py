from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://root:12345678@localhost:5433/botjudol"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).fetchone()
        print("Connected! PostgreSQL version:", version[0])
except Exception as e:
    print("Connection failed:", e)

# LATER: google/server return 401 in the middle of request something
# async def fetch_google_with_refresh_retry(
#     request: Request,
#     db: Session,
#     google_api_call_fn: Callable[[str], Awaitable[httpx.Response]]
# ) -> httpx.Response:
#     redis = get_redis()
#     session_id = request.cookies.get("session_id")
#     session_data = await redis.get(f"session:{session_id}")
#     access_token = session_data["access_token"]

#     response = await google_api_call_fn(access_token)

#     if response.status_code == 401:
#         # Refresh token
#         refresh_token_obj = get_refresh_token_by_session(db, session_id)
#         new_access_token = await refresh_access_token(refresh_token_obj.refresh_token_plain)

#         # Create new session
#         new_session_id = create_session({"user_id": refresh_token_obj.user_id, "access_token": new_access_token}, 3600)
#         update_session_id(db, refresh_token_obj.user_id, session_id, new_session_id)

#         # Retry
#         response = await google_api_call_fn(new_access_token)

#     return response
