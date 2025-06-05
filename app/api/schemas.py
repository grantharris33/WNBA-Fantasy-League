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

    # New biographical fields
    first_name: str | None = None
    last_name: str | None = None
    jersey_number: str | None = None
    height: int | None = None  # in inches
    weight: int | None = None  # in pounds
    birth_date: datetime | None = None
    birth_place: str | None = None
    college: str | None = None
    draft_year: int | None = None
    draft_round: int | None = None
    draft_pick: int | None = None
    years_pro: int | None = None
    status: str = "active"  # active, injured, inactive
    headshot_url: str | None = None

    # Metadata
    created_at: datetime | None = None
    updated_at: datetime | None = None
    team_id: int | None = None

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
    position: str | None = None
    team_abbr: str | None = None
    total_points: float
    games_played: int
    avg_points: float

    class Config:
        orm_mode = True


class ScoreTrendOut(BaseModel):
    team_id: int
    team_name: str
    weekly_scores: List[dict] = Field(default_factory=list)
    total_points: float = Field(default=0.0)

    class Config:
        orm_mode = True


# Comprehensive Statistics Schemas
class ComprehensivePlayerStatsOut(BaseModel):
    """Comprehensive player statistics for a game."""

    player_id: int
    player_name: str
    position: Optional[str] = None
    is_starter: bool = False
    did_not_play: bool = False

    # Basic stats
    points: float = 0.0
    rebounds: float = 0.0
    assists: float = 0.0
    steals: float = 0.0
    blocks: float = 0.0

    # Detailed stats
    minutes_played: float = 0.0
    field_goals_made: int = 0
    field_goals_attempted: int = 0
    field_goal_percentage: float = 0.0
    three_pointers_made: int = 0
    three_pointers_attempted: int = 0
    three_point_percentage: float = 0.0
    free_throws_made: int = 0
    free_throws_attempted: int = 0
    free_throw_percentage: float = 0.0
    offensive_rebounds: int = 0
    defensive_rebounds: int = 0
    turnovers: int = 0
    personal_fouls: int = 0
    plus_minus: int = 0

    # Game context
    team_id: Optional[int] = None
    opponent_id: Optional[int] = None
    is_home_game: bool = True

    class Config:
        orm_mode = True


class GameOut(BaseModel):
    """Comprehensive game information."""

    id: str
    date: datetime
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    home_score: int = 0
    away_score: int = 0
    status: str = "scheduled"
    venue: Optional[str] = None
    attendance: Optional[int] = None

    class Config:
        orm_mode = True


class ComprehensiveGameStatsOut(BaseModel):
    """Complete game statistics including game info and all player stats."""

    game: GameOut
    player_stats: List[ComprehensivePlayerStatsOut] = Field(default_factory=list)

    class Config:
        orm_mode = True


# Weekly Lineup Schemas
class WeeklyLineupPlayerOut(BaseModel):
    """Player in a weekly lineup."""

    player_id: int
    player_name: str
    position: str | None = None
    team_abbr: str | None = None
    is_starter: bool = False
    locked: bool = False
    locked_at: Optional[datetime] = None


class WeeklyLineupOut(BaseModel):
    """Weekly lineup for a team."""

    week_id: int
    lineup: List[WeeklyLineupPlayerOut] = Field(default_factory=list)
    is_current: bool = False


class LineupHistoryOut(BaseModel):
    """Historical lineups for a team."""

    history: List[WeeklyLineupOut] = Field(default_factory=list)


class SetWeeklyStartersRequest(BaseModel):
    """Request to set starters for a specific week."""

    starter_player_ids: List[int]


class LineupLockResponse(BaseModel):
    """Response for lineup locking operation."""

    week_id: int
    teams_processed: int
    locked_at: datetime


# WNBA Data Schemas
class WNBATeamOut(BaseModel):
    """WNBA team information."""

    id: int
    name: str
    location: str
    abbreviation: str
    display_name: str
    color: Optional[str] = None
    alternate_color: Optional[str] = None
    logo_url: Optional[str] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    venue_state: Optional[str] = None
    wins: int = 0
    losses: int = 0
    win_percentage: float = 0.0
    games_behind: Optional[float] = None
    streak: Optional[str] = None
    last_10: Optional[str] = None
    conference_rank: Optional[int] = None

    class Config:
        orm_mode = True


class StandingsOut(BaseModel):
    """Team standings information."""

    rank: int
    team_id: int
    team_name: str
    team_abbr: str
    wins: int
    losses: int
    win_percentage: float
    games_behind: float
    streak: Optional[str] = None
    last_10: Optional[str] = None
    conference_rank: Optional[int] = None
    home_record: str
    away_record: str
    points_for: float
    points_against: float
    point_differential: float


class TeamRosterPlayerOut(BaseModel):
    """Player information in team roster."""

    player_id: int
    full_name: str
    jersey_number: Optional[str] = None
    position: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    college: Optional[str] = None
    years_pro: Optional[int] = None
    status: str = "active"
    headshot_url: Optional[str] = None
    games_played: int = 0
    ppg: float = 0.0
    rpg: float = 0.0
    apg: float = 0.0
    mpg: float = 0.0
    fg_percentage: float = 0.0


class TeamScheduleGameOut(BaseModel):
    """Game information in team schedule."""

    game_id: str
    date: datetime
    is_home: bool
    opponent_id: Optional[int] = None
    opponent_name: str
    opponent_abbr: str
    team_score: int
    opponent_score: int
    status: str
    venue: Optional[str] = None
    result: Optional[str] = None  # W, L, or None if not final


class TeamStatsOut(BaseModel):
    """Team statistics summary."""

    team_id: int
    team_name: str
    team_abbr: str
    games_played: int
    wins: int
    losses: int
    win_percentage: float
    home_record: str
    away_record: str
    points_per_game: float
    points_allowed_per_game: float
    point_differential: float


class PlayerGameLogOut(BaseModel):
    """Player game log entry."""

    game_id: str
    date: datetime
    opponent_id: Optional[int] = None
    opponent_name: str
    opponent_abbr: str
    is_home: bool
    is_starter: bool
    minutes_played: float
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    field_goals_made: int
    field_goals_attempted: int
    field_goal_percentage: float
    three_pointers_made: int
    three_pointers_attempted: int
    three_point_percentage: float
    free_throws_made: int
    free_throws_attempted: int
    free_throw_percentage: float
    plus_minus: int
    did_not_play: bool


class LeagueLeaderOut(BaseModel):
    """League leader in a statistical category."""

    rank: int
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    team_abbr: str
    games_played: int
    value: float
    position: Optional[str] = None


class PlayerSearchResultOut(BaseModel):
    """Player search result."""

    player_id: int
    full_name: str
    jersey_number: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    team_abbr: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    college: Optional[str] = None
    years_pro: Optional[int] = None
    status: str = "active"
    headshot_url: Optional[str] = None
    ppg: float = 0.0
    rpg: float = 0.0
    apg: float = 0.0
    games_played: int = 0


class DetailedPlayerStatsOut(BaseModel):
    """Detailed player statistics including advanced metrics."""

    player_id: int
    player_name: str
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    team_abbr: Optional[str] = None
    position: Optional[str] = None
    jersey_number: Optional[str] = None

    # Basic info
    height: Optional[int] = None
    weight: Optional[int] = None
    college: Optional[str] = None
    years_pro: Optional[int] = None
    status: str = "active"
    headshot_url: Optional[str] = None

    # Season stats
    season: int
    games_played: int = 0
    games_started: int = 0

    # Per game averages
    ppg: float = 0.0
    rpg: float = 0.0
    apg: float = 0.0
    spg: float = 0.0
    bpg: float = 0.0
    topg: float = 0.0
    mpg: float = 0.0

    # Shooting percentages
    fg_percentage: float = 0.0
    three_point_percentage: float = 0.0
    ft_percentage: float = 0.0

    # Advanced metrics
    per: float = 0.0
    true_shooting_percentage: float = 0.0
    usage_rate: float = 0.0

    # Fantasy specific
    fantasy_ppg: float = 0.0
    consistency_score: float = 0.0
    ceiling: float = 0.0
    floor: float = 0.0


class ScoreUpdateResponse(BaseModel):
    """Response for manual score update endpoint."""
    success: bool
    message: str
    updated_at: datetime
    week_updated: int
