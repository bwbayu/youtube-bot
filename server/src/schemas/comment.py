from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from src.schemas.video import VideoResponse

class CommentBase(BaseModel):
    # comment data for insert and fetch
    comment_id: str
    video_id: str
    author_display_name: str
    text: str
    published_at: datetime
    updated_at: datetime

class CommentCreate(CommentBase):
    # insert comment
    pass

class CommentClassification(BaseModel):
    # update comment classification result
    comment_id: str
    is_judi: bool

class CommentResponse(CommentBase):
    # fetch comment with classification result
    is_judi: bool

    class Config:
        from_attributes = True

class CommentListResponse(BaseModel):
    # list of fetch comment
    videoDetail: VideoResponse
    items: list[CommentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool