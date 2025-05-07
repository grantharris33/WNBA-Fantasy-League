from __future__ import annotations

from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.database import SessionLocal
from app.models import League, Player, Team, TeamScore, User, WeeklyBonus
from app.services.roster import RosterService
from app.services.team import TeamService, map_team_to_out
from app.api.schemas import TeamCreate, TeamUpdate

from .schemas import (
    AddPlayerRequest,
    BonusOut,
    DropPlayerRequest,
    LeagueOut,
    Pagination,
    PlayerOut,
    ScoreOut,
    SetStartersRequest,
    TeamOut,
)

router = APIRouter(prefix="/api/v1", tags=["public"])

# Create Roster Management router
router_roster = APIRouter(tags=["roster"])


# ---------------------------------------------------------------------------
# Dependency: provide DB session per request
# ---------------------------------------------------------------------------


def _get_db() -> Session:  # noqa: D401
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 5-B List Leagues – GET /api/v1/leagues
# ---------------------------------------------------------------------------


@router.get("/leagues", response_model=Pagination[LeagueOut])
def list_leagues(  # noqa: D401
    *, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(_get_db)
):
    total = db.query(League).count()
    leagues = db.query(League).order_by(League.id).offset(offset).limit(limit).all()  # deterministic ordering

    items = [LeagueOut.from_orm(league) for league in leagues]
    return Pagination[LeagueOut](total=total, limit=limit, offset=offset, items=items)


# ---------------------------------------------------------------------------
# 5-C Team Detail – GET /api/v1/teams/{team_id}
# ---------------------------------------------------------------------------


@router.get("/teams/{team_id}", response_model=TeamOut)
def team_detail(*, team_id: int, db: Session = Depends(_get_db)):  # noqa: D401
    team = db.query(Team).filter_by(id=team_id).one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Roster list
    roster_players: List[PlayerOut] = [PlayerOut.from_orm(rs.player) for rs in team.roster_slots]

    # Season points = sum of all weekly scores
    season_points = sum(score.score for score in team.scores)

    return TeamOut(
        id=team.id,
        name=team.name,
        league_id=team.league_id,
        owner_id=team.owner_id,
        moves_this_week=team.moves_this_week,
        roster=roster_players,
        season_points=round(season_points, 2),
    )


# ---------------------------------------------------------------------------
# 5-D Current Scores – GET /api/v1/scores/current
# ---------------------------------------------------------------------------


@router.get("/scores/current", response_model=List[ScoreOut])
def current_scores(*, db: Session = Depends(_get_db)) -> List[ScoreOut]:  # noqa: D401
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
    return result


@router.get("/me", response_model=dict)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Test endpoint to verify the current user authentication
    """
    return {"id": current_user.id, "email": current_user.email}


@router_roster.get("/leagues/{league_id}/free-agents", response_model=Pagination[PlayerOut])
def list_free_agents(
    league_id: int = Path(..., description="League ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List players not currently on any team in the specified league.
    """
    # Verify league exists
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get free agents
    service = RosterService(db)
    players = service.get_free_agents(league_id, page, limit)

    # Calculate total for pagination
    total = len(service.get_free_agents(league_id, 1, 10000))  # Approximate count of all free agents

    return Pagination[PlayerOut](total=total, limit=limit, offset=(page - 1) * limit, items=players)


@router_roster.post("/teams/{team_id}/roster/add", response_model=TeamOut)
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


@router_roster.post("/teams/{team_id}/roster/drop", response_model=TeamOut)
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


@router_roster.put("/teams/{team_id}/roster/starters", response_model=TeamOut)
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


# ---------------------------------------------------------------------------
# 24-C Create Team – POST /api/v1/leagues/{league_id}/teams
# ---------------------------------------------------------------------------


@router.post(
    "/leagues/{league_id}/teams",
    response_model=TeamOut,
    status_code=201,
)
def create_team(
    *,
    league_id: int = Path(..., description="League ID"),
    data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new team in a league for the authenticated user."""
    try:
        team = TeamService.create_team_in_league(
            db=db, name=data.name, league_id=league_id, owner_id=current_user.id
        )
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


# Add the router to the API
router.include_router(router_roster, prefix="")
