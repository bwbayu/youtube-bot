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
    last_fetch_comment: datetime

class VideoCreate(VideoBase):
    # create video, no additional column
    pass

class VideoResponse(VideoBase):
    # fetch video, the rest column is inheritance
    class Config:
        orm_mode = True

class VideoListResponse(BaseModel):
    # list of fetch video
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int