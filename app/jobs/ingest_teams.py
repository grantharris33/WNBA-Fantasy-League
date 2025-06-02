"""
WNBA Teams Ingestion Job

This module handles the ingestion of WNBA team information from the RapidAPI.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import httpx

try:
    from tenacity import RetryError  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # Provide minimal no-op fallback so that code can run without tenacity in CI
    import functools

    def retry(*dargs, **dkwargs):  # type: ignore
        max_attempts = 3

        def decorator(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                attempts = 0
                while True:
                    try:
                        return await fn(*args, **kwargs)
                    except Exception as exc:  # noqa: BLE001
                        attempts += 1
                        if attempts >= max_attempts:
                            raise RetryError(str(exc)) from exc
                        # No sleep to keep tests fast

            return wrapper

        return decorator

    def stop_after_attempt(*args, **kwargs):  # type: ignore
        return None

    def wait_exponential(*args, **kwargs):  # type: ignore
        return None

    class RetryError(Exception):
        pass


from app import models
from app.core.database import SessionLocal
from app.external_apis.rapidapi_client import wnba_client, RapidApiError, RateLimitError, ApiKeyError, RetryableError
from app.models import IngestLog


def _upsert_wnba_team(session, team_data: dict[str, Any]) -> models.WNBATeam:
    """Create or update a WNBA team record."""
    team_id = int(team_data.get("teamId", team_data.get("id", 0)))
    if team_id == 0:
        raise ValueError("No team ID found in team data")

    team = session.get(models.WNBATeam, team_id)

    # Extract team name and location from displayName
    display_name = team_data.get("displayName", "")
    short_name = team_data.get("shortDisplayName", "")

    # Try to split display name into location and name
    # e.g., "Atlanta Dream" -> location="Atlanta", name="Dream"
    name_parts = display_name.split()
    if len(name_parts) >= 2:
        location = " ".join(name_parts[:-1])
        name = name_parts[-1]
    else:
        location = ""
        name = display_name

    if team is None:
        team = models.WNBATeam(
            id=team_id,
            name=name,
            location=location,
            abbreviation=team_data.get("abbreviation", ""),
            display_name=display_name,
            color=team_data.get("color"),
            alternate_color=team_data.get("alternateColor"),
            logo_url=team_data.get("logo"),
            venue_name=team_data.get("venue", {}).get("name") if team_data.get("venue") else None,
            venue_city=team_data.get("venue", {}).get("city") if team_data.get("venue") else None,
            venue_state=team_data.get("venue", {}).get("state") if team_data.get("venue") else None,
        )
        session.add(team)
    else:
        # Update existing team with new information
        team.name = name
        team.location = location
        team.abbreviation = team_data.get("abbreviation", team.abbreviation)
        team.display_name = display_name
        team.color = team_data.get("color", team.color)
        team.alternate_color = team_data.get("alternateColor", team.alternate_color)
        team.logo_url = team_data.get("logo", team.logo_url)

        if team_data.get("venue"):
            venue = team_data["venue"]
            team.venue_name = venue.get("name", team.venue_name)
            team.venue_city = venue.get("city", team.venue_city)
            team.venue_state = venue.get("state", team.venue_state)

    return team


async def ingest_wnba_teams() -> None:
    """Main task callable — fetch and upsert WNBA team information."""
    try:
        teams_data = await wnba_client.fetch_all_teams()
    except (RetryError, RapidApiError) as exc:
        _log_error(provider="rapidapi", msg=f"Failed to fetch teams: {exc}")
        return

    if not teams_data:
        _log_error(provider="rapidapi", msg="No teams data received from API")
        return

    session = SessionLocal()
    try:
        teams_processed = 0
        teams_failed = 0

                # teams_data might be a dict with team info nested, or a list
        if isinstance(teams_data, dict):
            # Look for teams in various possible keys
            teams_list = (
                teams_data.get("teams", []) or
                teams_data.get("data", []) or
                teams_data.get("results", []) or
                [teams_data]  # Single team object
            )
        else:
            teams_list = teams_data

        for team_data in teams_list:
            if not team_data or not (team_data.get("teamId") or team_data.get("id")):
                teams_failed += 1
                continue

            try:
                _upsert_wnba_team(session, team_data)
                teams_processed += 1
            except Exception as exc:
                _log_error(provider="rapidapi", msg=f"Error processing team {team_data.get('id', 'unknown')}: {exc}")
                teams_failed += 1
                continue

        session.commit()
        _log_info(provider="rapidapi", msg=f"Teams ingest complete: {teams_processed} teams processed, {teams_failed} failed")

    except Exception as exc:
        session.rollback()
        _log_error(provider="rapidapi", msg=f"Database error during teams ingest: {exc}")
        raise
    finally:
        session.close()
        await wnba_client.close()


def _log_error(provider: str, msg: str) -> None:
    """Log an error message to the database."""
    session = SessionLocal()
    try:
        ingest_log = IngestLog(provider=provider, message=f"ERROR: {msg}")
        session.add(ingest_log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _log_info(provider: str, msg: str) -> None:
    """Log an info message to the database."""
    session = SessionLocal()
    try:
        ingest_log = IngestLog(provider=provider, message=f"INFO: {msg}")
        session.add(ingest_log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()