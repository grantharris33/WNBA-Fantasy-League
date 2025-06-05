from __future__ import annotations

import datetime as dt
from typing import Any, List

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.external_apis.rapidapi_client import RetryError, wnba_client

from .schemas import (
    LeagueInjuryReportOut,
    NewsArticleOut,
    PlayerInjuryDetailOut,
    ScheduleDayOut,
    ScheduledGameCompetitorOut,
    ScheduledGameOut,
    TeamInjuryListOut,
)

router = APIRouter(tags=["league"])


def _safe_int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _map_schedule(games: List[dict[str, Any]], date_str: str) -> ScheduleDayOut:
    mapped_games: List[ScheduledGameOut] = []
    for game in games:
        competitors: List[ScheduledGameCompetitorOut] = []
        for comp in game.get("competitors", game.get("teams", [])):
            competitors.append(
                ScheduledGameCompetitorOut(
                    team_id=str(comp.get("id")),
                    abbrev=comp.get("abbrev"),
                    display_name=comp.get("displayName"),
                    score=_safe_int(comp.get("score")),
                    is_home=comp.get("isHome"),
                    winner=comp.get("winner"),
                )
            )
        mapped_games.append(
            ScheduledGameOut(
                game_id=str(game.get("id")),
                start_time=game.get("date"),
                venue=game.get("venue", {}).get("fullName"),
                completed=game.get("completed"),
                competitors=competitors,
            )
        )
    return ScheduleDayOut(date=date_str, games=mapped_games)


def _map_news(raw: dict[str, Any] | list[dict[str, Any]]) -> List[NewsArticleOut]:
    articles: List[NewsArticleOut] = []
    # Handle case where raw is already a list of articles
    if isinstance(raw, list):
        items = raw
    else:
        # Handle case where raw is a dict with articles or data key
        items = raw.get("articles", raw.get("data", []))

    for item in items:
        link_val = item.get("link")
        if isinstance(link_val, dict):
            link_val = link_val.get("href")
        articles.append(
            NewsArticleOut(
                headline=item.get("headline"), link=link_val, source=item.get("source"), published=item.get("published")
            )
        )
    return articles


def _map_injuries(raw: dict[str, Any]) -> LeagueInjuryReportOut:
    teams: List[TeamInjuryListOut] = []

    # Handle new API structure where data is under "injuries" key
    injury_data = raw.get("injuries", raw.get("teams", []))

    for team in injury_data:
        players: List[PlayerInjuryDetailOut] = []
        for injury in team.get("injuries", []):
            # Extract player info from athlete object
            athlete = injury.get("athlete", {})
            player_id = str(athlete.get("id") or injury.get("id", ""))
            player_name = athlete.get("displayName") or athlete.get("firstName", "") + " " + athlete.get("lastName", "")
            position = athlete.get("position", {}).get("abbreviation")

            # Get injury details
            status = injury.get("status", "Unknown")
            comment = (
                injury.get("shortComment") or injury.get("longComment") or injury.get("details", {}).get("type", "")
            )

            players.append(
                PlayerInjuryDetailOut(
                    player_id=player_id,
                    player_name=player_name.strip(),
                    position=position,
                    status=status,
                    comment=comment,
                )
            )

        team_id = str(team.get("id", ""))
        team_name = team.get("displayName") or team.get("name", "")

        teams.append(TeamInjuryListOut(team_id=team_id, team_name=team_name, players=players))

    return LeagueInjuryReportOut(teams=teams)


@router.get("/schedule", response_model=ScheduleDayOut)
async def get_schedule(date: str | None = Query(None, description="YYYY-MM-DD")) -> ScheduleDayOut:
    if date:
        try:
            date_obj = dt.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format – use YYYY-MM-DD")
    else:
        date_obj = dt.datetime.utcnow().date()

    try:
        games = await wnba_client.fetch_schedule(
            date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")
        )
    except RetryError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail="Failed to fetch schedule") from exc
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network errors
        status = 404 if exc.response.status_code == 404 else 502
        raise HTTPException(status_code=status, detail="Failed to fetch schedule") from exc

    return _map_schedule(games, date_obj.isoformat())


@router.get("/news", response_model=List[NewsArticleOut])
async def get_news(limit: int = Query(20, ge=1, le=100)) -> List[NewsArticleOut]:
    try:
        raw = await wnba_client.fetch_wnba_news(limit)
    except RetryError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail="Failed to fetch news") from exc
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network errors
        status = 404 if exc.response.status_code == 404 else 502
        raise HTTPException(status_code=status, detail="Failed to fetch news") from exc

    return _map_news(raw)


@router.get("/injuries", response_model=LeagueInjuryReportOut)
async def get_injuries() -> LeagueInjuryReportOut:
    try:
        raw = await wnba_client.fetch_league_injuries()
    except RetryError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=502, detail="Failed to fetch injuries") from exc
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network errors
        status = 404 if exc.response.status_code == 404 else 502
        raise HTTPException(status_code=status, detail="Failed to fetch injuries") from exc

    return _map_injuries(raw)
