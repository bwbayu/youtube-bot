# src/session.py
import redis
import os
import uuid
import json
from src.database import db_dependency, RefreshToken

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = 3600
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def create_session(session_data: dict, session_ttl: int = SESSION_TTL):
    session_id = str(uuid.uuid4())

    redis_client.setex(f"session:{session_id}", session_ttl, json.dumps(session_data))
    return session_id

def get_session(session_id: str):
    data = redis_client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return None

def delete_session(session_id: str):
    redis_client.delete(f"session:{session_id}")

def store_refresh_token(db: db_dependency, refresh_token_data: dict):
    # validate refresh token data
    refresh_token_obj = RefreshToken(**refresh_token_data)
    # insert data
    db.add(refresh_token_obj)
    db.commit()
    return {"status": 200, "message": "insert refresh data successfully"}

def verify_refresh_token(db: db_dependency, session_id: str, hash_refresh_token: str):
    # get refresh token data by session id
    token_data = db.query(RefreshToken).filter_by(session_id=session_id).first()
    
    # if data not available
    if not token_data:
        return False
    
    return token_data.token_hash == hash_refresh_token

def delete_refresh_token(db: db_dependency, session_id: str):
    db.query(RefreshToken).filter_by(session_id=session_id).delete()
    db.commit()