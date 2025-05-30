from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

# Optional dependency
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

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def fetch_schedule(date_iso: str) -> List[dict[str, Any]]:
    """Fetch schedule for a given date using the RapidAPI client."""
    date_obj = dt.datetime.strptime(date_iso, "%Y-%m-%d").date()
    year = date_obj.strftime("%Y")
    month = date_obj.strftime("%m")
    day = date_obj.strftime("%d")

    try:
        return await wnba_client.fetch_schedule(year, month, day)
    except RateLimitError as e:
        _log_error(provider="rapidapi", msg=f"Rate limit exceeded fetching schedule for {date_iso}: {e}")
        raise
    except ApiKeyError as e:
        _log_error(provider="rapidapi", msg=f"API key error fetching schedule for {date_iso}: {e}")
        raise
    except RapidApiError as e:
        _log_error(provider="rapidapi", msg=f"API error fetching schedule for {date_iso}: {e}")
        raise


async def fetch_box_score(game_id: str) -> dict[str, Any]:
    """Fetch box score for a specific game using the RapidAPI client."""
    try:
        return await wnba_client.fetch_box_score(game_id)
    except RateLimitError as e:
        _log_error(provider="rapidapi", msg=f"Rate limit exceeded fetching box score for game {game_id}: {e}")
        raise
    except ApiKeyError as e:
        _log_error(provider="rapidapi", msg=f"API key error fetching box score for game {game_id}: {e}")
        raise
    except RapidApiError as e:
        _log_error(provider="rapidapi", msg=f"API error fetching box score for game {game_id}: {e}")
        raise


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _upsert_player(session, athlete: dict[str, Any]) -> models.Player:
    """Create or update a player record."""
    player_id = int(athlete["id"])
    player = session.get(models.Player, player_id)
    if player is None:
        player = models.Player(
            id=player_id,
            full_name=athlete["displayName"],
            position=athlete.get("position", {}).get("abbreviation")
        )
        session.add(player)
    else:
        # Update name / position if changed
        player.full_name = athlete["displayName"]
        player.position = athlete.get("position", {}).get("abbreviation")
    return player


def _parse_stat_line(stats: List[str]) -> dict[str, float]:
    """
    Parse stats array from WNBA API response.

    Based on actual API response structure:
    stats array format: [MIN, FG, 3PT, FT, OREB, DREB, REB, AST, STL, BLK, TO, PF, +/-, PTS]
    Indices:             [0,   1,  2,   3,  4,    5,    6,   7,   8,   9,   10, 11, 12,  13]
    """
    def _to_float(val: str) -> float:
        try:
            # Handle cases like "2-7" for field goals by extracting the made shots
            if "-" in val:
                val = val.split("-")[0]
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    if len(stats) < 14:
        # If stats array is incomplete, return zeros for safety
        return {
            "points": 0.0,
            "rebounds": 0.0,
            "assists": 0.0,
            "steals": 0.0,
            "blocks": 0.0,
        }

    return {
        "points": _to_float(stats[13]),      # PTS - last element
        "rebounds": _to_float(stats[6]),     # REB - total rebounds
        "assists": _to_float(stats[7]),      # AST
        "steals": _to_float(stats[8]),       # STL
        "blocks": _to_float(stats[9]),       # BLK
    }


async def ingest_stat_lines(target_date: dt.date | None = None) -> None:
    """Main task callable — fetch schedule then box-scores and upsert lines."""
    target_date = target_date or (dt.datetime.utcnow() - dt.timedelta(days=1)).date()
    date_iso = target_date.strftime("%Y-%m-%d")
    game_datetime = dt.datetime.combine(target_date, dt.time())

    try:
        games = await fetch_schedule(date_iso)
    except (RetryError, RapidApiError) as exc:
        _log_error(provider="rapidapi", msg=f"Failed to fetch schedule {date_iso}: {exc}")
        return

    if not games:
        _log_error(provider="rapidapi", msg=f"No games found for {date_iso}")
        return

    processed_games = 0
    failed_games = 0

    for game in games:
        game_id = game.get("id")
        if not game_id:
            _log_error(provider="rapidapi", msg=f"Game missing ID in schedule response: {game}")
            failed_games += 1
            continue

        try:
            box = await fetch_box_score(str(game_id))
            await _process_box_score(box, game_datetime, game_id)
            processed_games += 1
        except (RetryError, RapidApiError) as exc:
            _log_error(provider="rapidapi", msg=f"Failed to fetch box score for game {game_id}: {exc}")
            failed_games += 1
            continue
        except Exception as exc:
            _log_error(provider="rapidapi", msg=f"Unexpected error processing game {game_id}: {exc}")
            failed_games += 1
            continue

    # Log summary
    _log_info(provider="rapidapi", msg=f"Ingest complete for {date_iso}: {processed_games} games processed, {failed_games} failed")

    # Close the client after we're done
    await wnba_client.close()


async def _process_box_score(box: dict[str, Any], game_date: dt.datetime, game_id: str) -> None:
    """Process a single box score and upsert player stats."""
    session = SessionLocal()
    try:
        players_blocks = box.get("players", [])
        if not players_blocks:
            _log_error(provider="rapidapi", msg=f"No players data in box score for game {game_id}")
            return

        stats_processed = 0
        for team_block in players_blocks:
            statistics = team_block.get("statistics", [])
            if not statistics:
                continue

            for stat_block in statistics:
                athletes = stat_block.get("athletes", [])
                if not athletes:
                    continue

                for athlete_block in athletes:
                    athlete = athlete_block.get("athlete")
                    if not athlete:
                        continue

                    # Skip players who didn't play
                    if athlete_block.get("didNotPlay", False):
                        continue

                    stats_arr = athlete_block.get("stats", [])
                    if not stats_arr:
                        continue

                    try:
                        player = _upsert_player(session, athlete)
                        stat_vals = _parse_stat_line(stats_arr)

                        # Upsert StatLine
                        existing = (
                            session.query(models.StatLine)
                            .filter_by(player_id=player.id, game_date=game_date)
                            .one_or_none()
                        )

                        if existing:
                            for k, v in stat_vals.items():
                                setattr(existing, k, v)
                        else:
                            session.add(models.StatLine(player_id=player.id, game_date=game_date, **stat_vals))

                        stats_processed += 1
                    except Exception as exc:
                        _log_error(provider="rapidapi", msg=f"Error processing player {athlete.get('id', 'unknown')} in game {game_id}: {exc}")
                        continue

        session.commit()
        _log_info(provider="rapidapi", msg=f"Processed {stats_processed} stat lines for game {game_id}")

    except Exception as exc:
        # Guard idempotency: ignore unique constraint duplicate inserts
        if "UNIQUE constraint failed" in str(exc):
            session.rollback()
            _log_info(provider="rapidapi", msg=f"Duplicate stats found for game {game_id}, skipping")
        else:
            session.rollback()
            _log_error(provider="rapidapi", msg=f"Database error processing game {game_id}: {exc}")
            raise
    finally:
        session.close()


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
