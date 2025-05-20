from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class Pagination(GenericModel, Generic[T]):
    """Generic pagination wrapper for list endpoints."""

    total: int = Field(..., description="Total number of available records")
    limit: int = Field(..., description="Limit originally requested")
    offset: int = Field(..., description="Offset originally requested")
    items: List[T] = Field(..., description="List of items in current page")


class LeagueOut(BaseModel):
    """DTO for ``league`` rows (read-only)."""

    id: int
    name: str
    created_at: datetime | None = None

    class Config:
        orm_mode = True


class PlayerOut(BaseModel):
    id: int
    full_name: str
    position: str | None = None
    team_abbr: str | None = None

    class Config:
        orm_mode = True


class RosterSlotOut(BaseModel):
    player_id: int
    position: str | None = None
    is_starter: bool = False

    # Include nested player details
    player: Optional[PlayerOut] = None

    class Config:
        orm_mode = True


class TeamOut(BaseModel):
    id: int
    name: str
    league_id: int | None = None
    owner_id: int | None = None
    moves_this_week: int = 0

    roster: List[PlayerOut] = Field(..., description="Current roster players")
    season_points: float = Field(..., description="Aggregated season points so far")

    class Config:
        orm_mode = True


class BonusOut(BaseModel):
    category: str
    points: float
    player_name: str


class ScoreOut(BaseModel):
    team_id: int
    team_name: str
    season_points: float
    weekly_delta: float
    weekly_bonus_points: float = Field(default=0.0, description="Sum of weekly leader bonuses")
    bonuses: List[BonusOut] = Field(default_factory=list, description="Weekly leader bonuses")

    class Config:
        orm_mode = True


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Draft schemas
class DraftPickRequest(BaseModel):
    player_id: int


class DraftPickResponse(BaseModel):
    id: int
    round: int
    pick_number: int
    team_id: int
    team_name: str
    player_id: int
    player_name: str
    player_position: Optional[str]
    timestamp: str
    is_auto: bool


class DraftStateResponse(BaseModel):
    id: int
    league_id: int
    current_round: int
    current_pick_index: int
    status: str
    seconds_remaining: int
    current_team_id: int
    picks: List[DraftPickResponse]


# Roster Management schemas
class AddPlayerRequest(BaseModel):
    player_id: int
    set_as_starter: bool = False


class DropPlayerRequest(BaseModel):
    player_id: int


class SetStartersRequest(BaseModel):
    starter_player_ids: List[int]


class TeamCreate(BaseModel):
    """Schema for creating a new team."""

    name: str


class TeamUpdate(BaseModel):
    """Schema for updating an existing team."""

    name: Optional[str] = None


class GameSummaryPlayerStatsOut(BaseModel):
    """Player statistics for a game summary."""

    player_id: str
    player_name: str
    points: int
    rebounds: int
    assists: int


class GameSummaryBoxScoreTeamOut(BaseModel):
    """Box score data for a single team."""

    team_id: str
    team_abbr: Optional[str] = None
    score: int
    players: List[GameSummaryPlayerStatsOut] = Field(default_factory=list)


class GameInfoOut(BaseModel):
    """Basic information about a game."""

    game_id: str
    venue: Optional[str] = None
    status: Optional[str] = None


class GameSummaryOut(BaseModel):
    """Combined game summary with box scores."""

    game: GameInfoOut
    teams: List[GameSummaryBoxScoreTeamOut]


class PlayByPlayEventOut(BaseModel):
    """Single play in the play-by-play log."""

    clock: Optional[str] = None
    description: str
    team_id: Optional[str] = None
    period: Optional[int] = None


class GamePlayByPlayOut(BaseModel):
    """Play-by-play data for a game."""

    game_id: str
    events: List[PlayByPlayEventOut]
