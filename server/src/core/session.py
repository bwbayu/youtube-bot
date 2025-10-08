# src/core/session.py
import redis.asyncio as redis
import os
import uuid
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = 3600
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def create_session(session_data: dict, session_ttl: int = SESSION_TTL):
    # create redis session
    session_id = str(uuid.uuid4())
    await redis_client.setex(f"session:{session_id}", session_ttl, json.dumps(session_data))
    return session_id

async def get_session(session_id: str):
    # get redis session based on session_id/keys
    data = await redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

async def delete_session(session_id: str):
    # delete redis session if needed because the session already has TTL (time to live)
    await redis_client.delete(f"session:{session_id}")
