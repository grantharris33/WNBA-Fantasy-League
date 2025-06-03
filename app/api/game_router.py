from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException, Path, Depends
from sqlalchemy.orm import Session

from app.api.schemas import (
    GamePlayByPlayOut,
    GameSummaryBoxScoreTeamOut,
    GameSummaryOut,
    GameSummaryPlayerStatsOut,
    GameInfoOut,
    PlayByPlayEventOut,
    ComprehensiveGameStatsOut,
    ComprehensivePlayerStatsOut,
    GameOut,
)
from app.api.deps import get_db
from app import models
from app.external_apis.rapidapi_client import RapidApiClient, RetryError, wnba_client

router = APIRouter(prefix="/games", tags=["games"])


def _safe_int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _map_game_summary(data: dict[str, Any]) -> GameSummaryOut:
    competition = (data.get("header", {}).get("competitions") or [{}])[0]
    game_id = str(competition.get("id") or data.get("gameId", ""))

    game_info = GameInfoOut(
        game_id=game_id,
        venue=competition.get("venue", {}).get("fullName"),
        status=competition.get("status", {}).get("type", {}).get("description"),
    )

    competitor_meta = {}
    for comp in competition.get("competitors", []):
        tid = str(comp.get("id") or comp.get("team", {}).get("id", ""))
        competitor_meta[tid] = {
            "abbr": comp.get("team", {}).get("abbreviation"),
            "score": _safe_int(comp.get("score")),
        }

    teams: List[GameSummaryBoxScoreTeamOut] = []
    for team_block in data.get("boxscore", {}).get("players", []):
        team = team_block.get("team", {})
        team_id = str(team.get("id", ""))
        players: List[GameSummaryPlayerStatsOut] = []
        for stats_block in team_block.get("statistics", []):
            for athlete in stats_block.get("athletes", []):
                info = athlete.get("athlete", {})
                stats = athlete.get("stats", [])
                players.append(
                    GameSummaryPlayerStatsOut(
                        player_id=str(info.get("id")),
                        player_name=info.get("displayName"),
                        points=_safe_int(stats[-1]) if stats else 0,
                        rebounds=_safe_int(stats[6]) if len(stats) > 6 else 0,
                        assists=_safe_int(stats[7]) if len(stats) > 7 else 0,
                    )
                )
        meta = competitor_meta.get(team_id, {})
        teams.append(
            GameSummaryBoxScoreTeamOut(
                team_id=team_id,
                team_abbr=meta.get("abbr"),
                score=meta.get("score", 0),
                players=players,
            )
        )

    return GameSummaryOut(game=game_info, teams=teams)


def _map_playbyplay(data: dict[str, Any]) -> GamePlayByPlayOut:
    competition = (data.get("header", {}).get("competitions") or [{}])[0]
    game_id = str(competition.get("id") or data.get("gameId", ""))
    events: List[PlayByPlayEventOut] = []
    for play in data.get("plays", []):
        events.append(
            PlayByPlayEventOut(
                clock=play.get("clock", {}).get("displayValue"),
                description=play.get("text"),
                team_id=str(play.get("team", {}).get("id")) if play.get("team") else None,
                period=play.get("period", {}).get("number"),
            )
        )
    return GamePlayByPlayOut(game_id=game_id, events=events)


@router.get("/{game_id}/summary", response_model=GameSummaryOut)
async def game_summary(game_id: str = Path(..., description="Game ID")) -> GameSummaryOut:
    """Return a game summary including box scores."""

    try:
        raw = await wnba_client.fetch_game_summary(game_id)
    except RetryError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail="Failed to fetch game summary") from exc
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network errors
        status = 404 if exc.response.status_code == 404 else 502
        raise HTTPException(status_code=status, detail="Failed to fetch game summary") from exc

    if not raw:
        raise HTTPException(status_code=404, detail="Game not found")

    return _map_game_summary(raw)


@router.get("/{game_id}/playbyplay", response_model=GamePlayByPlayOut)
async def game_playbyplay(game_id: str = Path(..., description="Game ID")) -> GamePlayByPlayOut:
    """Return play-by-play data for a game."""

    try:
        raw = await wnba_client.fetch_game_playbyplay(game_id)
    except RetryError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail="Failed to fetch play-by-play") from exc
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network errors
        status = 404 if exc.response.status_code == 404 else 502
        raise HTTPException(status_code=status, detail="Failed to fetch play-by-play") from exc

    if not raw:
        raise HTTPException(status_code=404, detail="Game not found")

    return _map_playbyplay(raw)


@router.get("/{game_id}/enhanced", response_model=Dict)
async def get_enhanced_game_view(
    game_id: str = Path(..., description="Game ID"),
    db: Session = Depends(get_db)
) -> Dict:
    """Get enhanced game view with team names, player names, and additional context."""

    # Get game record
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get team information
    home_team = db.query(models.WNBATeam).filter(models.WNBATeam.id == game.home_team_id).first() if game.home_team_id else None
    away_team = db.query(models.WNBATeam).filter(models.WNBATeam.id == game.away_team_id).first() if game.away_team_id else None

    # Get all stat lines for this game with player and team info
    stat_lines = (
        db.query(models.StatLine)
        .filter(models.StatLine.game_id == game_id)
        .join(models.Player)
        .outerjoin(models.WNBATeam, models.Player.wnba_team_id == models.WNBATeam.id)
        .all()
    )

    # Group players by team
    home_players = []
    away_players = []

    for stat_line in stat_lines:
        player_data = {
            "player_id": stat_line.player_id,
            "player_name": stat_line.player.full_name,
            "jersey_number": stat_line.player.jersey_number,
            "position": stat_line.player.position,
            "is_starter": stat_line.is_starter,
            "did_not_play": stat_line.did_not_play,
            "minutes_played": stat_line.minutes_played,
            "points": stat_line.points,
            "rebounds": stat_line.rebounds,
            "assists": stat_line.assists,
            "steals": stat_line.steals,
            "blocks": stat_line.blocks,
            "turnovers": stat_line.turnovers,
            "personal_fouls": stat_line.personal_fouls,
            "field_goals_made": stat_line.field_goals_made,
            "field_goals_attempted": stat_line.field_goals_attempted,
            "field_goal_percentage": stat_line.field_goal_percentage,
            "three_pointers_made": stat_line.three_pointers_made,
            "three_pointers_attempted": stat_line.three_pointers_attempted,
            "three_point_percentage": stat_line.three_point_percentage,
            "free_throws_made": stat_line.free_throws_made,
            "free_throws_attempted": stat_line.free_throws_attempted,
            "free_throw_percentage": stat_line.free_throw_percentage,
            "plus_minus": stat_line.plus_minus,
        }

        if stat_line.is_home_game:
            home_players.append(player_data)
        else:
            away_players.append(player_data)

    # Calculate team totals
    def calculate_team_totals(players):
        if not players:
            return {}

        totals = {
            "points": sum(p["points"] for p in players),
            "rebounds": sum(p["rebounds"] for p in players),
            "assists": sum(p["assists"] for p in players),
            "steals": sum(p["steals"] for p in players),
            "blocks": sum(p["blocks"] for p in players),
            "turnovers": sum(p["turnovers"] for p in players),
            "field_goals_made": sum(p["field_goals_made"] for p in players),
            "field_goals_attempted": sum(p["field_goals_attempted"] for p in players),
            "three_pointers_made": sum(p["three_pointers_made"] for p in players),
            "three_pointers_attempted": sum(p["three_pointers_attempted"] for p in players),
            "free_throws_made": sum(p["free_throws_made"] for p in players),
            "free_throws_attempted": sum(p["free_throws_attempted"] for p in players),
        }

        # Calculate percentages
        totals["field_goal_percentage"] = (
            totals["field_goals_made"] / totals["field_goals_attempted"] * 100
            if totals["field_goals_attempted"] > 0 else 0
        )
        totals["three_point_percentage"] = (
            totals["three_pointers_made"] / totals["three_pointers_attempted"] * 100
            if totals["three_pointers_attempted"] > 0 else 0
        )
        totals["free_throw_percentage"] = (
            totals["free_throws_made"] / totals["free_throws_attempted"] * 100
            if totals["free_throws_attempted"] > 0 else 0
        )

        return totals

    home_totals = calculate_team_totals(home_players)
    away_totals = calculate_team_totals(away_players)

    return {
        "game": {
            "id": game.id,
            "date": game.date,
            "status": game.status,
            "venue": game.venue,
            "attendance": game.attendance,
        },
        "home_team": {
            "id": game.home_team_id,
            "name": home_team.display_name if home_team else "Unknown",
            "abbreviation": home_team.abbreviation if home_team else "UNK",
            "score": game.home_score,
            "logo_url": home_team.logo_url if home_team else None,
            "players": sorted(home_players, key=lambda x: (not x["is_starter"], x["player_name"])),
            "totals": home_totals
        },
        "away_team": {
            "id": game.away_team_id,
            "name": away_team.display_name if away_team else "Unknown",
            "abbreviation": away_team.abbreviation if away_team else "UNK",
            "score": game.away_score,
            "logo_url": away_team.logo_url if away_team else None,
            "players": sorted(away_players, key=lambda x: (not x["is_starter"], x["player_name"])),
            "totals": away_totals
        },
        "game_leaders": {
            "points": max(stat_lines, key=lambda x: x.points, default=None),
            "rebounds": max(stat_lines, key=lambda x: x.rebounds, default=None),
            "assists": max(stat_lines, key=lambda x: x.assists, default=None),
        } if stat_lines else {}
    }


@router.get("/{game_id}/comprehensive-stats", response_model=ComprehensiveGameStatsOut)
async def get_comprehensive_game_stats(
    game_id: str = Path(..., description="Game ID"),
    db: Session = Depends(get_db)
) -> ComprehensiveGameStatsOut:
    """Get comprehensive statistics for a game from our database."""

    # Get game record
    game = db.get(models.Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get all stat lines for this game
    stat_lines = (
        db.query(models.StatLine)
        .filter(models.StatLine.game_id == game_id)
        .join(models.Player)
        .all()
    )

    # Convert to response format
    player_stats = []
    for stat_line in stat_lines:
        player_stats.append(
            ComprehensivePlayerStatsOut(
                player_id=stat_line.player_id,
                player_name=stat_line.player.full_name,
                position=stat_line.player.position,
                is_starter=stat_line.is_starter,
                did_not_play=stat_line.did_not_play,
                points=stat_line.points,
                rebounds=stat_line.rebounds,
                assists=stat_line.assists,
                steals=stat_line.steals,
                blocks=stat_line.blocks,
                minutes_played=stat_line.minutes_played,
                field_goals_made=stat_line.field_goals_made,
                field_goals_attempted=stat_line.field_goals_attempted,
                field_goal_percentage=stat_line.field_goal_percentage,
                three_pointers_made=stat_line.three_pointers_made,
                three_pointers_attempted=stat_line.three_pointers_attempted,
                three_point_percentage=stat_line.three_point_percentage,
                free_throws_made=stat_line.free_throws_made,
                free_throws_attempted=stat_line.free_throws_attempted,
                free_throw_percentage=stat_line.free_throw_percentage,
                offensive_rebounds=stat_line.offensive_rebounds,
                defensive_rebounds=stat_line.defensive_rebounds,
                turnovers=stat_line.turnovers,
                personal_fouls=stat_line.personal_fouls,
                plus_minus=stat_line.plus_minus,
                team_id=stat_line.team_id,
                opponent_id=stat_line.opponent_id,
                is_home_game=stat_line.is_home_game,
            )
        )

    game_out = GameOut(
        id=game.id,
        date=game.date,
        home_team_id=game.home_team_id,
        away_team_id=game.away_team_id,
        home_score=game.home_score,
        away_score=game.away_score,
        status=game.status,
        venue=game.venue,
        attendance=game.attendance,
    )

    return ComprehensiveGameStatsOut(
        game=game_out,
        player_stats=player_stats
    )

