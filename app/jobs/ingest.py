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
from app.external_apis.rapidapi_client import wnba_client
from app.models import IngestLog

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def fetch_schedule(date_iso: str) -> List[dict[str, Any]]:
    date_obj = dt.datetime.strptime(date_iso, "%Y-%m-%d").date()
    params = {"year": date_obj.strftime("%Y"), "month": date_obj.strftime("%m"), "day": date_obj.strftime("%d")}
    data = await wnba_client._get_json("wnbaschedule", params=params)
    date_key = date_obj.strftime("%Y%m%d")
    return data.get(date_key, [])


async def fetch_box_score(game_id: str) -> dict[str, Any]:
    return await wnba_client._get_json("wnbabox", params={"gameId": game_id})


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _upsert_player(session, athlete: dict[str, Any]) -> models.Player:
    player_id = int(athlete["id"])
    player = session.get(models.Player, player_id)
    if player is None:
        player = models.Player(
            id=player_id, full_name=athlete["displayName"], position=athlete.get("position", {}).get("abbreviation")
        )
        session.add(player)
    else:
        # Update name / position if changed
        player.full_name = athlete["displayName"]
        player.position = athlete.get("position", {}).get("abbreviation")
    return player


def _parse_stat_line(stats: List[str]) -> dict[str, float]:
    # stats array order (see sample): MIN, FG, 3PT, FT, OREB, DREB, REB, AST, STL, BLK, TO, PF, +/- , PTS
    def _to_float(val: str) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    return {
        "points": _to_float(stats[-1]),
        "rebounds": _to_float(stats[6]),
        "assists": _to_float(stats[7]),
        "steals": _to_float(stats[8]),
        "blocks": _to_float(stats[9]),
    }


async def ingest_stat_lines(target_date: dt.date | None = None) -> None:
    """Main task callable — fetch schedule then box-scores and upsert lines."""
    target_date = target_date or (dt.datetime.utcnow() - dt.timedelta(days=1)).date()
    date_iso = target_date.strftime("%Y-%m-%d")
    game_datetime = dt.datetime.combine(target_date, dt.time())

    try:
        games = await fetch_schedule(date_iso)
    except RetryError as exc:
        _log_error(provider="rapidapi", msg=f"Failed to fetch schedule {date_iso}: {exc}")
        return

    for game in games:
        game_id = game["id"]
        try:
            box = await fetch_box_score(game_id)
        except RetryError as exc:
            _log_error(provider="rapidapi", msg=f"Failed to fetch box {game_id}: {exc}")
            continue

        await _process_box_score(box, game_datetime)

    # Close the client after we're done
    await wnba_client.close()


async def _process_box_score(box: dict[str, Any], game_date: dt.datetime) -> None:
    session = SessionLocal()
    try:
        players_blocks = box.get("players", [])
        for team_block in players_blocks:
            for stat_block in team_block.get("statistics", []):
                for athlete_block in stat_block.get("athletes", []):
                    athlete = athlete_block["athlete"]
                    stats_arr = athlete_block.get("stats", [])
                    if not stats_arr:
                        continue

                    player = _upsert_player(session, athlete)

                    stat_vals = _parse_stat_line(stats_arr)

                    # Upsert StatLine
                    existing = (
                        session.query(models.StatLine).filter_by(player_id=player.id, game_date=game_date).one_or_none()
                    )

                    if existing:
                        for k, v in stat_vals.items():
                            setattr(existing, k, v)
                    else:
                        session.add(models.StatLine(player_id=player.id, game_date=game_date, **stat_vals))
        session.commit()
    except Exception as exc:
        # Guard idempotency: ignore unique constraint duplicate inserts
        if "UNIQUE constraint failed" in str(exc):
            session.rollback()
        else:
            session.rollback()
            raise
    finally:
        session.close()


def _log_error(provider: str, msg: str) -> None:
    session = SessionLocal()
    ingest_log = IngestLog(provider=provider, message=msg)
    session.add(ingest_log)
    session.commit()
    session.close()
