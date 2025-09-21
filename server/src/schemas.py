from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# insert user
class UserCreate(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    channel_id: str
    custom_url: str

# fetch user
class UserResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: EmailStr
    channel_id: str
    custom_url: str

    class Config:
        orm_mode = True



# class SessionSchema(BaseModel):
#     session_id: str
#     user_id: str
#     access_token: str
#     id_token: Optional[str]
#     expires_at: datetime