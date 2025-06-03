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


def _parse_comprehensive_stats(stats: List[str], athlete_data: dict) -> dict[str, Any]:
    """
    Parse all 14 statistical categories from the API response.
    Stats array format: [MIN, FG, 3PT, FT, OREB, DREB, REB, AST, STL, BLK, TO, PF, +/-, PTS]
    Indices:             [0,   1,  2,   3,  4,    5,    6,   7,   8,   9,   10, 11, 12,  13]
    """
    def _to_float(val: str) -> float:
        try:
            if "-" in val:
                val = val.split("-")[0]
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def _to_int(val: str) -> int:
        try:
            if "-" in val:
                val = val.split("-")[0]
            return int(val)
        except (ValueError, TypeError):
            return 0

    def _parse_shooting(val: str) -> tuple[int, int, float]:
        """Parse shooting stats like '2-7' to return (made, attempted, percentage)"""
        try:
            if "-" in val:
                made, attempted = val.split("-")
                made, attempted = int(made), int(attempted)
                percentage = (made / attempted * 100) if attempted > 0 else 0.0
                return made, attempted, percentage
            else:
                # If no dash, assume it's just made shots with 0 attempted
                made = int(val) if val else 0
                return made, 0, 0.0
        except (ValueError, TypeError):
            return 0, 0, 0.0

    if len(stats) < 14:
        # If stats array is incomplete, return zeros for safety
        return {
            "minutes_played": 0.0,
            "field_goals_made": 0,
            "field_goals_attempted": 0,
            "field_goal_percentage": 0.0,
            "three_pointers_made": 0,
            "three_pointers_attempted": 0,
            "three_point_percentage": 0.0,
            "free_throws_made": 0,
            "free_throws_attempted": 0,
            "free_throw_percentage": 0.0,
            "offensive_rebounds": 0,
            "defensive_rebounds": 0,
            "rebounds": 0.0,
            "assists": 0.0,
            "steals": 0.0,
            "blocks": 0.0,
            "turnovers": 0,
            "personal_fouls": 0,
            "plus_minus": 0,
            "points": 0.0,
        }

    # Parse shooting statistics
    fg_made, fg_attempted, fg_percentage = _parse_shooting(stats[1])
    threept_made, threept_attempted, threept_percentage = _parse_shooting(stats[2])
    ft_made, ft_attempted, ft_percentage = _parse_shooting(stats[3])

    return {
        "minutes_played": _to_float(stats[0]),
        "field_goals_made": fg_made,
        "field_goals_attempted": fg_attempted,
        "field_goal_percentage": fg_percentage,
        "three_pointers_made": threept_made,
        "three_pointers_attempted": threept_attempted,
        "three_point_percentage": threept_percentage,
        "free_throws_made": ft_made,
        "free_throws_attempted": ft_attempted,
        "free_throw_percentage": ft_percentage,
        "offensive_rebounds": _to_int(stats[4]),
        "defensive_rebounds": _to_int(stats[5]),
        "rebounds": _to_float(stats[6]),      # Total rebounds
        "assists": _to_float(stats[7]),
        "steals": _to_float(stats[8]),
        "blocks": _to_float(stats[9]),
        "turnovers": _to_int(stats[10]),
        "personal_fouls": _to_int(stats[11]),
        "plus_minus": _to_int(stats[12]),
        "points": _to_float(stats[13]),
    }


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

    _log_info(provider="rapidapi", msg=f"Starting ingest for {date_iso}")

    try:
        games = await fetch_schedule(date_iso)
        _log_info(provider="rapidapi", msg=f"Fetched schedule for {date_iso}: {len(games) if games else 0} games found")
    except (RetryError, RapidApiError) as exc:
        _log_error(provider="rapidapi", msg=f"Failed to fetch schedule {date_iso}: {exc}")
        return
    except Exception as exc:
        _log_error(provider="rapidapi", msg=f"Unexpected error fetching schedule {date_iso}: {exc}")
        return

    if not games:
        _log_info(provider="rapidapi", msg=f"No games found for {date_iso} - this is normal for off-season dates")
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
            await _process_box_score(box, game_datetime, game_id, game)
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


async def _process_box_score(box: dict[str, Any], game_date: dt.datetime, game_id: str, schedule_game: dict[str, Any]) -> None:
    """Process a single box score and upsert player stats."""
    session = SessionLocal()
    try:
        # Extract game information from teams array
        teams = box.get("teams", [])

        # Find home and away teams from box score
        home_team_id = None
        away_team_id = None

        for team_data in teams:
            team_info = team_data.get("team", {})
            if team_data.get("homeAway") == "home":
                home_team_id = team_info.get("id")
            elif team_data.get("homeAway") == "away":
                away_team_id = team_info.get("id")

        # Extract scores, venue, and status from schedule data
        home_score = 0
        away_score = 0
        venue = None
        status = "scheduled"

        # Get venue from schedule data
        venue_info = schedule_game.get("venue", {})
        if venue_info:
            venue = venue_info.get("fullName")

        # Get status from schedule data
        status_info = schedule_game.get("status", {})
        if status_info:
            if schedule_game.get("completed", False):
                status = "final"
            elif status_info.get("state") == "in":
                status = "in_progress"
            else:
                status = "scheduled"

        # Get scores from schedule data
        competitors = schedule_game.get("competitors", [])
        for comp in competitors:
            score = comp.get("score", 0)
            team_id = comp.get("id")
            is_home = comp.get("isHome", False)

            if is_home and str(team_id) == str(home_team_id):
                home_score = score
            elif not is_home and str(team_id) == str(away_team_id):
                away_score = score

        # Upsert Game record
        existing_game = session.get(models.Game, game_id)
        if existing_game:
            # Update existing game
            existing_game.date = game_date
            existing_game.home_team_id = int(home_team_id) if home_team_id else None
            existing_game.away_team_id = int(away_team_id) if away_team_id else None
            existing_game.home_score = home_score
            existing_game.away_score = away_score
            existing_game.status = status
            existing_game.venue = venue
        else:
            # Create new game
            new_game = models.Game(
                id=game_id,
                date=game_date,
                home_team_id=int(home_team_id) if home_team_id else None,
                away_team_id=int(away_team_id) if away_team_id else None,
                home_score=home_score,
                away_score=away_score,
                status=status,
                venue=venue,
                attendance=None  # Attendance not available in current API
            )
            session.add(new_game)

        session.commit()  # Commit game record first

        players_blocks = box.get("players", [])
        if not players_blocks:
            _log_error(provider="rapidapi", msg=f"No players data in box score for game {game_id}")
            return

        stats_processed = 0
        dnp_processed = 0

        for team_idx, team_block in enumerate(players_blocks):
            # Determine team info from teams array
            team_info = teams[team_idx] if team_idx < len(teams) else {}
            current_team_id = int(team_info.get("team", {}).get("id")) if team_info.get("team", {}).get("id") else None
            is_home_team = team_info.get("homeAway") == "home"
            opponent_team_id = away_team_id if is_home_team else home_team_id

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

                    player = _upsert_player(session, athlete)

                    # Handle DNP players
                    did_not_play = athlete_block.get("didNotPlay", False)

                    if did_not_play:
                        # Create DNP record
                        existing = (
                            session.query(models.StatLine)
                            .filter_by(player_id=player.id, game_id=game_id)
                            .one_or_none()
                        )

                        if existing:
                            existing.did_not_play = True
                            existing.game_date = game_date
                            existing.team_id = current_team_id
                            existing.opponent_id = opponent_team_id
                            existing.is_home_game = is_home_team
                        else:
                            dnp_stats = models.StatLine(
                                player_id=player.id,
                                game_id=game_id,
                                game_date=game_date,
                                did_not_play=True,
                                team_id=current_team_id,
                                opponent_id=opponent_team_id,
                                is_home_game=is_home_team
                            )
                            session.add(dnp_stats)

                        dnp_processed += 1
                        continue

                    stats_arr = athlete_block.get("stats", [])
                    if not stats_arr:
                        continue

                    try:
                        stat_vals = _parse_comprehensive_stats(stats_arr, athlete)

                        # Add game context
                        stat_vals.update({
                            "game_id": game_id,
                            "game_date": game_date,
                            "team_id": current_team_id,
                            "opponent_id": opponent_team_id,
                            "is_home_game": is_home_team,
                            "is_starter": athlete_block.get("starter", False)
                        })

                        # Upsert StatLine
                        existing = (
                            session.query(models.StatLine)
                            .filter_by(player_id=player.id, game_id=game_id)
                            .one_or_none()
                        )

                        if existing:
                            for k, v in stat_vals.items():
                                setattr(existing, k, v)
                        else:
                            session.add(models.StatLine(player_id=player.id, **stat_vals))

                        stats_processed += 1
                    except Exception as exc:
                        _log_error(provider="rapidapi", msg=f"Error processing player {athlete.get('id', 'unknown')} in game {game_id}: {exc}")
                        continue

        session.commit()
        _log_info(provider="rapidapi", msg=f"Processed game {game_id}: {stats_processed} stat lines, {dnp_processed} DNP records")

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
