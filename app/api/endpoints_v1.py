from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import (
    AddPlayerRequest,
    BonusOut,
    DraftPickRequest,
    DraftPickResponse,
    DraftStateResponse,
    DropPlayerRequest,
    GamePlayByPlayOut,
    GameSummaryOut,
    InviteCodeResponse,
    JoinLeagueRequest,
    LeagueChampionOut,
    LeagueCreate,
    LeagueOut,
    LeagueUpdate,
    LeagueWithRole,
    LineupHistoryOut,
    LineupLockResponse,
    NewsArticleOut,
    Pagination,
    PlayerOut,
    PlayerScoreBreakdownOut,
    RosterSlotOut,
    ScheduleDayOut,
    ScoreOut,
    ScoreTrendOut,
    SetStartersRequest,
    SetWeeklyStartersRequest,
    TeamCreate,
    TeamOut,
    TeamScoreHistoryOut,
    TeamUpdate,
    TeamWithRosterSlotsOut,
    TopPerformerOut,
    UserOut,
    WeeklyLineupOut,
    WeeklyLineupPlayerOut,
    WeeklyScoresOut,
)
from app.core.database import get_db
from app.models import DraftState, League, Player, RosterSlot, StatLine, Team, TeamScore, User, WeeklyBonus
from app.services.draft import DraftService
from app.services.lineup import LineupService
from app.services.roster import RosterService
from app.services.team import TeamService, map_team_to_out

# CORS support
router = APIRouter(prefix="/api/v1")
router_roster = APIRouter()

# ---------------------------------------------------------------------------
# 5-B List Leagues – GET /api/v1/leagues
# ---------------------------------------------------------------------------


@router.get("/leagues", response_model=Pagination[LeagueOut])
def list_leagues(  # noqa: D401
    *, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)
):
    total = db.query(League).count()
    leagues = db.query(League).order_by(League.id).offset(offset).limit(limit).all()  # deterministic ordering

    items = [LeagueOut.from_orm(league) for league in leagues]
    return Pagination[LeagueOut](total=total, limit=limit, offset=offset, items=items)


# ---------------------------------------------------------------------------
# 5-C Team Detail – GET /api/v1/teams/{team_id}
# ---------------------------------------------------------------------------


@router.get("/teams/{team_id}", response_model=TeamWithRosterSlotsOut)
def team_detail(*, team_id: int, db: Session = Depends(get_db)):  # noqa: D401
    from sqlalchemy.orm import joinedload

    team = (
        db.query(Team)
        .options(joinedload(Team.roster_slots).joinedload(RosterSlot.player), joinedload(Team.scores))
        .filter_by(id=team_id)
        .one_or_none()
    )

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Ensure starters are carried over from previous week if needed
    from app.services.roster import RosterService

    roster_service = RosterService(db)
    roster_service.ensure_starters_carried_over(team_id)

    # Refresh the team data to get updated starter information
    team = (
        db.query(Team)
        .options(joinedload(Team.roster_slots).joinedload(RosterSlot.player), joinedload(Team.scores))
        .filter_by(id=team_id)
        .one_or_none()
    )

    # Build roster slots with player details and starter info
    roster_slots: List[RosterSlotOut] = []
    for rs in team.roster_slots:
        player_out = PlayerOut.from_orm(rs.player)
        roster_slot = RosterSlotOut(
            player_id=rs.player_id, position=rs.position, is_starter=rs.is_starter, player=player_out
        )
        roster_slots.append(roster_slot)

    # Season points = sum of all weekly scores
    season_points = sum(score.score for score in team.scores) if team.scores else 0

    return TeamWithRosterSlotsOut(
        id=team.id,
        name=team.name,
        league_id=team.league_id,
        owner_id=team.owner_id,
        moves_this_week=team.moves_this_week,
        roster_slots=roster_slots,
        season_points=round(season_points, 2),
    )


# ---------------------------------------------------------------------------
# 5-D Current Scores – GET /api/v1/scores/current
# ---------------------------------------------------------------------------


@router.get("/scores/current", response_model=List[ScoreOut])
def current_scores(*, db: Session = Depends(get_db)) -> List[ScoreOut]:  # noqa: D401
    from app.services.cache import CacheService

    # Try to get from cache first
    cache_service = CacheService(db)
    cache_key = cache_service.create_cache_key("current_scores")
    cached_scores = cache_service.get(cache_key)

    if cached_scores is not None:
        # Convert cached dictionaries back to ScoreOut objects
        return [ScoreOut(**score_data) for score_data in cached_scores]

    # Determine latest week id (if any)
    latest_week = db.query(func.max(TeamScore.week)).scalar()

    teams = db.query(Team).all()
    result: List[ScoreOut] = []

    for team in teams:
        season_points = sum(score.score for score in team.scores)

        # Weekly delta = score of latest week if exists else 0
        latest_week_score = 0.0
        if latest_week is not None:
            for score in team.scores:
                if score.week == latest_week:
                    latest_week_score = score.score
                    break

        # Get weekly bonuses for this team
        weekly_bonuses = []
        weekly_bonus_total = 0.0
        if latest_week is not None:
            # Query all bonuses for this team in the latest week
            bonuses = (
                db.query(WeeklyBonus, Player.full_name)
                .join(Player, WeeklyBonus.player_id == Player.id)
                .filter(WeeklyBonus.team_id == team.id, WeeklyBonus.week_id == latest_week)
                .all()
            )

            for bonus, player_name in bonuses:
                weekly_bonuses.append(BonusOut(category=bonus.category, points=bonus.points, player_name=player_name))
                weekly_bonus_total += bonus.points

        result.append(
            ScoreOut(
                team_id=team.id,
                team_name=team.name,
                season_points=round(season_points, 2),
                weekly_delta=round(latest_week_score, 2),
                weekly_bonus_points=round(weekly_bonus_total, 2),
                bonuses=weekly_bonuses,
            )
        )

    # Sort descending by season points
    result.sort(key=lambda s: s.season_points, reverse=True)

    # Cache the results for 5 minutes - convert to dictionaries for JSON serialization
    cache_data = [score.dict() for score in result]
    cache_service.set(cache_key, cache_data, ttl_seconds=300, endpoint="current_scores")

    return result


# ---------------------------------------------------------------------------
# 5-E Historical Scores – GET /api/v1/scores/history
# ---------------------------------------------------------------------------


@router.get("/scores/history", response_model=List[WeeklyScoresOut])
def historical_scores(
    *, db: Session = Depends(get_db), league_id: int = Query(None)
) -> List[WeeklyScoresOut]:  # noqa: D401
    """Get historical weekly scores for all teams."""
    # Get all weeks that have scores
    weeks_query = db.query(TeamScore.week).distinct().order_by(TeamScore.week)
    weeks = [week[0] for week in weeks_query.all()]

    result = []

    for week in weeks:
        # Get all team scores for this week
        weekly_scores = []
        teams_query = db.query(Team)
        if league_id:
            teams_query = teams_query.filter(Team.league_id == league_id)
        teams = teams_query.all()

        for team in teams:
            # Calculate season total up to this week
            season_total = sum(score.score for score in team.scores if score.week <= week)

            # Get weekly score
            weekly_score = 0.0
            for score in team.scores:
                if score.week == week:
                    weekly_score = score.score
                    break

            # Get player breakdown for this week
            player_breakdown = []
            for roster_slot in team.roster_slots:
                # Calculate player's points for this week
                player_points = 0.0
                games_played = 0

                # Sum points from stat lines in this week
                for stat_line in roster_slot.player.stat_lines:
                    # Simple week calculation - in a real app you'd have proper week boundaries
                    stat_week = stat_line.game_date.isocalendar()[1]
                    if stat_week == week:
                        player_points += stat_line.points
                        games_played += 1

                if player_points > 0 or games_played > 0:
                    player_breakdown.append(
                        PlayerScoreBreakdownOut(
                            player_id=roster_slot.player_id,
                            player_name=roster_slot.player.full_name,
                            position=roster_slot.player.position,
                            points_scored=round(player_points, 2),
                            games_played=games_played,
                            is_starter=roster_slot.is_starter,
                        )
                    )

            weekly_scores.append(
                TeamScoreHistoryOut(
                    team_id=team.id,
                    team_name=team.name,
                    week=week,
                    weekly_score=round(weekly_score, 2),
                    season_total=round(season_total, 2),
                    player_breakdown=player_breakdown,
                )
            )

        # Sort by season total and assign ranks
        weekly_scores.sort(key=lambda s: s.season_total, reverse=True)
        for i, score in enumerate(weekly_scores):
            score.rank = i + 1

        result.append(WeeklyScoresOut(week=week, scores=weekly_scores))

    return result


# ---------------------------------------------------------------------------
# 5-F Top Performers – GET /api/v1/scores/top-performers
# ---------------------------------------------------------------------------


@router.get("/scores/top-performers", response_model=List[TopPerformerOut])
def top_performers(*, db: Session = Depends(get_db), week: int = Query(None)) -> List[TopPerformerOut]:  # noqa: D401
    """Get top performing players for a given week or overall."""
    query = db.query(StatLine).join(Player)

    # Filter by week if provided
    if week is not None:
        # Simple week calculation - in a real app you'd have proper week boundaries
        query = query.filter(func.extract('week', StatLine.game_date) == week)

    # Get stat lines and calculate points
    stat_lines = query.all()

    # Group by player and sum points
    player_totals = {}
    for stat in stat_lines:
        if stat.player_id not in player_totals:
            player_totals[stat.player_id] = {'player': stat.player, 'total_points': 0.0, 'games_played': 0}
        player_totals[stat.player_id]['total_points'] += stat.points
        player_totals[stat.player_id]['games_played'] += 1

    # Convert to TopPerformerOut and sort
    performers = []
    for player_data in player_totals.values():
        performers.append(
            TopPerformerOut(
                player_id=player_data['player'].id,
                player_name=player_data['player'].full_name,
                position=player_data['player'].position,
                team_abbr=player_data['player'].team_abbr,
                total_points=round(player_data['total_points'], 2),
                games_played=player_data['games_played'],
                avg_points=round(player_data['total_points'] / max(player_data['games_played'], 1), 2),
            )
        )

    # Sort by total points descending and limit to top 50
    performers.sort(key=lambda p: p.total_points, reverse=True)
    return performers[:50]


# ---------------------------------------------------------------------------
# 5-G Score Trends – GET /api/v1/scores/trends
# ---------------------------------------------------------------------------


@router.get("/scores/trends", response_model=List[ScoreTrendOut])
def score_trends(*, db: Session = Depends(get_db), league_id: int = Query(None)) -> List[ScoreTrendOut]:  # noqa: D401
    """Get score trends over time for teams."""
    teams_query = db.query(Team)
    if league_id:
        teams_query = teams_query.filter(Team.league_id == league_id)
    teams = teams_query.all()

    result = []
    for team in teams:
        # Get scores by week
        weekly_scores = []
        cumulative_points = 0.0

        # Sort scores by week
        sorted_scores = sorted(team.scores, key=lambda s: s.week)

        for score in sorted_scores:
            cumulative_points += score.score
            weekly_scores.append(
                {
                    'week': score.week,
                    'weekly_score': round(score.score, 2),
                    'cumulative_score': round(cumulative_points, 2),
                }
            )

        result.append(
            ScoreTrendOut(
                team_id=team.id,
                team_name=team.name,
                weekly_scores=weekly_scores,
                total_points=round(cumulative_points, 2),
            )
        )

    # Sort by total points
    result.sort(key=lambda t: t.total_points, reverse=True)
    return result


# ---------------------------------------------------------------------------
# 5-H League Champion – GET /api/v1/scores/champion
# ---------------------------------------------------------------------------


@router.get("/scores/champion", response_model=LeagueChampionOut | None)
def league_champion(
    *, db: Session = Depends(get_db), league_id: int = Query(None)
) -> LeagueChampionOut | None:  # noqa: D401
    """Get the current league champion (team with highest season points)."""
    teams_query = db.query(Team)
    if league_id:
        teams_query = teams_query.filter(Team.league_id == league_id)
    teams = teams_query.all()

    if not teams:
        return None

    # Calculate season totals and find champion
    champion_team = None
    champion_points = 0.0

    for team in teams:
        season_points = sum(score.score for score in team.scores)
        if season_points > champion_points:
            champion_points = season_points
            champion_team = team

    if not champion_team:
        return None

    # Get champion's best week
    best_week_score = 0.0
    best_week = 0
    for score in champion_team.scores:
        if score.score > best_week_score:
            best_week_score = score.score
            best_week = score.week

    return LeagueChampionOut(
        team_id=champion_team.id,
        team_name=champion_team.name,
        total_points=round(champion_points, 2),
        best_week=best_week,
        best_week_score=round(best_week_score, 2),
        league_id=champion_team.league_id,
    )


# ---------------------------------------------------------------------------
# User's profile information
# ---------------------------------------------------------------------------


@router.get("/me", response_model=dict)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user's information."""
    return {"id": current_user.id, "email": current_user.email, "is_admin": current_user.is_admin}


# ---------------------------------------------------------------------------
# Roster management endpoints
# ---------------------------------------------------------------------------


@router_roster.get("/leagues/{league_id}/free-agents", response_model=List[PlayerOut])
def list_free_agents(
    league_id: int = Path(..., description="League ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get list of free agents (players not on any roster) in a league.
    """
    # Verify league exists
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get all free agents
    service = RosterService(db)
    free_agents = service.get_free_agents(league_id)

    return [PlayerOut.from_orm(player) for player in free_agents]


@router_roster.post("/teams/{team_id}/roster/add", response_model=TeamWithRosterSlotsOut)
def add_player(
    *,
    team_id: int = Path(..., description="Team ID"),
    data: AddPlayerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Add a free agent to a team's roster.
    """
    # Verify the team exists and belongs to the current user
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")

    # Add the player
    service = RosterService(db)
    try:
        service.add_player_to_team(
            team_id=team_id, player_id=data.player_id, set_as_starter=data.set_as_starter, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return the updated team details
    return team_detail(team_id=team_id, db=db)


@router_roster.post("/teams/{team_id}/roster/drop", response_model=TeamWithRosterSlotsOut)
def drop_player(
    *,
    team_id: int = Path(..., description="Team ID"),
    data: DropPlayerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Remove a player from a team's roster.
    """
    # Verify the team exists and belongs to the current user
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")

    # Drop the player
    service = RosterService(db)
    try:
        service.drop_player_from_team(team_id=team_id, player_id=data.player_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return the updated team details
    return team_detail(team_id=team_id, db=db)


@router_roster.put("/teams/{team_id}/roster/starters", response_model=TeamWithRosterSlotsOut)
def set_starters(
    *,
    team_id: int = Path(..., description="Team ID"),
    data: SetStartersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Set the starting lineup for a team.
    """
    # Verify the team exists and belongs to the current user
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")

    # Set the starters
    service = RosterService(db)
    try:
        service.set_starters(team_id=team_id, starter_player_ids=data.starter_player_ids, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return the updated team details
    return team_detail(team_id=team_id, db=db)


@router.options("/teams/{team_id}")
async def options_team(team_id: int):
    """Handle OPTIONS requests for team endpoints."""
    return {"allow": "PUT,OPTIONS"}


# ---------------------------------------------------------------------------
# 24-C Create Team – POST /api/v1/leagues/{league_id}/teams
# ---------------------------------------------------------------------------


@router.post("/leagues/{league_id}/teams", response_model=TeamOut, status_code=201)
def create_team(
    *,
    league_id: int = Path(..., description="League ID"),
    data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new team in a league for the authenticated user."""
    try:
        team = TeamService.create_team_in_league(db=db, name=data.name, league_id=league_id, owner_id=current_user.id)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "League not found" in detail else 409
        raise HTTPException(status_code=status_code, detail=detail)

    return map_team_to_out(team)


# ---------------------------------------------------------------------------
# 24-D Get User's Teams – GET /api/v1/users/me/teams
# ---------------------------------------------------------------------------


@router.get("/users/me/teams", response_model=List[TeamOut])
def list_my_teams(*, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teams = TeamService.get_teams_by_owner_id(db, owner_id=current_user.id)
    return [map_team_to_out(team) for team in teams]


# ---------------------------------------------------------------------------
# 24-E Get League's Teams – GET /api/v1/leagues/{league_id}/teams
# ---------------------------------------------------------------------------


@router.get("/leagues/{league_id}/teams", response_model=List[TeamOut])
def list_league_teams(*, league_id: int, db: Session = Depends(get_db)):
    # Validate league exists
    league_exists = db.query(League.id).filter(League.id == league_id).scalar() is not None
    if not league_exists:
        raise HTTPException(status_code=404, detail="League not found")

    teams = TeamService.get_teams_by_league_id(db, league_id=league_id)
    return [map_team_to_out(team) for team in teams]


# ---------------------------------------------------------------------------
# 24-F Update Team – PUT /api/v1/teams/{team_id}
# ---------------------------------------------------------------------------


@router.put("/teams/{team_id}", response_model=TeamOut)
def update_team(
    *,
    team_id: int = Path(..., description="Team ID"),
    data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        team = TeamService.update_team_details(db=db, team_id=team_id, owner_id=current_user.id, data=data)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return map_team_to_out(team)


@router.get("/leagues/{league_id}/draft/state", response_model=DraftStateResponse)
def get_league_draft_state(
    *, league_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get the current draft state for a league.
    """
    # Verify league exists
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get draft state for this league
    draft_state = db.query(DraftState).filter(DraftState.league_id == league_id).first()
    if not draft_state:
        raise HTTPException(status_code=404, detail="No draft found for this league")

    # Use DraftService to get formatted response
    draft_service = DraftService(db)
    return draft_service.get_draft_state(draft_state.id)


# ---------------------------------------------------------------------------
# Player Endpoints
# ---------------------------------------------------------------------------


@router.get("/players", response_model=Pagination[PlayerOut])
def list_players(
    *,
    limit: int = Query(100, ge=1, le=500, description="Number of players to return"),
    offset: int = Query(0, ge=0, description="Number of players to skip"),
    position: str = Query(None, description="Filter by position (e.g., 'G', 'F', 'C')"),
    team_abbr: str = Query(None, description="Filter by team abbreviation"),
    status: str = Query("active", description="Filter by status (active, injured, inactive)"),
    search: str = Query(None, description="Search by player name"),
    db: Session = Depends(get_db),
) -> Pagination[PlayerOut]:
    """List all players with optional filtering."""
    query = db.query(Player)

    # Apply filters
    if position:
        query = query.filter(Player.position == position)
    if team_abbr:
        query = query.filter(Player.team_abbr == team_abbr)
    if status:
        query = query.filter(Player.status == status)
    if search:
        query = query.filter(Player.full_name.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    players = query.order_by(Player.full_name).offset(offset).limit(limit).all()

    items = [PlayerOut.from_orm(player) for player in players]
    return Pagination[PlayerOut](total=total, limit=limit, offset=offset, items=items)


@router.get("/players/{player_id}", response_model=PlayerOut)
def get_player(*, player_id: int = Path(..., description="Player ID"), db: Session = Depends(get_db)) -> PlayerOut:
    """Get detailed player profile by ID."""
    player = db.query(Player).filter_by(id=player_id).one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return PlayerOut.from_orm(player)


# ---------------------------------------------------------------------------
# Weekly Lineup Endpoints
# ---------------------------------------------------------------------------


@router.get("/teams/{team_id}/lineups/{week_id}", response_model=WeeklyLineupOut)
def get_weekly_lineup(
    *,
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyLineupOut:
    """Get lineup for a specific team and week."""
    # Verify team ownership
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")

    lineup_service = LineupService(db)

    lineup_data = lineup_service.get_weekly_lineup(team_id, week_id)
    if lineup_data is None:
        raise HTTPException(status_code=404, detail="Lineup not found for this week")

    # Convert to schema format
    lineup_players = []
    for player_data in lineup_data:
        lineup_players.append(
            WeeklyLineupPlayerOut(
                player_id=player_data["player_id"],
                player_name=player_data["player_name"],
                position=player_data["position"],
                team_abbr=player_data["team_abbr"],
                is_starter=player_data["is_starter"],
                locked=player_data["locked"],
                locked_at=player_data.get("locked_at"),
            )
        )

    current_week_id = lineup_service.get_current_week_id()
    return WeeklyLineupOut(week_id=week_id, lineup=lineup_players, is_current=week_id == current_week_id)


@router.get("/teams/{team_id}/lineups/history", response_model=LineupHistoryOut)
def get_lineup_history(
    *,
    team_id: int = Path(..., description="Team ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LineupHistoryOut:
    """Get all historical lineups for a team."""
    # Verify team ownership
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")

    lineup_service = LineupService(db)

    history_data = lineup_service.get_lineup_history(team_id)

    # Convert to schema format
    history = []
    for week_data in history_data:
        lineup_players = []
        for player_data in week_data["lineup"]:
            lineup_players.append(
                WeeklyLineupPlayerOut(
                    player_id=player_data["player_id"],
                    player_name=player_data["player_name"],
                    position=player_data["position"],
                    team_abbr=player_data["team_abbr"],
                    is_starter=player_data["is_starter"],
                    locked=player_data["locked"],
                    locked_at=player_data.get("locked_at"),
                )
            )

        history.append(
            WeeklyLineupOut(week_id=week_data["week_id"], lineup=lineup_players, is_current=week_data["is_current"])
        )

    return LineupHistoryOut(history=history)


@router.put("/teams/{team_id}/lineups/{week_id}/starters", response_model=WeeklyLineupOut)
def set_weekly_starters(
    *,
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    data: SetWeeklyStartersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyLineupOut:
    """Set starters for a specific week."""
    # Verify team ownership
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or access denied")

    lineup_service = LineupService(db)

    # Check if lineup can be modified
    if not lineup_service.can_modify_lineup(team_id, week_id):
        raise HTTPException(status_code=400, detail="Lineup is locked and cannot be modified")

    # Set the starters
    success = lineup_service.set_weekly_starters(team_id, week_id, data.starter_player_ids)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set starters")

    # Return the updated lineup
    return get_weekly_lineup(team_id=team_id, week_id=week_id, db=db, current_user=current_user)


@router.post("/admin/lineups/lock/{week_id}", response_model=LineupLockResponse)
def lock_weekly_lineups(
    *,
    week_id: int = Path(..., description="Week ID to lock"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LineupLockResponse:
    """Lock lineups for a specific week (admin only)."""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    lineup_service = LineupService(db)

    teams_processed = lineup_service.lock_weekly_lineups(week_id)

    return LineupLockResponse(week_id=week_id, teams_processed=teams_processed, locked_at=datetime.now(timezone.utc))


# Add the router to the API
router.include_router(router_roster, prefix="")
