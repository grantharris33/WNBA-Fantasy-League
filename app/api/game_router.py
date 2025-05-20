from __future__ import annotations

from typing import Any, List

import httpx
from fastapi import APIRouter, HTTPException, Path

from app.api.schemas import (
    GamePlayByPlayOut,
    GameSummaryBoxScoreTeamOut,
    GameSummaryOut,
    GameSummaryPlayerStatsOut,
    GameInfoOut,
    PlayByPlayEventOut,
)
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

