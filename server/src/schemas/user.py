from pydantic import BaseModel, EmailStr

# insert user
class UserCreate(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    channel_id: str
    channel_name: str
    custom_url: str
    playlist_id: str

# fetch user
class UserResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    channel_id: str
    custom_url: str

    class Config:
        orm_mode = True