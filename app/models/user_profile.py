"""User profile and preferences models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserProfile(Base):
    """Extended user profile information."""

    __tablename__ = "user_profile"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)

    # Profile information
    display_name: Optional[str] = Column(String(100), nullable=True)
    bio: Optional[str] = Column(Text, nullable=True)
    avatar_url: Optional[str] = Column(String(500), nullable=True)
    location: Optional[str] = Column(String(100), nullable=True)
    timezone: str = Column(String(50), default="UTC", nullable=False)

    # Verification
    email_verified: bool = Column(Boolean, default=False, nullable=False)
    email_verification_token: Optional[str] = Column(String(255), nullable=True)
    email_verification_sent_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="profile", uselist=False)
    preferences = relationship("UserPreferences", back_populates="profile", uselist=False, cascade="all, delete-orphan")


class UserPreferences(Base):
    """User preferences and settings."""

    __tablename__ = "user_preferences"

    id: int = Column(Integer, primary_key=True, index=True)
    profile_id: int = Column(Integer, ForeignKey("user_profile.id"), unique=True, nullable=False)

    # Theme preferences
    theme: str = Column(String(20), default="light", nullable=False)  # light, dark, system
    accent_color: Optional[str] = Column(String(7), nullable=True)  # Hex color

    # Notification preferences
    email_notifications: bool = Column(Boolean, default=True, nullable=False)
    email_draft_reminders: bool = Column(Boolean, default=True, nullable=False)
    email_trade_offers: bool = Column(Boolean, default=True, nullable=False)
    email_league_updates: bool = Column(Boolean, default=True, nullable=False)
    email_weekly_summary: bool = Column(Boolean, default=True, nullable=False)

    # Dashboard preferences
    dashboard_layout: dict = Column(JSON, default={}, nullable=True)  # Widget positions and visibility
    default_league_id: Optional[int] = Column(Integer, ForeignKey("league.id"), nullable=True)
    show_player_photos: bool = Column(Boolean, default=True, nullable=False)

    # Favorite teams (WNBA teams to highlight)
    favorite_team_ids: list[int] = Column(JSON, default=[], nullable=False)

    # Privacy settings
    profile_visibility: str = Column(String(20), default="public", nullable=False)  # public, league_only, private
    show_email: bool = Column(Boolean, default=False, nullable=False)
    show_stats: bool = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = relationship("UserProfile", back_populates="preferences")
    default_league = relationship("League", backref="users_with_default")
