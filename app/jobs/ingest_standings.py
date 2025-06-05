"""
WNBA Standings Ingestion Job

This module handles the ingestion of WNBA standings information from the RapidAPI.
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
from app.external_apis.rapidapi_client import ApiKeyError, RapidApiError, RateLimitError, RetryableError, wnba_client
from app.models import IngestLog


def _parse_standings_entry(standings_data: dict[str, Any], season: int, date: dt.datetime) -> dict[str, Any]:
    """Parse a standings entry from the API response."""

    def _to_float(val: Any) -> float:
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _to_int(val: Any) -> int:
        try:
            return int(val) if val is not None else 0
        except (ValueError, TypeError):
            return 0

    def _get_stat_value(stats: list, stat_name: str) -> Any:
        """Extract a stat value from the stats array."""
        for stat in stats:
            if stat.get("name") == stat_name or stat.get("type") == stat_name:
                return stat.get("value")
        return None

    def _get_record_stat(stats: list, stat_id: str) -> str:
        """Extract a record stat (like home/away record) from the stats array."""
        for stat in stats:
            if stat.get("id") == stat_id:
                return stat.get("summary", "0-0")
        return "0-0"

    def _parse_record(record_str: str) -> tuple[int, int]:
        """Parse a record string like '16-4' into wins and losses."""
        try:
            parts = record_str.split("-")
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass
        return 0, 0

    # Extract team information
    team_info = standings_data.get("team", {})
    team_id = team_info.get("id")
    if not team_id:
        raise ValueError("No team ID found in standings data")

    # Extract stats array
    stats = standings_data.get("stats", [])

    # Parse home and away records
    home_record = _get_record_stat(stats, "33")  # Home record
    away_record = _get_record_stat(stats, "34")  # Away record
    conf_record = _get_record_stat(stats, "61")  # Conference record
    div_record = _get_record_stat(stats, "60")  # Division record

    home_wins, home_losses = _parse_record(home_record)
    away_wins, away_losses = _parse_record(away_record)
    conf_wins, conf_losses = _parse_record(conf_record)
    div_wins, div_losses = _parse_record(div_record)

    return {
        "team_id": int(team_id),
        "season": season,
        "date": date,
        "wins": _to_int(_get_stat_value(stats, "wins")),
        "losses": _to_int(_get_stat_value(stats, "losses")),
        "win_percentage": _to_float(_get_stat_value(stats, "winPercent")),
        "games_behind": _to_float(_get_stat_value(stats, "gamesBehind")),
        "home_wins": home_wins,
        "home_losses": home_losses,
        "away_wins": away_wins,
        "away_losses": away_losses,
        "division_wins": div_wins,
        "division_losses": div_losses,
        "conference_wins": conf_wins,
        "conference_losses": conf_losses,
        "points_for": _to_float(_get_stat_value(stats, "pointsFor")),
        "points_against": _to_float(_get_stat_value(stats, "pointsAgainst")),
        "point_differential": _to_float(_get_stat_value(stats, "pointDifferential")),
    }


def _upsert_standings_entry(session, standings_data: dict[str, Any]) -> models.Standings:
    """Create or update a standings entry."""
    # Check if entry already exists for this team/season/date
    existing = (
        session.query(models.Standings)
        .filter_by(team_id=standings_data["team_id"], season=standings_data["season"], date=standings_data["date"])
        .one_or_none()
    )

    if existing:
        # Update existing entry
        for key, value in standings_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        return existing
    else:
        # Create new entry
        new_entry = models.Standings(**standings_data)
        session.add(new_entry)
        return new_entry


async def ingest_standings(year: str | None = None) -> None:
    """Main task callable — fetch and upsert WNBA standings."""
    if year is None:
        year = str(dt.datetime.now().year)

    try:
        standings_data = await wnba_client.fetch_standings(year)
    except (RetryError, RapidApiError) as exc:
        _log_error(provider="rapidapi", msg=f"Failed to fetch standings for {year}: {exc}")
        return

    if not standings_data:
        _log_error(provider="rapidapi", msg=f"No standings data received for {year}")
        return

    session = SessionLocal()
    try:
        entries_processed = 0
        entries_failed = 0
        ingest_date = dt.datetime.utcnow()
        season = int(year)

        # Extract standings entries from the API response
        # The API returns standings in standings.entries
        standings_entries = []
        if isinstance(standings_data, dict):
            standings_info = standings_data.get("standings", {})
            standings_entries = standings_info.get("entries", [])

        if not standings_entries:
            _log_info(provider="rapidapi", msg=f"No standings entries found in API response for {year}")
            return

        for entry in standings_entries:
            if not entry or not entry.get("team", {}).get("id"):
                entries_failed += 1
                continue

            try:
                parsed_entry = _parse_standings_entry(entry, season, ingest_date)
                _upsert_standings_entry(session, parsed_entry)
                entries_processed += 1
            except Exception as exc:
                team_id = entry.get("team", {}).get("id", "unknown")
                _log_error(provider="rapidapi", msg=f"Error processing standings for team {team_id}: {exc}")
                entries_failed += 1
                continue

        session.commit()
        _log_info(
            provider="rapidapi",
            msg=f"Standings ingest complete for {year}: {entries_processed} entries processed, {entries_failed} failed",
        )

    except Exception as exc:
        session.rollback()
        _log_error(provider="rapidapi", msg=f"Database error during standings ingest for {year}: {exc}")
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
