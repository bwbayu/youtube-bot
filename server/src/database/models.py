# src/database/models.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    channel_id = Column(String)
    channel_name = Column(String)
    custom_url = Column(String)
    playlist_id = Column(String)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    """
    refresh token is ecrypted because using plain is security issue, 
    if using hash, you cannot get the original token, 
    so using encrypt is the best option because better security and can get original token
    """
    refresh_token_encrypted = Column(String, nullable=False)
    expires_at = Column(DateTime)
