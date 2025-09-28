# src/database/models.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
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

# https://youtube.googleapis.com/youtube/v3/playlistItems
class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String, primary_key=True, unique=True, nullable=False, index=True) # items[i].contentDetails.videoId
    channel_id = Column(String, nullable=True, index=True) # items[i].snippet.channelId
    playlist_id = Column(String, nullable=False, index=True) # items[i].snippet.playlistId
    title = Column(String, nullable=False) # items[i].snippet.title
    description = Column(Text, nullable=True) # items[i].snippet.description
    published_at = Column(DateTime(timezone=True), nullable=True) # items[i].snippet.publishedAt
    last_fetch_comment = Column(DateTime(timezone=True), nullable=True) # update everytime fetch comment and used to filter newest comment

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")

# https://www.googleapis.com/youtube/v3/commentThreads
class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(String, primary_key=True, unique=True, nullable=False, index=True) # items[i].snippet.topLevelComment[j].id
    video_id = Column(String, ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True) # items[i].snippet.videoId
    author_display_name = Column(String, nullable=True) # items[i].snippet.topLevelComment[j].snippet.authorDisplayName
    text = Column(Text, nullable=False) # items[i].snippet.topLevelComment[j].snippet.textDisplay/textOriginal
    published_at = Column(DateTime(timezone=True), nullable=False) # items[i].snippet.topLevelComment[j].snippet.publishedAt
    updated_at = Column(DateTime(timezone=True), nullable=False) # items[i].snippet.topLevelComment[j].snippet.updatedAt
    is_judi = Column(Boolean, default=False)
    label = Column(Boolean, default=False) # true label of model prediction (for further training)
    confidence = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True),  default=lambda: datetime.now(timezone.utc), nullable=False)

    video = relationship("Video", back_populates="comments")