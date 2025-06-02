"""League management endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas import (
    InviteCodeResponse,
    JoinLeagueRequest,
    LeagueCreate,
    LeagueOut,
    LeagueUpdate,
    LeagueWithRole,
    TeamOut,
)
from app.models import TransactionLog, User
from app.services.league import LeagueService
from app.services.team import map_team_to_out

router = APIRouter(prefix="/api/v1/leagues", tags=["league-management"])


def log_transaction(db: Session, user: User, action: str, path: str, method: str) -> None:
    """Log a transaction for audit purposes."""
    transaction = TransactionLog(
        user_id=user.id,
        action=action,
        path=path,
        method=method,
    )
    db.add(transaction)
    db.commit()


@router.options("/{league_id}")
async def options_league(league_id: int):
    """Handle OPTIONS requests for league endpoints."""
    return {"allow": "GET,PUT,DELETE,OPTIONS"}


@router.options("/{league_id}/teams/{team_id}")
async def options_league_team(league_id: int, team_id: int):
    """Handle OPTIONS requests for team removal endpoints."""
    return {"allow": "DELETE,OPTIONS"}


@router.post("", response_model=LeagueOut, status_code=status.HTTP_201_CREATED)
def create_league(
    *,
    data: LeagueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeagueOut:
    """
    Create a new league with the requesting user as commissioner.
    """
    service = LeagueService(db)
    league = service.create_league(
        name=data.name,
        commissioner=current_user,
        max_teams=data.max_teams,
        draft_date=data.draft_date,
        settings=data.settings,
    )

    # Log transaction
    log_transaction(db, current_user, "CREATE_LEAGUE", "/api/v1/leagues", "POST")

    # Include invite code since user is commissioner
    league_out = LeagueOut.from_orm(league)
    league_out.invite_code = league.invite_code
    return league_out


@router.put("/{league_id}", response_model=LeagueOut)
def update_league(
    *,
    league_id: int = Path(..., description="League ID"),
    data: LeagueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeagueOut:
    """
    Update league settings. Only commissioner can update.
    """
    service = LeagueService(db)
    league = service.update_league(
        league_id=league_id,
        user=current_user,
        name=data.name,
        max_teams=data.max_teams,
        draft_date=data.draft_date,
        settings=data.settings,
    )

    # Log transaction
    log_transaction(db, current_user, "UPDATE_LEAGUE", f"/api/v1/leagues/{league_id}", "PUT")

    # Include invite code since user is commissioner
    league_out = LeagueOut.from_orm(league)
    league_out.invite_code = league.invite_code
    return league_out


@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_league(
    *,
    league_id: int = Path(..., description="League ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a league. Only commissioner can delete and only if draft hasn't started.
    """
    service = LeagueService(db)
    service.delete_league(league_id=league_id, user=current_user)

    # Log transaction
    log_transaction(db, current_user, "DELETE_LEAGUE", f"/api/v1/leagues/{league_id}", "DELETE")


@router.post("/join", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def join_league(
    *,
    data: JoinLeagueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamOut:
    """
    Join a league using invite code and create a team.
    """
    service = LeagueService(db)
    team = service.join_league(
        invite_code=data.invite_code,
        team_name=data.team_name,
        user=current_user,
    )

    # Log transaction
    log_transaction(db, current_user, "JOIN_LEAGUE", "/api/v1/leagues/join", "POST")

    return map_team_to_out(team)


@router.get("/mine", response_model=List[LeagueWithRole])
def get_my_leagues(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[LeagueWithRole]:
    """
    Get all leagues where user has a team or is commissioner.
    """
    service = LeagueService(db)
    user_leagues = service.get_user_leagues(user=current_user)

    result = []
    for item in user_leagues:
        league_out = LeagueOut.from_orm(item["league"])

        # Include invite code only if user is commissioner
        if item["role"] == "commissioner":
            league_out.invite_code = item["league"].invite_code
        else:
            league_out.invite_code = None

        result.append(LeagueWithRole(league=league_out, role=item["role"]))

    return result


@router.get("/{league_id}", response_model=LeagueOut)
def get_league_details(
    *,
    league_id: int = Path(..., description="League ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeagueOut:
    """
    Get league details. Include invite_code only if user is commissioner.
    """
    service = LeagueService(db)
    league = service.get_league_details(league_id=league_id, user=current_user)

    league_out = LeagueOut.from_orm(league)

    # Include invite code only if user is commissioner
    if league.commissioner_id == current_user.id:
        league_out.invite_code = league.invite_code
    else:
        league_out.invite_code = None

    return league_out


@router.delete("/{league_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def leave_league(
    *,
    league_id: int = Path(..., description="League ID"),
    team_id: int = Path(..., description="Team ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a team from a league. User can remove their own team, commissioner can remove any team.
    """
    service = LeagueService(db)

    # Get the team to determine if it's the user's own team
    from app.models import Team
    team = db.query(Team).filter(Team.id == team_id, Team.league_id == league_id).first()

    service.leave_league(league_id=league_id, team_id=team_id, user=current_user)

    # Log transaction - determine if it's leave or kick
    action = "LEAVE_LEAGUE" if team and team.owner_id == current_user.id else "KICK_TEAM"
    log_transaction(db, current_user, action, f"/api/v1/leagues/{league_id}/teams/{team_id}", "DELETE")


@router.post("/{league_id}/invite-code", response_model=InviteCodeResponse)
def generate_new_invite_code(
    *,
    league_id: int = Path(..., description="League ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InviteCodeResponse:
    """
    Generate a new invite code for the league. Commissioner only.
    """
    service = LeagueService(db)
    new_invite_code = service.generate_new_invite_code(league_id=league_id, user=current_user)

    # Log transaction
    log_transaction(db, current_user, "GENERATE_INVITE_CODE", f"/api/v1/leagues/{league_id}/invite-code", "POST")

    return InviteCodeResponse(invite_code=new_invite_code)