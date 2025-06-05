"""Backfill service for historical game data ingestion and recovery."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.external_apis.rapidapi_client import RapidApiError, RetryError, wnba_client
from app.jobs.ingest import fetch_schedule, ingest_stat_lines
from app.models import IngestionQueue, IngestionRun, IngestLog, Player, StatLine


class BackfillService:
    """Service for backfilling historical game data and managing ingestion queues."""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._should_close_db = db is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_db:
            self.db.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_db:
            self.db.close()

    async def backfill_season(
        self, year: int, start_date: date = None, end_date: date = None, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Backfill all games for a season or date range.

        Args:
            year: Target season year
            start_date: Optional start date (defaults to Jan 1)
            end_date: Optional end date (defaults to Dec 31)
            dry_run: If True, only identify games without ingesting

        Returns:
            Dictionary representation of the IngestionRun record
        """
        start_date = start_date or date(year, 1, 1)
        end_date = end_date or date(year, 12, 31)

        # Create ingestion run record
        run = IngestionRun(
            target_date=start_date, status="running", games_found=0, games_processed=0, players_updated=0, errors="[]"
        )
        self.db.add(run)
        self.db.commit()

        # Capture initial attributes before any processing that might affect session
        run_id = run.id
        run_start_time = run.start_time
        run_target_date = run.target_date

        try:
            current_date = start_date
            total_games_found = 0
            total_games_processed = 0
            total_players_updated = 0
            errors = []

            while current_date <= end_date:
                try:
                    # Get games for this date
                    date_str = current_date.strftime("%Y-%m-%d")
                    games = await fetch_schedule(date_str)

                    if games:
                        total_games_found += len(games)

                        if not dry_run:
                            # Process the date
                            await ingest_stat_lines(current_date)

                            # Count what we processed
                            game_date_dt = dt.datetime.combine(current_date, dt.time())
                            self.db.query(StatLine).filter(
                                StatLine.game_date >= game_date_dt,
                                StatLine.game_date < game_date_dt + dt.timedelta(days=1),
                            ).count()

                            # Count unique players updated
                            updated_players = (
                                self.db.query(func.count(func.distinct(StatLine.player_id)))
                                .filter(
                                    StatLine.game_date >= game_date_dt,
                                    StatLine.game_date < game_date_dt + dt.timedelta(days=1),
                                )
                                .scalar()
                            )

                            total_games_processed += len(games)
                            total_players_updated += updated_players or 0

                except Exception as e:
                    error_msg = f"Error processing {current_date}: {str(e)}"
                    errors.append(error_msg)
                    self._log_error("backfill", error_msg)
                    # Continue processing other dates even if one fails

                current_date += dt.timedelta(days=1)

                # Rate limiting - small delay between requests
                await asyncio.sleep(0.1)

            # Update run record
            run.end_time = datetime.utcnow()
            run.games_found = total_games_found
            run.games_processed = total_games_processed
            run.players_updated = total_players_updated
            run.errors = json.dumps(errors)
            run.status = "completed" if not errors else "partial"

            # Capture final values
            run_end_time = run.end_time
            run_status = run.status
            run_games_found = run.games_found
            run_games_processed = run.games_processed
            run_players_updated = run.players_updated
            run_errors = run.errors

        except Exception as e:
            run.end_time = datetime.utcnow()
            run.status = "failed"
            run.errors = json.dumps([str(e)])
            self._log_error("backfill", f"Season backfill failed: {str(e)}")

            # Capture final values for error case
            run_end_time = run.end_time
            run_status = run.status
            run_games_found = run.games_found
            run_games_processed = run.games_processed
            run_players_updated = run.players_updated
            run_errors = run.errors

        # Commit changes to ensure they're saved
        self.db.commit()

        # Build result dict using the captured values
        result = {
            "id": run_id,
            "start_time": run_start_time.isoformat(),
            "end_time": run_end_time.isoformat() if run_end_time else None,
            "target_date": run_target_date.isoformat(),
            "status": run_status,
            "games_found": run_games_found,
            "games_processed": run_games_processed,
            "players_updated": run_players_updated,
            "errors": run_errors,
        }

        # Close the WNBA client to avoid connection issues
        await wnba_client.close()

        return result

    async def backfill_player_season_stats(self, player_id: int, year: int) -> Dict[str, Any]:
        """
        Backfill all games for a specific player in a season.

        Args:
            player_id: Database ID of the player
            year: Season year

        Returns:
            Summary of the backfill operation
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError(f"Player with ID {player_id} not found")

        # Get existing stat lines for this player in this year
        year_start = datetime(year, 1, 1)
        year_end = datetime(year + 1, 1, 1)

        existing_stats = (
            self.db.query(StatLine)
            .filter(
                and_(StatLine.player_id == player_id, StatLine.game_date >= year_start, StatLine.game_date < year_end)
            )
            .all()
        )

        existing_game_ids = {stat.game_id for stat in existing_stats}

        # Queue games that might be missing
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        current_date = start_date

        games_queued = 0

        while current_date <= end_date:
            try:
                date_str = current_date.strftime("%Y-%m-%d")
                games = await fetch_schedule(date_str)

                for game in games:
                    game_id = str(game.get("id", ""))
                    if game_id and game_id not in existing_game_ids:
                        self._queue_game(game_id, current_date, priority=1)
                        games_queued += 1

            except Exception as e:
                self._log_error("backfill", f"Error queuing games for {current_date}: {str(e)}")

            current_date += dt.timedelta(days=1)
            await asyncio.sleep(0.1)  # Rate limiting

        return {
            "player_name": player.full_name,
            "year": year,
            "existing_games": len(existing_stats),
            "games_queued": games_queued,
        }

    async def reprocess_game(self, game_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Reprocess a specific game, optionally forcing overwrites.

        Args:
            game_id: Game ID to reprocess
            force: If True, overwrite existing data

        Returns:
            Summary of reprocessing result
        """
        # Check if game exists in database
        existing_stats = self.db.query(StatLine).filter(StatLine.game_id == game_id).all()

        if existing_stats and not force:
            return {
                "game_id": game_id,
                "status": "skipped",
                "reason": "Game already exists (use force=True to overwrite)",
                "existing_stats": len(existing_stats),
            }

        # Try to find the game date from existing data
        game_date = None
        if existing_stats:
            game_date = existing_stats[0].game_date.date()
        else:
            # We need to search for the game date by querying recent schedules
            # This is a fallback - in practice, game_id should come with date context
            for days_back in range(30):  # Look back up to 30 days
                check_date = date.today() - dt.timedelta(days=days_back)
                try:
                    games = await fetch_schedule(check_date.strftime("%Y-%m-%d"))
                    for game in games:
                        if str(game.get("id", "")) == game_id:
                            game_date = check_date
                            break
                    if game_date:
                        break
                except Exception:
                    continue

        if not game_date:
            return {"game_id": game_id, "status": "failed", "reason": "Could not determine game date"}

        # Queue the game for reprocessing
        self._queue_game(game_id, game_date, priority=2)  # High priority

        return {"game_id": game_id, "status": "queued", "game_date": game_date.isoformat(), "force": force}

    async def find_missing_games(self, start_date: date, end_date: date) -> List[str]:
        """
        Identify games that should exist but aren't in the database.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of missing game IDs
        """
        missing_games = []
        current_date = start_date

        while current_date <= end_date:
            try:
                # Get games from API
                date_str = current_date.strftime("%Y-%m-%d")
                api_games = await fetch_schedule(date_str)

                if api_games:
                    api_game_ids = {str(game.get("id", "")) for game in api_games}

                    # Get games we have in database for this date
                    game_date_dt = dt.datetime.combine(current_date, dt.time())
                    db_game_ids = set(
                        self.db.query(StatLine.game_id)
                        .filter(
                            StatLine.game_date >= game_date_dt, StatLine.game_date < game_date_dt + dt.timedelta(days=1)
                        )
                        .distinct()
                        .all()
                    )
                    db_game_ids = {game_id[0] for game_id in db_game_ids}

                    # Find missing games
                    missing_for_date = api_game_ids - db_game_ids
                    missing_games.extend(missing_for_date)

            except Exception as e:
                self._log_error("backfill", f"Error checking missing games for {current_date}: {str(e)}")

            current_date += dt.timedelta(days=1)
            await asyncio.sleep(0.1)  # Rate limiting

        return missing_games

    def get_ingestion_health(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get ingestion system health metrics.

        Args:
            days_back: Number of days to look back for metrics

        Returns:
            Health metrics dictionary
        """
        cutoff_date = datetime.utcnow() - dt.timedelta(days=days_back)

        # Recent ingestion runs
        recent_runs = (
            self.db.query(IngestionRun)
            .filter(IngestionRun.start_time >= cutoff_date)
            .order_by(IngestionRun.start_time.desc())
            .all()
        )

        # Queue status
        queue_stats = (
            self.db.query(IngestionQueue.status, func.count().label('count')).group_by(IngestionQueue.status).all()
        )

        # Recent errors
        recent_errors = (
            self.db.query(IngestLog)
            .filter(and_(IngestLog.timestamp >= cutoff_date, IngestLog.message.like("ERROR:%")))
            .count()
        )

        # Recent stat lines
        recent_stats = self.db.query(StatLine).filter(StatLine.game_date >= cutoff_date).count()

        return {
            "period_days": days_back,
            "recent_runs": len(recent_runs),
            "successful_runs": len([r for r in recent_runs if r.status == "completed"]),
            "failed_runs": len([r for r in recent_runs if r.status == "failed"]),
            "queue_status": {status: count for status, count in queue_stats},
            "recent_errors": recent_errors,
            "recent_stat_lines": recent_stats,
            "last_successful_run": max((r.end_time for r in recent_runs if r.status == "completed"), default=None),
        }

    def _queue_game(self, game_id: str, game_date: date, priority: int = 0) -> IngestionQueue:
        """Add a game to the ingestion queue."""
        # Check if already queued
        existing = self.db.query(IngestionQueue).filter(IngestionQueue.game_id == game_id).first()

        if existing:
            # Update priority if higher
            if priority > existing.priority:
                existing.priority = priority
                existing.status = "pending"  # Reset status
                self.db.commit()
            return existing

        # Create new queue entry
        queue_entry = IngestionQueue(game_id=game_id, game_date=game_date, priority=priority, status="pending")
        self.db.add(queue_entry)
        self.db.commit()
        return queue_entry

    def _log_error(self, provider: str, message: str):
        """Log an error message."""
        log_entry = IngestLog(provider=provider, message=f"ERROR: {message}")
        self.db.add(log_entry)
        self.db.commit()

    def _log_info(self, provider: str, message: str):
        """Log an info message."""
        log_entry = IngestLog(provider=provider, message=f"INFO: {message}")
        self.db.add(log_entry)
        self.db.commit()
