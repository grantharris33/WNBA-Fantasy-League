"""API endpoints for quick lookups of teams and players by ID."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Player, WNBATeam

router = APIRouter(prefix="/api/v1/lookup", tags=["lookup"])


@router.get("/teams", response_model=Dict[int, Dict])
async def lookup_teams(
    team_ids: Optional[str] = Query(None, description="Comma-separated team IDs"), db: Session = Depends(get_db)
) -> Dict[int, Dict]:
    """
    Get team name and abbreviation lookup for team IDs.
    If no team_ids provided, returns all teams.
    """
    query = db.query(WNBATeam)

    if team_ids:
        try:
            id_list = [int(id.strip()) for id in team_ids.split(",")]
            query = query.filter(WNBATeam.id.in_(id_list))
        except ValueError:
            return {}

    teams = query.all()

    return {
        team.id: {
            "id": team.id,
            "name": team.display_name,
            "abbreviation": team.abbreviation,
            "location": team.location,
            "logo_url": team.logo_url,
        }
        for team in teams
    }


@router.get("/players", response_model=Dict[int, Dict])
async def lookup_players(
    player_ids: Optional[str] = Query(None, description="Comma-separated player IDs"), db: Session = Depends(get_db)
) -> Dict[int, Dict]:
    """
    Get player name and team lookup for player IDs.
    If no player_ids provided, returns first 100 players.
    """
    query = db.query(Player).join(WNBATeam, Player.wnba_team_id == WNBATeam.id, isouter=True)

    if player_ids:
        try:
            id_list = [int(id.strip()) for id in player_ids.split(",")]
            query = query.filter(Player.id.in_(id_list))
        except ValueError:
            return {}
    else:
        query = query.limit(100)  # Limit to avoid massive responses

    players = query.all()

    return {
        player.id: {
            "id": player.id,
            "full_name": player.full_name,
            "position": player.position,
            "jersey_number": player.jersey_number,
            "team_id": player.wnba_team_id,
            "team_name": player.wnba_team.display_name if player.wnba_team else None,
            "team_abbreviation": player.wnba_team.abbreviation if player.wnba_team else None,
            "headshot_url": player.headshot_url,
        }
        for player in players
    }


@router.get("/batch", response_model=Dict)
async def batch_lookup(
    team_ids: Optional[str] = Query(None, description="Comma-separated team IDs"),
    player_ids: Optional[str] = Query(None, description="Comma-separated player IDs"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Batch lookup for both teams and players in a single request.
    Returns both teams and players dictionaries.
    """
    result = {"teams": {}, "players": {}}

    # Get teams
    if team_ids:
        try:
            team_id_list = [int(id.strip()) for id in team_ids.split(",")]
            teams = db.query(WNBATeam).filter(WNBATeam.id.in_(team_id_list)).all()
            result["teams"] = {
                team.id: {
                    "id": team.id,
                    "name": team.display_name,
                    "abbreviation": team.abbreviation,
                    "location": team.location,
                    "logo_url": team.logo_url,
                }
                for team in teams
            }
        except ValueError:
            pass

    # Get players
    if player_ids:
        try:
            player_id_list = [int(id.strip()) for id in player_ids.split(",")]
            players = (
                db.query(Player)
                .join(WNBATeam, Player.wnba_team_id == WNBATeam.id, isouter=True)
                .filter(Player.id.in_(player_id_list))
                .all()
            )
            result["players"] = {
                player.id: {
                    "id": player.id,
                    "full_name": player.full_name,
                    "position": player.position,
                    "jersey_number": player.jersey_number,
                    "team_id": player.wnba_team_id,
                    "team_name": player.wnba_team.display_name if player.wnba_team else None,
                    "team_abbreviation": player.wnba_team.abbreviation if player.wnba_team else None,
                    "headshot_url": player.headshot_url,
                }
                for player in players
            }
        except ValueError:
            pass

    return result
