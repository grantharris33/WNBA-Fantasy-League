"""
Live game update job for real-time game tracking.
Handles frequent updates during live games while avoiding updates on finished games.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Game, LiveGameTracker
from app.services.live_games import LiveGameService

logger = logging.getLogger(__name__)


class LiveGameUpdateJob:
    """Job for updating live games in real-time."""

    def __init__(self):
        self.db = next(get_db())
        self.live_game_service = LiveGameService(self.db)

    def run_live_updates(self) -> dict:
        """
        Run live game updates for all active games.

        Returns:
            Dictionary with update results
        """
        try:
            logger.info("Starting live game updates")

            # Get games that need updates
            games_to_update = self.live_game_service.get_games_to_update()

            if not games_to_update:
                logger.info("No games need updates at this time")
                return {"success": True, "games_updated": 0, "message": "No games to update"}

            results = {
                "success": True,
                "games_updated": 0,
                "games_processed": len(games_to_update),
                "updates": [],
                "errors": [],
            }

            for tracker in games_to_update:
                try:
                    logger.info(f"Updating game {tracker.game_id} (status: {tracker.status})")

                    update_result = self.live_game_service.update_live_game(tracker.game_id)

                    if update_result.get("success"):
                        results["games_updated"] += 1
                        results["updates"].append(
                            {
                                "game_id": tracker.game_id,
                                "status": update_result.get("status"),
                                "home_score": update_result.get("home_score"),
                                "away_score": update_result.get("away_score"),
                                "player_stats_updated": update_result.get("player_stats_updated", 0),
                            }
                        )
                        logger.info(f"Successfully updated game {tracker.game_id}")
                    else:
                        error_msg = f"Failed to update game {tracker.game_id}: {update_result.get('error')}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)

                except Exception as e:
                    error_msg = f"Error updating game {tracker.game_id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(
                f"Live game updates completed. Updated {results['games_updated']}/{results['games_processed']} games"
            )

            return results

        except Exception as e:
            logger.error(f"Critical error in live game updates: {e}")
            return {"success": False, "error": str(e), "games_updated": 0}
        finally:
            self.db.close()

    def start_tracking_todays_games(self) -> dict:
        """
        Start tracking all games scheduled for today.

        Returns:
            Dictionary with tracking setup results
        """
        try:
            logger.info("Setting up tracking for today's games")

            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)

            # Get all games for today
            todays_games = self.db.query(Game).filter(Game.date >= today, Game.date < tomorrow).all()

            if not todays_games:
                logger.info("No games scheduled for today")
                return {"success": True, "games_tracked": 0, "message": "No games scheduled for today"}

            results = {
                "success": True,
                "games_tracked": 0,
                "games_found": len(todays_games),
                "tracking_started": [],
                "already_tracking": [],
                "errors": [],
            }

            for game in todays_games:
                try:
                    # Check if already tracking
                    existing_tracker = self.db.query(LiveGameTracker).filter(LiveGameTracker.game_id == game.id).first()

                    if existing_tracker and existing_tracker.is_active:
                        results["already_tracking"].append(game.id)
                        logger.info(f"Already tracking game {game.id}")
                        continue

                    # Start tracking
                    if self.live_game_service.start_tracking_game(game.id):
                        results["games_tracked"] += 1
                        results["tracking_started"].append(game.id)
                        logger.info(f"Started tracking game {game.id}")
                    else:
                        error_msg = f"Failed to start tracking game {game.id}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)

                except Exception as e:
                    error_msg = f"Error setting up tracking for game {game.id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(f"Game tracking setup completed. Tracking {results['games_tracked']} new games")

            return results

        except Exception as e:
            logger.error(f"Critical error setting up game tracking: {e}")
            return {"success": False, "error": str(e), "games_tracked": 0}

    def cleanup_old_trackers(self, days_old: int = 7) -> dict:
        """
        Clean up old game trackers and live stats.

        Args:
            days_old: Remove trackers older than this many days

        Returns:
            Dictionary with cleanup results
        """
        try:
            logger.info(f"Cleaning up game trackers older than {days_old} days")

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Find old trackers
            old_trackers = self.db.query(LiveGameTracker).filter(LiveGameTracker.game_date < cutoff_date).all()

            if not old_trackers:
                logger.info("No old trackers to clean up")
                return {"success": True, "trackers_removed": 0, "message": "No old trackers found"}

            results = {"success": True, "trackers_removed": 0, "live_stats_removed": 0, "errors": []}

            for tracker in old_trackers:
                try:
                    # Remove associated live stats first
                    from app.models import LivePlayerStats

                    live_stats = self.db.query(LivePlayerStats).filter(LivePlayerStats.game_id == tracker.game_id).all()

                    for stat in live_stats:
                        self.db.delete(stat)
                        results["live_stats_removed"] += 1

                    # Remove the tracker
                    self.db.delete(tracker)
                    results["trackers_removed"] += 1

                    logger.info(f"Removed tracker for game {tracker.game_id}")

                except Exception as e:
                    error_msg = f"Error removing tracker for game {tracker.game_id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            self.db.commit()
            logger.info(
                f"Cleanup completed. Removed {results['trackers_removed']} trackers and {results['live_stats_removed']} live stats"
            )

            return results

        except Exception as e:
            logger.error(f"Critical error during cleanup: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e), "trackers_removed": 0}

    def stop_finished_games(self) -> dict:
        """
        Stop tracking games that have finished.

        Returns:
            Dictionary with results
        """
        try:
            logger.info("Stopping tracking for finished games")

            # Find active trackers for finished games
            finished_trackers = (
                self.db.query(LiveGameTracker)
                .filter(LiveGameTracker.is_active == True, LiveGameTracker.status == "final")
                .all()
            )

            if not finished_trackers:
                logger.info("No finished games to stop tracking")
                return {"success": True, "games_stopped": 0, "message": "No finished games found"}

            results = {"success": True, "games_stopped": 0, "errors": []}

            for tracker in finished_trackers:
                try:
                    if self.live_game_service.stop_tracking_game(tracker.game_id):
                        results["games_stopped"] += 1
                        logger.info(f"Stopped tracking finished game {tracker.game_id}")
                    else:
                        error_msg = f"Failed to stop tracking game {tracker.game_id}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)

                except Exception as e:
                    error_msg = f"Error stopping tracking for game {tracker.game_id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(f"Finished game cleanup completed. Stopped tracking {results['games_stopped']} games")

            return results

        except Exception as e:
            logger.error(f"Critical error stopping finished games: {e}")
            return {"success": False, "error": str(e), "games_stopped": 0}


def run_live_game_updates():
    """Entry point for the live game update job."""
    job = LiveGameUpdateJob()
    return job.run_live_updates()


def setup_todays_game_tracking():
    """Entry point for setting up today's game tracking."""
    job = LiveGameUpdateJob()
    return job.start_tracking_todays_games()


def cleanup_old_live_data():
    """Entry point for cleaning up old live data."""
    job = LiveGameUpdateJob()
    return job.cleanup_old_trackers()


def stop_finished_game_tracking():
    """Entry point for stopping finished game tracking."""
    job = LiveGameUpdateJob()
    return job.stop_finished_games()
