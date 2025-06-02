from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, JSON
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
    is_admin: bool = Column(Boolean, default=False, nullable=False)

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
    invite_code: str = Column(String, unique=True, nullable=False)
    max_teams: int = Column(Integer, default=12, nullable=False)
    draft_date: datetime | None = Column(DateTime, nullable=True)
    settings: dict = Column(JSON, default={}, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)

    commissioner_id: int | None = Column(Integer, ForeignKey("user.id"))
    commissioner = relationship("User", back_populates="leagues_owned")

    teams = relationship("Team", back_populates="league", cascade="all, delete-orphan")
    draft_state = relationship("DraftState", back_populates="league", uselist=False)


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------


class Team(Base):
    __tablename__ = "team"
    __table_args__ = (UniqueConstraint("league_id", "name", name="uq_team_league_name"),)

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False)
    moves_this_week: int = Column(Integer, default=0, nullable=False)

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
    __table_args__ = (UniqueConstraint("team_id", "player_id", name="uq_roster_slot_team_player"),)

    id: int = Column(Integer, primary_key=True, index=True)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    position: str | None = Column(String, nullable=True)
    is_starter: bool = Column(Boolean, default=False, nullable=False)

    team = relationship("Team", back_populates="roster_slots")
    player = relationship("Player", back_populates="roster_slots")


# ---------------------------------------------------------------------------
# StatLine (player game stats)
# ---------------------------------------------------------------------------


class StatLine(Base):
    __tablename__ = "stat_line"
    __table_args__ = (UniqueConstraint("player_id", "game_date", name="uq_stat_line_player_date"),)

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
    __table_args__ = (UniqueConstraint("team_id", "week", name="uq_team_week"),)

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
    path: str | None = Column(String, nullable=True)  # Request path
    method: str | None = Column(String, nullable=True)  # HTTP method
    patch: str | None = Column(String, nullable=True)  # JSONPatch for diff

    user = relationship("User", back_populates="transactions")


# ---------------------------------------------------------------------------
# IngestLog (error log for nightly ingest)
# ---------------------------------------------------------------------------


class IngestLog(Base):
    __tablename__ = "ingest_log"

    id: int = Column(Integer, primary_key=True, index=True)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    provider: str = Column(String, nullable=False)
    message: str = Column(String, nullable=False)

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Draft Models
# ---------------------------------------------------------------------------


class DraftState(Base):
    __tablename__ = "draft_state"

    id: int = Column(Integer, primary_key=True, index=True)
    league_id: int = Column(Integer, ForeignKey("league.id"), nullable=False, unique=True)
    current_round: int = Column(Integer, default=1, nullable=False)
    current_pick_index: int = Column(Integer, default=0, nullable=False)
    status: str = Column(String, default="pending", nullable=False)  # pending, active, paused, completed
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # When pause/resume, we store the seconds remaining for the current pick
    seconds_remaining: int = Column(Integer, default=60, nullable=False)

    # Store the pick order as comma-separated team IDs, e.g. "1,2,3,4,4,3,2,1"
    pick_order: str = Column(String, nullable=False)

    league = relationship("League", back_populates="draft_state")
    picks = relationship("DraftPick", back_populates="draft", cascade="all, delete-orphan")

    def get_pick_order(self) -> list[int]:
        """Convert the stored pick_order string to a list of team IDs."""
        return [int(team_id) for team_id in self.pick_order.split(",")]

    def current_team_id(self) -> int:
        """Get the team ID whose turn it is to pick."""
        pick_order = self.get_pick_order()
        # Calculate current position in the snake draft
        total_picks_per_round = len(pick_order) // 2  # Half of teams in pick_order (due to snake format)

        if self.current_round % 2 == 1:  # Odd round (forward)
            return pick_order[self.current_pick_index]
        else:  # Even round (backward)
            return pick_order[total_picks_per_round - 1 - self.current_pick_index]

    def advance_pick(self, timer_seconds: int = 60) -> None:
        """Advance to the next pick in the draft."""
        pick_order = self.get_pick_order()
        total_picks_per_round = len(pick_order) // 2

        # Advance pick index
        self.current_pick_index += 1

        # If we've reached the end of a round
        if self.current_pick_index >= total_picks_per_round:
            self.current_round += 1
            self.current_pick_index = 0

        # Reset timer for new pick
        self.seconds_remaining = timer_seconds

    def as_dict(self) -> dict:
        """Return the draft state as a dictionary for API responses."""
        # Get formatted picks for this draft
        from sqlalchemy.orm import object_session
        session = object_session(self)

        formatted_picks = []
        if session:
            # Import here to avoid circular imports
            from app.models import Player, Team

            for pick in self.picks:
                player = session.query(Player).filter(Player.id == pick.player_id).first()
                team = session.query(Team).filter(Team.id == pick.team_id).first()

                formatted_picks.append({
                    "id": pick.id,
                    "round": pick.round,
                    "pick_number": pick.pick_number,
                    "team_id": pick.team_id,
                    "team_name": team.name if team else "Unknown",
                    "player_id": pick.player_id,
                    "player_name": player.full_name if player else "Unknown",
                    "player_position": player.position if player else "Unknown",
                    "timestamp": pick.timestamp.isoformat(),
                    "is_auto": pick.is_auto,
                })

        return {
            "id": self.id,
            "league_id": self.league_id,
            "current_round": self.current_round,
            "current_pick_index": self.current_pick_index,
            "status": self.status,
            "seconds_remaining": self.seconds_remaining,
            "current_team_id": self.current_team_id(),
            "picks": formatted_picks,
        }


class DraftPick(Base):
    __tablename__ = "draft_pick"

    id: int = Column(Integer, primary_key=True, index=True)
    draft_id: int = Column(Integer, ForeignKey("draft_state.id"), nullable=False)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    round: int = Column(Integer, nullable=False)
    pick_number: int = Column(Integer, nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_auto: bool = Column(Integer, default=False, nullable=False)  # True if auto-picked

    # Relationships
    draft = relationship("DraftState", back_populates="picks")
    team = relationship("Team", backref="draft_picks")
    player = relationship("Player", backref="draft_picks")

    __table_args__ = (
        UniqueConstraint("draft_id", "player_id", name="uq_draft_player"),
        UniqueConstraint("draft_id", "round", "pick_number", name="uq_draft_round_pick"),
    )


# ---------------------------------------------------------------------------
# WeeklyBonus (weekly leader bonuses)
# ---------------------------------------------------------------------------


class WeeklyBonus(Base):
    __tablename__ = "weekly_bonus"
    __table_args__ = (UniqueConstraint("week_id", "player_id", "category", name="uq_bonus_week_player_category"),)

    id: int = Column(Integer, primary_key=True, index=True)
    week_id: int = Column(Integer, nullable=False, index=True)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    category: str = Column(String, nullable=False)  # top_scorer, top_rebounder, etc.
    points: float = Column(Float, default=0.0, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    player = relationship("Player", backref="weekly_bonuses")
    team = relationship("Team", backref="weekly_bonuses")
