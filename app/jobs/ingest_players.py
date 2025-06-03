from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app import models
from app.core.database import SessionLocal
from app.external_apis.rapidapi_client import wnba_client, RapidApiError, RateLimitError, ApiKeyError, RetryableError
from app.models import IngestLog


def _log_error(provider: str, msg: str) -> None:
    """Log an error message to the database."""
    session = SessionLocal()
    try:
        log_entry = IngestLog(provider=provider, message=msg)
        session.add(log_entry)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _log_info(provider: str, msg: str) -> None:
    """Log an info message to the database."""
    session = SessionLocal()
    try:
        log_entry = IngestLog(provider=provider, message=f"INFO: {msg}")
        session.add(log_entry)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _parse_height(height_str: str | None) -> int | None:
    """Parse height string like '6-2' to inches."""
    if not height_str:
        return None
    try:
        # Format is typically "6-2" (feet-inches)
        if "-" in height_str:
            feet, inches = height_str.split("-")
            return int(feet) * 12 + int(inches)
        else:
            # Assume it's just inches if no dash
            return int(height_str)
    except (ValueError, TypeError):
        return None


def _parse_weight(weight_str: str | None) -> int | None:
    """Parse weight string to integer."""
    if not weight_str:
        return None
    try:
        # Remove any non-numeric characters except the number itself
        weight_clean = ''.join(c for c in weight_str if c.isdigit())
        return int(weight_clean) if weight_clean else None
    except (ValueError, TypeError):
        return None


def _parse_draft_info(draft_str: str | None) -> tuple[int | None, int | None, int | None]:
    """Parse draft string like '2020 Round 1, Pick 5' to year, round, pick."""
    if not draft_str:
        return None, None, None

    try:
        # Common formats: "2020 Round 1, Pick 5" or "2020 R1 P5" or "Undrafted"
        if "undrafted" in draft_str.lower() or "not drafted" in draft_str.lower():
            return None, None, None

        year = None
        round_num = None
        pick_num = None

        # Extract year (first 4 digits)
        for word in draft_str.split():
            if word.isdigit() and len(word) == 4:
                year = int(word)
                break

        # Extract round
        if "round" in draft_str.lower():
            import re
            round_match = re.search(r'round\s*(\d+)', draft_str.lower())
            if round_match:
                round_num = int(round_match.group(1))

        # Extract pick
        if "pick" in draft_str.lower():
            import re
            pick_match = re.search(r'pick\s*(\d+)', draft_str.lower())
            if pick_match:
                pick_num = int(pick_match.group(1))

        return year, round_num, pick_num
    except (ValueError, TypeError):
        return None, None, None


def _parse_birth_date(birth_str: str | None) -> dt.datetime | None:
    """Parse birth date string to datetime."""
    if not birth_str:
        return None

    try:
        # Common formats: "1995-06-15", "June 15, 1995", "6/15/1995"
        from dateutil import parser
        return parser.parse(birth_str)
    except (ValueError, TypeError, ImportError):
        # If dateutil is not available, try simple formats
        try:
            if "-" in birth_str:
                return dt.datetime.strptime(birth_str, "%Y-%m-%d")
            elif "/" in birth_str:
                return dt.datetime.strptime(birth_str, "%m/%d/%Y")
        except ValueError:
            pass
        return None


async def _upsert_player_from_roster(session, roster_player: Dict[str, Any]) -> models.Player:
    """Create or update a player record from roster data."""
    player_id = int(roster_player["playerId"])  # API uses "playerId" not "id"
    player = session.get(models.Player, player_id)

    if player is None:
        player = models.Player(
            id=player_id,
            full_name=roster_player.get("displayName", ""),
            created_at=dt.datetime.utcnow(),
            updated_at=dt.datetime.utcnow()
        )
        session.add(player)
    else:
        player.updated_at = dt.datetime.utcnow()

    # Update basic info from roster
    player.full_name = roster_player.get("displayName", player.full_name)
    player.position = roster_player.get("position", {}).get("abbreviation")
    player.jersey_number = roster_player.get("jersey")  # API returns jersey as string directly

    # Parse name components
    if roster_player.get("firstName"):
        player.first_name = roster_player["firstName"]
    if roster_player.get("lastName"):
        player.last_name = roster_player["lastName"]

    # Add basic physical stats from roster if available
    if roster_player.get("height"):
        player.height = roster_player["height"]  # API returns height in inches
    if roster_player.get("weight"):
        player.weight = roster_player["weight"]  # API returns weight in lbs

    # Add college info if available
    if roster_player.get("college", {}).get("name"):
        player.college = roster_player["college"]["name"]

    # Add birth info if available
    if roster_player.get("dateOfBirth"):
        player.birth_date = _parse_birth_date(roster_player["dateOfBirth"])
    if roster_player.get("birthPlace", {}).get("city"):
        birth_place_parts = []
        birth_place = roster_player["birthPlace"]
        if birth_place.get("city"):
            birth_place_parts.append(birth_place["city"])
        if birth_place.get("state"):
            birth_place_parts.append(birth_place["state"])
        if birth_place.get("country"):
            birth_place_parts.append(birth_place["country"])
        player.birth_place = ", ".join(birth_place_parts)

    # Add experience if available
    if roster_player.get("experience", {}).get("years") is not None:
        player.years_pro = roster_player["experience"]["years"]

    # Add headshot if available
    if roster_player.get("headshot"):
        player.headshot_url = roster_player["headshot"]

    # Add status if available
    if roster_player.get("status"):
        status = roster_player["status"].lower()
        player.status = status if status in ["active", "injured", "inactive"] else "active"

    return player


async def _enhance_player_with_bio(session, player: models.Player) -> None:
    """Enhance player with biographical data from the bio API."""
    try:
        bio_data = await wnba_client.fetch_player_bio(str(player.id))

        if not bio_data:
            return

        # Extract biographical information
        athlete = bio_data.get("athlete", {})

        # Physical stats
        player.height = _parse_height(athlete.get("height"))
        player.weight = _parse_weight(athlete.get("weight"))

        # Birth information
        player.birth_date = _parse_birth_date(athlete.get("birthDate"))
        player.birth_place = athlete.get("birthPlace", {}).get("displayText")

        # College
        player.college = athlete.get("college", {}).get("name")

        # Draft information
        draft_info = athlete.get("draft", {})
        if draft_info:
            player.draft_year = draft_info.get("year")
            player.draft_round = draft_info.get("round")
            player.draft_pick = draft_info.get("selection")

        # Years pro
        player.years_pro = athlete.get("experience", {}).get("years")

        # Headshot
        headshot = athlete.get("headshot", {})
        if headshot and headshot.get("href"):
            player.headshot_url = headshot["href"]

        # Status (active/injured/inactive)
        status = athlete.get("status", {}).get("type", {}).get("name", "active").lower()
        player.status = status if status in ["active", "injured", "inactive"] else "active"

        player.updated_at = dt.datetime.utcnow()

    except (RateLimitError, ApiKeyError) as e:
        _log_error(provider="rapidapi", msg=f"API error fetching bio for player {player.id}: {e}")
        raise
    except RapidApiError as e:
        _log_error(provider="rapidapi", msg=f"API error fetching bio for player {player.id}: {e}")
    except Exception as e:
        _log_error(provider="rapidapi", msg=f"Unexpected error fetching bio for player {player.id}: {e}")


async def ingest_player_profiles() -> None:
    """
    Comprehensive player profile ingestion that:
    1. Fetches all teams
    2. For each team, fetches the roster
    3. For each player, fetches detailed bio information
    4. Updates or creates player records with full data
    """
    processed_teams = 0
    processed_players = 0
    failed_players = 0

    try:
        # Step 1: Fetch all teams
        _log_info(provider="rapidapi", msg="Starting player profile ingestion")
        teams_data = await wnba_client.fetch_all_teams()

        if not teams_data:
            _log_error(provider="rapidapi", msg="No teams data received")
            return

        # teams_data is a list of teams directly from the API
        if isinstance(teams_data, list):
            teams = teams_data
        else:
            # Fallback to old structure in case API changes
            teams = teams_data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])

        if not teams:
            _log_error(provider="rapidapi", msg="No teams found in API response")
            return

        _log_info(provider="rapidapi", msg=f"Found {len(teams)} teams to process")

        # Step 2: Process each team's roster
        for team in teams:
            team_id = team.get("teamId") or team.get("id")  # API returns teamId as string
            team_name = team.get("displayName", "Unknown")

            if not team_id:
                _log_error(provider="rapidapi", msg=f"Team missing ID: {team}")
                continue

            try:
                # Fetch team roster
                roster_data = await wnba_client.fetch_team_roster(str(team_id))

                if not roster_data:
                    _log_error(provider="rapidapi", msg=f"No roster data for team {team_name} ({team_id})")
                    continue

                # Extract athletes/players from roster
                # API returns players in "data" array, not nested in "team.athletes"
                athletes = roster_data.get("data", [])
                if not athletes:
                    _log_info(provider="rapidapi", msg=f"No players found for team {team_name}")
                    continue

                processed_teams += 1
                _log_info(provider="rapidapi", msg=f"Processing {len(athletes)} players for {team_name}")

                # Step 3: Process each player
                session = SessionLocal()
                try:
                    for athlete in athletes:
                        try:
                            # Create/update player from roster data
                            player = await _upsert_player_from_roster(session, athlete)

                            # Set team association
                            team_abbr = team.get("abbreviation")
                            player.team_abbr = team_abbr

                            # Also link to the WNBATeam record for proper relationships
                            if team_abbr:
                                wnba_team = session.query(models.WNBATeam).filter(
                                    models.WNBATeam.abbreviation == team_abbr
                                ).first()
                                if wnba_team:
                                    player.wnba_team_id = wnba_team.id

                            # Most biographical data is already in roster, so we don't need to call bio API
                            # This avoids rate limiting issues and speeds up the process
                            # await _enhance_player_with_bio(session, player)

                            processed_players += 1

                            # Commit after each player to avoid losing progress
                            session.commit()

                        except (RateLimitError, ApiKeyError) as e:
                            # Don't continue if we hit rate limits or auth issues
                            session.rollback()
                            _log_error(provider="rapidapi", msg=f"API limit hit, stopping ingestion: {e}")
                            return
                        except Exception as e:
                            session.rollback()
                            failed_players += 1
                            _log_error(provider="rapidapi", msg=f"Error processing player {athlete.get('playerId', 'unknown')}: {e}")
                            continue

                finally:
                    session.close()

                # Add delay between teams to be respectful of API limits
                await asyncio.sleep(1.0)

            except (RateLimitError, ApiKeyError) as e:
                _log_error(provider="rapidapi", msg=f"API limit hit for team {team_name}: {e}")
                break  # Stop processing if we hit limits
            except Exception as e:
                _log_error(provider="rapidapi", msg=f"Error processing team {team_name}: {e}")
                continue

        # Final summary
        _log_info(
            provider="rapidapi",
            msg=f"Player ingestion complete: {processed_teams} teams, {processed_players} players processed, {failed_players} failed"
        )

    except Exception as e:
        _log_error(provider="rapidapi", msg=f"Fatal error in player ingestion: {e}")
    finally:
        await wnba_client.close()


if __name__ == "__main__":
    # For testing
    asyncio.run(ingest_player_profiles())