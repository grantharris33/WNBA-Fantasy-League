from __future__ import annotations

from datetime import datetime, date
from typing import Any

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, JSON, Text
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
    draft_state = relationship("DraftState", back_populates="league", uselist=False, cascade="all, delete-orphan")


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
    players = relationship("Player", back_populates="team")
    weekly_lineups = relationship("WeeklyLineup", back_populates="team", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# WNBATeam (WNBA teams reference data)
# ---------------------------------------------------------------------------


class WNBATeam(Base):
    __tablename__ = "wnba_team"

    id: int = Column(Integer, primary_key=True)  # API team ID
    name: str = Column(String, nullable=False)
    location: str = Column(String, nullable=False)
    abbreviation: str = Column(String, nullable=False, unique=True)
    display_name: str = Column(String, nullable=False)
    color: str | None = Column(String)
    alternate_color: str | None = Column(String)
    logo_url: str | None = Column(String)
    venue_name: str | None = Column(String)
    venue_city: str | None = Column(String)
    venue_state: str | None = Column(String)

    # Season stats
    wins: int = Column(Integer, default=0)
    losses: int = Column(Integer, default=0)
    win_percentage: float = Column(Float, default=0.0)
    games_behind: float | None = Column(Float)
    streak: str | None = Column(String)  # e.g., "W3", "L2"
    last_10: str | None = Column(String)  # e.g., "7-3"
    conference_rank: int | None = Column(Integer)

    # Relationships
    players = relationship("Player", back_populates="wnba_team")
    home_games = relationship("Game", foreign_keys="Game.home_team_id")
    away_games = relationship("Game", foreign_keys="Game.away_team_id")


# ---------------------------------------------------------------------------
# Standings (daily standings tracking)
# ---------------------------------------------------------------------------


class Standings(Base):
    __tablename__ = "standings"
    __table_args__ = (
        UniqueConstraint("team_id", "season", "date", name="uq_standings_team_season_date"),
    )

    id: int = Column(Integer, primary_key=True)
    team_id: int = Column(Integer, ForeignKey("wnba_team.id"))
    season: int = Column(Integer, nullable=False)
    date: datetime = Column(DateTime, nullable=False)

    # Detailed standings data
    wins: int = Column(Integer, default=0)
    losses: int = Column(Integer, default=0)
    win_percentage: float = Column(Float, default=0.0)
    games_behind: float = Column(Float, default=0.0)
    home_wins: int = Column(Integer, default=0)
    home_losses: int = Column(Integer, default=0)
    away_wins: int = Column(Integer, default=0)
    away_losses: int = Column(Integer, default=0)
    division_wins: int = Column(Integer, default=0)
    division_losses: int = Column(Integer, default=0)
    conference_wins: int = Column(Integer, default=0)
    conference_losses: int = Column(Integer, default=0)
    points_for: float = Column(Float, default=0.0)
    points_against: float = Column(Float, default=0.0)
    point_differential: float = Column(Float, default=0.0)

    # Relationships
    team = relationship("WNBATeam", backref="standings_history")


# ---------------------------------------------------------------------------
# Player (readonly reference data)
# ---------------------------------------------------------------------------


class Player(Base):
    __tablename__ = "player"

    # Existing fields
    id: int = Column(Integer, primary_key=True, index=True)
    full_name: str = Column(String, nullable=False)
    position: str | None = Column(String, nullable=True)
    team_abbr: str | None = Column(String, nullable=True)

    # New biographical fields
    first_name: str | None = Column(String, nullable=True)
    last_name: str | None = Column(String, nullable=True)
    jersey_number: str | None = Column(String, nullable=True)
    height: int | None = Column(Integer, nullable=True)  # in inches
    weight: int | None = Column(Integer, nullable=True)  # in pounds
    birth_date: datetime | None = Column(DateTime, nullable=True)
    birth_place: str | None = Column(String, nullable=True)
    college: str | None = Column(String, nullable=True)
    draft_year: int | None = Column(Integer, nullable=True)
    draft_round: int | None = Column(Integer, nullable=True)
    draft_pick: int | None = Column(Integer, nullable=True)
    years_pro: int | None = Column(Integer, nullable=True)
    status: str = Column(String, default="active", nullable=False)  # active, injured, inactive
    headshot_url: str | None = Column(String, nullable=True)

    # Metadata
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign key to fantasy Team and WNBA Team
    team_id: int | None = Column(Integer, ForeignKey("team.id"), nullable=True)
    wnba_team_id: int | None = Column(Integer, ForeignKey("wnba_team.id"), nullable=True)

    # Relationships
    roster_slots = relationship("RosterSlot", back_populates="player")
    stat_lines = relationship("StatLine", back_populates="player")
    team = relationship("Team", back_populates="players")
    wnba_team = relationship("WNBATeam", back_populates="players")
    weekly_lineups = relationship("WeeklyLineup", back_populates="player", cascade="all, delete-orphan")


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
# WeeklyLineup (Historical lineups for each week)
# ---------------------------------------------------------------------------


class WeeklyLineup(Base):
    __tablename__ = "weekly_lineup"
    __table_args__ = (UniqueConstraint("team_id", "week_id", "player_id", name="uq_weekly_lineup_team_week_player"),)

    id: int = Column(Integer, primary_key=True, index=True)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    week_id: int = Column(Integer, nullable=False)
    is_starter: bool = Column(Boolean, nullable=False)
    locked_at: datetime = Column(DateTime, nullable=False)

    team = relationship("Team", back_populates="weekly_lineups")
    player = relationship("Player", back_populates="weekly_lineups")


# ---------------------------------------------------------------------------
# Game (game records)
# ---------------------------------------------------------------------------


class Game(Base):
    __tablename__ = "game"

    id: str = Column(String, primary_key=True)  # Game ID from API
    date: datetime = Column(DateTime, nullable=False, index=True)
    home_team_id: int | None = Column(Integer, ForeignKey("wnba_team.id"))
    away_team_id: int | None = Column(Integer, ForeignKey("wnba_team.id"))
    home_score: int = Column(Integer, default=0)
    away_score: int = Column(Integer, default=0)
    status: str = Column(String, default="scheduled")  # scheduled, in_progress, final
    venue: str | None = Column(String)
    attendance: int | None = Column(Integer)

    # Relationships
    home_team = relationship("WNBATeam", foreign_keys=[home_team_id], overlaps="home_games")
    away_team = relationship("WNBATeam", foreign_keys=[away_team_id], overlaps="away_games")
    stat_lines = relationship("StatLine", back_populates="game")


# ---------------------------------------------------------------------------
# StatLine (player game stats)
# ---------------------------------------------------------------------------


class StatLine(Base):
    __tablename__ = "stat_line"
    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_stat_line_player_game"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    game_id: str = Column(String, ForeignKey("game.id"), nullable=False, index=True)
    game_date: datetime = Column(DateTime, nullable=False, index=True)

    # Basic stats (existing)
    points: float = Column(Float, default=0.0)
    rebounds: float = Column(Float, default=0.0)
    assists: float = Column(Float, default=0.0)
    steals: float = Column(Float, default=0.0)
    blocks: float = Column(Float, default=0.0)

    # New detailed stats
    minutes_played: float = Column(Float, default=0.0)
    field_goals_made: int = Column(Integer, default=0)
    field_goals_attempted: int = Column(Integer, default=0)
    field_goal_percentage: float = Column(Float, default=0.0)
    three_pointers_made: int = Column(Integer, default=0)
    three_pointers_attempted: int = Column(Integer, default=0)
    three_point_percentage: float = Column(Float, default=0.0)
    free_throws_made: int = Column(Integer, default=0)
    free_throws_attempted: int = Column(Integer, default=0)
    free_throw_percentage: float = Column(Float, default=0.0)
    offensive_rebounds: int = Column(Integer, default=0)
    defensive_rebounds: int = Column(Integer, default=0)
    turnovers: int = Column(Integer, default=0)
    personal_fouls: int = Column(Integer, default=0)
    plus_minus: int = Column(Integer, default=0)

    # Game context
    is_starter: bool = Column(Boolean, default=False)
    did_not_play: bool = Column(Boolean, default=False)
    team_id: int | None = Column(Integer, ForeignKey("wnba_team.id"))
    opponent_id: int | None = Column(Integer, ForeignKey("wnba_team.id"))
    is_home_game: bool = Column(Boolean, default=True)

    # Relationships
    player = relationship("Player", back_populates="stat_lines")
    team = relationship("WNBATeam", foreign_keys=[team_id])
    opponent = relationship("WNBATeam", foreign_keys=[opponent_id])
    game = relationship("Game", back_populates="stat_lines")


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
# Ingestion tracking for backfill operations
# ---------------------------------------------------------------------------


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    id: int = Column(Integer, primary_key=True, index=True)
    start_time: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time: datetime | None = Column(DateTime)
    target_date: date = Column(Date, nullable=False)
    status: str = Column(String, nullable=False, default="running")  # running, completed, failed, partial
    games_found: int = Column(Integer, default=0)
    games_processed: int = Column(Integer, default=0)
    players_updated: int = Column(Integer, default=0)
    errors: str | None = Column(Text)  # JSON array of errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "target_date": self.target_date.isoformat(),
            "status": self.status,
            "games_found": self.games_found,
            "games_processed": self.games_processed,
            "players_updated": self.players_updated,
            "errors": self.errors,
        }


class IngestionQueue(Base):
    __tablename__ = "ingestion_queue"

    id: int = Column(Integer, primary_key=True, index=True)
    game_id: str = Column(String, nullable=False, unique=True)
    game_date: date = Column(Date, nullable=False)
    priority: int = Column(Integer, default=0)  # Higher = more important
    attempts: int = Column(Integer, default=0)
    last_attempt: datetime | None = Column(DateTime)
    status: str = Column(String, default="pending")  # pending, processing, completed, failed
    error_message: str | None = Column(Text)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "game_id": self.game_id,
            "game_date": self.game_date.isoformat(),
            "priority": self.priority,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "status": self.status,
            "error_message": self.error_message,
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
        # Use the relationship to access picks directly (no additional queries needed)
        formatted_picks = []
        for pick in self.picks:
            # Access via relationships that should be pre-loaded
            team_name = pick.team.name if pick.team else "Unknown"
            player_name = pick.player.full_name if pick.player else "Unknown"
            player_position = pick.player.position if pick.player else "Unknown"

            formatted_picks.append({
                "id": pick.id,
                "round": pick.round,
                "pick_number": pick.pick_number,
                "team_id": pick.team_id,
                "team_name": team_name,
                "player_id": pick.player_id,
                "player_name": player_name,
                "player_position": player_position,
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


# ---------------------------------------------------------------------------
# AdminMoveGrant (admin-granted emergency moves)
# ---------------------------------------------------------------------------


class AdminMoveGrant(Base):
    __tablename__ = "admin_move_grant"

    id: int = Column(Integer, primary_key=True, index=True)
    team_id: int = Column(Integer, ForeignKey("team.id"), nullable=False)
    admin_user_id: int = Column(Integer, ForeignKey("user.id"), nullable=False)
    moves_granted: int = Column(Integer, nullable=False)
    reason: str = Column(String, nullable=False)
    granted_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    week_id: int = Column(Integer, nullable=False)

    # Relationships
    team = relationship("Team", backref="admin_move_grants")
    admin_user = relationship("User", backref="admin_moves_granted")


# ---------------------------------------------------------------------------
# Analytics Models
# ---------------------------------------------------------------------------

from app.models.analytics import PlayerSeasonStats, PlayerTrends, MatchupAnalysis
