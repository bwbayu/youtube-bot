from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class VideoBase(BaseModel):
    # video data for insert and fetch video
    video_id: str
    channel_id: Optional[str] = None
    playlist_id: str
    title: str
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    last_fetch_comment: Optional[datetime] = None

class VideoCreate(VideoBase):
    # create video, no additional column
    pass

class VideoResponse(VideoBase):
    # fetch video, the rest column is inheritance
    class Config:
        from_attributes = True

class VideoFetchSummary(BaseModel):
    video_id: str
    title: str
    published_at: Optional[datetime] = None
    new_comment_count: Optional[int] = None
    error: Optional[str] = None

class VideoListResponse(BaseModel):
    # list of fetch video
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
