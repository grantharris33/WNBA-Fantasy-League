from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "user"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    teams = relationship("Team", back_populates="owner", cascade="all, delete-orphan")
    leagues_owned = relationship("League", back_populates="commissioner")
    transactions = relationship("TransactionLog", back_populates="user")


# ---------------------------------------------------------------------------
# League
# ---------------------------------------------------------------------------


class League(Base):
    __tablename__ = "league"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    commissioner_id: int | None = Column(Integer, ForeignKey("user.id"))
    commissioner = relationship("User", back_populates="leagues_owned")

    teams = relationship("Team", back_populates="league", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------


class Team(Base):
    __tablename__ = "team"
    __table_args__ = (
        UniqueConstraint("league_id", "name", name="uq_team_league_name"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False)

    owner_id: int | None = Column(Integer, ForeignKey("user.id"))
    league_id: int | None = Column(Integer, ForeignKey("league.id"))

    owner = relationship("User", back_populates="teams")
    league = relationship("League", back_populates="teams")

    roster_slots = relationship("RosterSlot", back_populates="team", cascade="all, delete-orphan")
    scores = relationship("TeamScore", back_populates="team", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Player (readonly reference data)
# ---------------------------------------------------------------------------


class Player(Base):
    __tablename__ = "player"

    id: int = Column(Integer, primary_key=True, index=True)
    full_name: str = Column(String, nullable=False)
    position: str | None = Column(String, nullable=True)
    team_abbr: str | None = Column(String, nullable=True)

    roster_slots = relationship("RosterSlot", back_populates="player")
    stat_lines = relationship("StatLine", back_populates="player")


# ---------------------------------------------------------------------------
# RosterSlot (many-to-many Team<->Player over season, latest state)
# ---------------------------------------------------------------------------


class RosterSlot(Base):
    __tablename__ = "roster_slot"
    __table_args__ = (
        UniqueConstraint("team_id", "player_id", name="uq_roster_slot_team_player"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    position: str | None = Column(String, nullable=True)

    team = relationship("Team", back_populates="roster_slots")
    player = relationship("Player", back_populates="roster_slots")


# ---------------------------------------------------------------------------
# StatLine (player game stats)
# ---------------------------------------------------------------------------


class StatLine(Base):
    __tablename__ = "stat_line"
    __table_args__ = (
        UniqueConstraint("player_id", "game_date", name="uq_stat_line_player_date"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    game_date: datetime = Column(DateTime, nullable=False, index=True)

    points: float = Column(Float, default=0.0)
    rebounds: float = Column(Float, default=0.0)
    assists: float = Column(Float, default=0.0)
    steals: float = Column(Float, default=0.0)
    blocks: float = Column(Float, default=0.0)

    player = relationship("Player", back_populates="stat_lines")


# ---------------------------------------------------------------------------
# TeamScore (aggregated weekly points)
# ---------------------------------------------------------------------------


class TeamScore(Base):
    __tablename__ = "team_score"
    __table_args__ = (
        UniqueConstraint("team_id", "week", name="uq_team_week"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    week: int = Column(Integer, nullable=False)
    score: float = Column(Float, default=0.0)

    team = relationship("Team", back_populates="scores")


# ---------------------------------------------------------------------------
# TransactionLog (audit)
# ---------------------------------------------------------------------------


class TransactionLog(Base):
    __tablename__ = "transaction_log"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int | None = Column(Integer, ForeignKey("user.id"))
    action: str = Column(String, nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="transactions")
