# src/database/crud.py
from sqlalchemy.orm import Session
from src.schemas.user import UserCreate
from src.database.models import User, RefreshToken
from datetime import datetime, timedelta

def save_user(db: Session, user_data: UserCreate):
    """
    create new user if not available
    """
    user = db.query(User).filter_by(user_id=user_data.user_id).first()
    if not user:
        user = User(**user_data.model_dump())
        db.add(user)
        db.commit()

def store_refresh_token(db: Session, refresh_token_data: dict):
    """
    save refresh token data for each user
    """
    # check refresh token data based on user id
    existing = db.query(RefreshToken).filter_by(
        user_id=refresh_token_data["user_id"],
        # session_id=refresh_token_data["session_id"]
    ).first()

    if existing:
        # user id and session id still the same
        # update refresh token and expires_at
        existing.refresh_token_encrypted = refresh_token_data["refresh_token_encrypted"]
        existing.expires_at = refresh_token_data["expires_at"]
        existing.session_id = refresh_token_data["session_id"]
    else:
        # refresh token data doesn't exist
        refresh_token_obj = RefreshToken(**refresh_token_data)
        db.add(refresh_token_obj)

    db.commit()

def update_session_id(db: Session, user_id: str, old_session_id: str, new_session_id: str):
    """
    update session id on refresh token table when session is expired
    """
    token_data = db.query(RefreshToken).filter_by(user_id=user_id, session_id=old_session_id).first()
    if token_data:
        token_data.session_id = new_session_id
        token_data.expires_at = datetime.now() + timedelta(days=7)
        db.commit()

def get_refresh_token_by_session(db: Session, session_id: str):
    """
    get refresh token data by session id
    """
    return db.query(RefreshToken).filter_by(session_id=session_id).first()