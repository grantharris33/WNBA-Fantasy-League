"""API endpoints for user profile management."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import User, UserPreferences, UserProfile

# from app.services.email import send_verification_email  # TODO: Implement email service

router = APIRouter()


# Pydantic models for requests/responses
class ProfileUpdate(BaseModel):
    """Model for updating user profile."""

    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)


class PreferencesUpdate(BaseModel):
    """Model for updating user preferences."""

    # Theme preferences
    theme: Optional[str] = Field(None, regex="^(light|dark|system)$")
    accent_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")

    # Notification preferences
    email_notifications: Optional[bool] = None
    email_draft_reminders: Optional[bool] = None
    email_trade_offers: Optional[bool] = None
    email_league_updates: Optional[bool] = None
    email_weekly_summary: Optional[bool] = None

    # Dashboard preferences
    dashboard_layout: Optional[dict] = None
    default_league_id: Optional[int] = None
    show_player_photos: Optional[bool] = None
    favorite_team_ids: Optional[list[int]] = None

    # Privacy settings
    profile_visibility: Optional[str] = Field(None, regex="^(public|league_only|private)$")
    show_email: Optional[bool] = None
    show_stats: Optional[bool] = None


class EmailUpdate(BaseModel):
    """Model for updating email address."""

    new_email: EmailStr
    password: str


class PasswordUpdate(BaseModel):
    """Model for updating password."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class ProfileResponse(BaseModel):
    """Response model for user profile."""

    id: int
    user_id: int
    email: str
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    location: Optional[str]
    timezone: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PreferencesResponse(BaseModel):
    """Response model for user preferences."""

    theme: str
    accent_color: Optional[str]
    email_notifications: bool
    email_draft_reminders: bool
    email_trade_offers: bool
    email_league_updates: bool
    email_weekly_summary: bool
    dashboard_layout: dict
    default_league_id: Optional[int]
    show_player_photos: bool
    favorite_team_ids: list[int]
    profile_visibility: str
    show_email: bool
    show_stats: bool

    class Config:
        from_attributes = True


@router.get("/api/v1/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        # Create default profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        location=profile.location,
        timezone=profile.timezone,
        email_verified=profile.email_verified,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/api/v1/profile", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Update current user's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        # Create profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # Update fields
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        location=profile.location,
        timezone=profile.timezone,
        email_verified=profile.email_verified,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/api/v1/profile/preferences", response_model=PreferencesResponse)
async def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's preferences."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        # Create profile if needed
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    preferences = db.query(UserPreferences).filter(UserPreferences.profile_id == profile.id).first()

    if not preferences:
        # Create default preferences
        preferences = UserPreferences(profile_id=profile.id, dashboard_layout={}, favorite_team_ids=[])
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return PreferencesResponse(
        theme=preferences.theme,
        accent_color=preferences.accent_color,
        email_notifications=preferences.email_notifications,
        email_draft_reminders=preferences.email_draft_reminders,
        email_trade_offers=preferences.email_trade_offers,
        email_league_updates=preferences.email_league_updates,
        email_weekly_summary=preferences.email_weekly_summary,
        dashboard_layout=preferences.dashboard_layout,
        default_league_id=preferences.default_league_id,
        show_player_photos=preferences.show_player_photos,
        favorite_team_ids=preferences.favorite_team_ids,
        profile_visibility=preferences.profile_visibility,
        show_email=preferences.show_email,
        show_stats=preferences.show_stats,
    )


@router.put("/api/v1/profile/preferences", response_model=PreferencesResponse)
async def update_preferences(
    preferences_update: PreferencesUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Update current user's preferences."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    preferences = db.query(UserPreferences).filter(UserPreferences.profile_id == profile.id).first()

    if not preferences:
        preferences = UserPreferences(profile_id=profile.id, dashboard_layout={}, favorite_team_ids=[])
        db.add(preferences)

    # Update fields
    for field, value in preferences_update.dict(exclude_unset=True).items():
        setattr(preferences, field, value)

    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)

    return PreferencesResponse(
        theme=preferences.theme,
        accent_color=preferences.accent_color,
        email_notifications=preferences.email_notifications,
        email_draft_reminders=preferences.email_draft_reminders,
        email_trade_offers=preferences.email_trade_offers,
        email_league_updates=preferences.email_league_updates,
        email_weekly_summary=preferences.email_weekly_summary,
        dashboard_layout=preferences.dashboard_layout,
        default_league_id=preferences.default_league_id,
        show_player_photos=preferences.show_player_photos,
        favorite_team_ids=preferences.favorite_team_ids,
        profile_visibility=preferences.profile_visibility,
        show_email=preferences.show_email,
        show_stats=preferences.show_stats,
    )


@router.post("/api/v1/profile/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Upload user avatar."""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")

    # In a real implementation, you would:
    # 1. Upload to S3/cloud storage
    # 2. Generate a unique filename
    # 3. Return the URL
    # For now, we'll just simulate this
    avatar_url = f"https://storage.example.com/avatars/{current_user.id}_{file.filename}"

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.avatar_url = avatar_url
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        location=profile.location,
        timezone=profile.timezone,
        email_verified=profile.email_verified,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.delete("/api/v1/profile/avatar")
async def delete_avatar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete user avatar."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        profile.avatar_url = None
        profile.updated_at = datetime.utcnow()
        db.commit()

    return {"message": "Avatar deleted successfully"}


@router.put("/api/v1/profile/email")
async def update_email(
    email_update: EmailUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Update user email address."""
    # Verify password
    if not verify_password(email_update.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email_update.new_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Update email
    current_user.email = email_update.new_email
    db.commit()

    # Update profile to mark email as unverified
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        profile.email_verified = False
        profile.email_verification_token = create_access_token(
            data={"sub": current_user.email}, expires_delta=timedelta(days=1)
        )
        profile.email_verification_sent_at = datetime.utcnow()
        db.commit()

        # Send verification email (in a real app)
        # await send_verification_email(current_user.email, profile.email_verification_token)

    return {"message": "Email updated successfully. Please check your email to verify the new address."}


@router.put("/api/v1/profile/password")
async def update_password(
    password_update: PasswordUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Update user password."""
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid current password")

    # Hash and update new password
    from app.core.security import hash_password

    current_user.hashed_password = hash_password(password_update.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/api/v1/profile/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address with token."""
    # In a real implementation, decode the token and verify
    # For now, we'll simulate this
    profile = db.query(UserProfile).filter(UserProfile.email_verification_token == token).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Invalid verification token")

    profile.email_verified = True
    profile.email_verification_token = None
    profile.email_verification_sent_at = None
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/api/v1/profile/resend-verification")
async def resend_verification(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Resend email verification."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if profile.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    # Generate new token
    profile.email_verification_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=timedelta(days=1)
    )
    profile.email_verification_sent_at = datetime.utcnow()
    db.commit()

    # Send verification email (in a real app)
    # await send_verification_email(current_user.email, profile.email_verification_token)

    return {"message": "Verification email sent"}
