# src/core/session.py
import redis
import os
import uuid
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = 3600
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def create_session(session_data: dict, session_ttl: int = SESSION_TTL):
    session_id = str(uuid.uuid4())
    redis_client.setex(f"session:{session_id}", session_ttl, json.dumps(session_data))
    return session_id

def get_session(session_id: str):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

def delete_session(session_id: str):
    redis_client.delete(f"session:{session_id}")
