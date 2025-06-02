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
    commissioner_id: int | None = None
    created_at: datetime | None = None
    invite_code: str | None = None  # Only included if user is commissioner
    max_teams: int = 12
    draft_date: datetime | None = None
    settings: dict = Field(default_factory=dict)
    is_active: bool = True

    class Config:
        orm_mode = True


class LeagueCreate(BaseModel):
    """Schema for creating a new league."""

    name: str = Field(..., min_length=1, max_length=100, description="League name")
    max_teams: int = Field(12, ge=2, le=12, description="Maximum number of teams (2-12)")
    draft_date: Optional[datetime] = Field(None, description="Scheduled draft date")
    settings: Optional[dict] = Field(default_factory=dict, description="League settings")


class LeagueUpdate(BaseModel):
    """Schema for updating league settings."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="League name")
    max_teams: Optional[int] = Field(None, ge=2, le=12, description="Maximum number of teams (2-12)")
    draft_date: Optional[datetime] = Field(None, description="Scheduled draft date")
    settings: Optional[dict] = Field(None, description="League settings")


class JoinLeagueRequest(BaseModel):
    """Schema for joining a league."""

    invite_code: str = Field(..., description="League invite code")
    team_name: str = Field(..., min_length=1, max_length=50, description="Team name")


class LeagueWithRole(BaseModel):
    """League with user's role in the league."""

    league: LeagueOut
    role: str = Field(..., description="User's role: 'commissioner' or 'member'")


class InviteCodeResponse(BaseModel):
    """Response for invite code generation."""

    invite_code: str = Field(..., description="New invite code")


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


class TeamWithRosterSlotsOut(BaseModel):
    """Team with detailed roster slot information including starter status."""
    id: int
    name: str
    league_id: int | None = None
    owner_id: int | None = None
    moves_this_week: int = 0

    roster_slots: List[RosterSlotOut] = Field(..., description="Detailed roster slots with starter info")
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


class ScheduledGameCompetitorOut(BaseModel):
    """Team information within a scheduled game."""

    team_id: str
    abbrev: Optional[str] = None
    display_name: Optional[str] = None
    score: Optional[int] = None
    is_home: Optional[bool] = None
    winner: Optional[bool] = None


class ScheduledGameOut(BaseModel):
    """Basic scheduled game info."""

    game_id: str
    start_time: Optional[str] = None
    venue: Optional[str] = None
    completed: Optional[bool] = None
    competitors: List[ScheduledGameCompetitorOut] = Field(default_factory=list)


class ScheduleDayOut(BaseModel):
    """List of games for a given day."""

    date: str
    games: List[ScheduledGameOut] = Field(default_factory=list)


class NewsArticleOut(BaseModel):
    """Representation of a news article."""

    headline: Optional[str] = None
    link: Optional[str] = None
    source: Optional[str] = None
    published: Optional[str] = None


class PlayerInjuryDetailOut(BaseModel):
    """Details about a player's injury status."""

    player_id: Optional[str] = None
    player_name: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class TeamInjuryListOut(BaseModel):
    """Injury list for a team."""

    team_id: str
    team_name: Optional[str] = None
    players: List[PlayerInjuryDetailOut] = Field(default_factory=list)


class LeagueInjuryReportOut(BaseModel):
    """Aggregated league-wide injuries."""

    teams: List[TeamInjuryListOut] = Field(default_factory=list)


# Historical scores and player performance schemas
class PlayerScoreBreakdownOut(BaseModel):
    player_id: int
    player_name: str
    position: str | None = None
    points_scored: float
    games_played: int
    is_starter: bool = False

    class Config:
        orm_mode = True


class TeamScoreHistoryOut(BaseModel):
    team_id: int
    team_name: str
    week: int
    weekly_score: float
    season_total: float
    rank: int = 0  # Will be calculated
    player_breakdown: List[PlayerScoreBreakdownOut] = Field(default_factory=list)

    class Config:
        orm_mode = True


class WeeklyScoresOut(BaseModel):
    week: int
    scores: List[TeamScoreHistoryOut]

    class Config:
        orm_mode = True


class LeagueChampionOut(BaseModel):
    team_id: int
    team_name: str
    owner_name: str | None = None
    final_score: float
    weeks_won: int = 0

    class Config:
        orm_mode = True


class TopPerformerOut(BaseModel):
    player_id: int
    player_name: str
    team_name: str
    position: str | None = None
    points_scored: float
    category: str  # e.g., "top_scorer", "top_rebounder"

    class Config:
        orm_mode = True


class ScoreTrendOut(BaseModel):
    team_id: int
    team_name: str
    weekly_scores: List[float] = Field(default_factory=list)
    weeks: List[int] = Field(default_factory=list)

    class Config:
        orm_mode = True
