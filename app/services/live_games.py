"""
Live game tracking service for real-time game updates and fantasy point calculations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.external_apis.rapidapi_client import wnba_client
from app.models import Game, LiveGameTracker, LivePlayerStats, Player, RosterSlot, StatLine, Team, WNBATeam
from app.services.cache import CacheService

logger = logging.getLogger(__name__)


class LiveGameService:
    """Service for managing live game tracking and real-time updates."""

    def __init__(self, db: Session):
        self.db = db
        self.api_client = wnba_client
        self.cache_service = CacheService(db)

    def start_tracking_game(self, game_id: str) -> bool:
        """
        Start tracking a game for live updates.

        Args:
            game_id: ID of the game to track

        Returns:
            True if tracking started successfully
        """
        try:
            # Check if game exists
            game = self.db.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.error(f"Game {game_id} not found")
                return False

            # Check if already tracking
            existing = self.db.query(LiveGameTracker).filter(LiveGameTracker.game_id == game_id).first()

            if existing:
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
            else:
                # Create new tracker
                now = datetime.utcnow()
                tracker = LiveGameTracker(
                    game_id=game_id,
                    game_date=game.date,
                    status=game.status,
                    last_update=now,
                    next_update=now + timedelta(seconds=300),  # 5 minutes
                    home_score=game.home_score,
                    away_score=game.away_score,
                )
                self.db.add(tracker)

            self.db.commit()
            logger.info(f"Started tracking game {game_id}")
            return True

        except Exception as e:
            logger.error(f"Error starting tracking for game {game_id}: {e}")
            self.db.rollback()
            return False

    def stop_tracking_game(self, game_id: str) -> bool:
        """
        Stop tracking a game.

        Args:
            game_id: ID of the game to stop tracking

        Returns:
            True if stopped successfully
        """
        try:
            tracker = self.db.query(LiveGameTracker).filter(LiveGameTracker.game_id == game_id).first()

            if tracker:
                tracker.is_active = False
                tracker.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Stopped tracking game {game_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error stopping tracking for game {game_id}: {e}")
            self.db.rollback()
            return False

    def get_games_to_update(self) -> List[LiveGameTracker]:
        """
        Get list of games that need updates.

        Returns:
            List of game trackers that should be updated
        """
        now = datetime.utcnow()
        return (
            self.db.query(LiveGameTracker)
            .filter(
                and_(
                    LiveGameTracker.is_active == True,
                    LiveGameTracker.next_update <= now,
                    LiveGameTracker.status.in_(["scheduled", "in_progress"]),
                )
            )
            .all()
        )

    def update_live_game(self, game_id: str) -> Dict[str, Any]:
        """
        Update live game data from API.

        Args:
            game_id: ID of the game to update

        Returns:
            Dictionary with update results
        """
        try:
            tracker = self.db.query(LiveGameTracker).filter(LiveGameTracker.game_id == game_id).first()

            if not tracker:
                return {"success": False, "error": "Game tracker not found"}

            # Get live game data from API
            game_data = self._fetch_live_game_data(game_id)
            if not game_data:
                return {"success": False, "error": "Failed to fetch game data"}

            # Update tracker with latest info
            old_status = tracker.status
            tracker.status = game_data.get("status", tracker.status)
            tracker.quarter = game_data.get("quarter")
            tracker.time_remaining = game_data.get("time_remaining")
            tracker.home_score = game_data.get("home_score", tracker.home_score)
            tracker.away_score = game_data.get("away_score", tracker.away_score)
            tracker.last_update = datetime.utcnow()
            tracker.next_update = tracker.calculate_next_update()

            # Update live player stats
            player_stats_updated = 0
            if "player_stats" in game_data:
                player_stats_updated = self._update_live_player_stats(
                    game_id, game_data["player_stats"], tracker.status == "final"
                )

            # If game just finished, finalize stats
            if old_status != "final" and tracker.status == "final":
                self._finalize_game_stats(game_id)
                tracker.is_active = False

            self.db.commit()

            return {
                "success": True,
                "game_id": game_id,
                "status": tracker.status,
                "home_score": tracker.home_score,
                "away_score": tracker.away_score,
                "quarter": tracker.quarter,
                "time_remaining": tracker.time_remaining,
                "player_stats_updated": player_stats_updated,
                "next_update": tracker.next_update.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error updating live game {game_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_live_game_data(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current live game data.

        Args:
            game_id: ID of the game

        Returns:
            Live game data including scores and player stats
        """
        try:
            # Check cache first
            cache_key = self.cache_service.create_cache_key("live_game", game_id=game_id)
            cached_data = self.cache_service.get(cache_key)
            if cached_data:
                return cached_data

            tracker = self.db.query(LiveGameTracker).filter(LiveGameTracker.game_id == game_id).first()

            if not tracker:
                return None

            # Get live player stats
            live_stats = self.db.query(LivePlayerStats).filter(LivePlayerStats.game_id == game_id).all()

            # Get game info
            game = self.db.query(Game).filter(Game.id == game_id).first()
            if not game:
                return None

            data = {
                "game_id": game_id,
                "status": tracker.status,
                "quarter": tracker.quarter,
                "time_remaining": tracker.time_remaining,
                "last_update": tracker.last_update.isoformat(),
                "home_team": {
                    "id": game.home_team_id,
                    "name": game.home_team.name if game.home_team else "Unknown",
                    "score": tracker.home_score,
                },
                "away_team": {
                    "id": game.away_team_id,
                    "name": game.away_team.name if game.away_team else "Unknown",
                    "score": tracker.away_score,
                },
                "live_stats": [],
            }

            # Add player stats with fantasy points
            for stat in live_stats:
                player_data = {
                    "player_id": stat.player_id,
                    "player_name": stat.player.full_name if stat.player else "Unknown",
                    "position": stat.player.position if stat.player else None,
                    "team_abbr": stat.player.team_abbr if stat.player else None,
                    "minutes_played": stat.minutes_played,
                    "points": stat.points,
                    "rebounds": stat.rebounds,
                    "assists": stat.assists,
                    "steals": stat.steals,
                    "blocks": stat.blocks,
                    "turnovers": stat.turnovers,
                    "fantasy_points": stat.fantasy_points,
                    "is_final": stat.is_final,
                }
                data["live_stats"].append(player_data)

            # Cache for 30 seconds during live games, 5 minutes for final games
            ttl = 30 if tracker.status == "in_progress" else 300
            self.cache_service.set(cache_key, data, ttl, "live_game")

            return data

        except Exception as e:
            logger.error(f"Error getting live game data for {game_id}: {e}")
            return None

    def get_live_fantasy_scores(self, team_id: int) -> Dict[str, Any]:
        """
        Get live fantasy scores for a team based on current player performance.

        Args:
            team_id: ID of the fantasy team

        Returns:
            Live fantasy score data
        """
        try:
            # Get team's current roster
            roster_slots = self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id).all()

            total_fantasy_points = 0.0
            starter_points = 0.0
            player_scores = []

            for slot in roster_slots:
                # Get live stats for this player if they're playing today
                live_stat = (
                    self.db.query(LivePlayerStats)
                    .join(Game)
                    .filter(
                        and_(
                            LivePlayerStats.player_id == slot.player_id,
                            Game.date >= datetime.utcnow().date(),
                            Game.date < datetime.utcnow().date() + timedelta(days=1),
                        )
                    )
                    .first()
                )

                fantasy_points = 0.0
                if live_stat:
                    fantasy_points = live_stat.fantasy_points
                else:
                    # No live game, check if they played today in finished games
                    stat_line = (
                        self.db.query(StatLine)
                        .join(Game)
                        .filter(
                            and_(
                                StatLine.player_id == slot.player_id,
                                Game.date >= datetime.utcnow().date(),
                                Game.date < datetime.utcnow().date() + timedelta(days=1),
                                Game.status == "final",
                            )
                        )
                        .first()
                    )

                    if stat_line:
                        fantasy_points = stat_line.points

                player_scores.append(
                    {
                        "player_id": slot.player_id,
                        "player_name": slot.player.full_name if slot.player else "Unknown",
                        "position": slot.player.position if slot.player else None,
                        "is_starter": slot.is_starter,
                        "fantasy_points": fantasy_points,
                        "has_live_game": live_stat is not None,
                    }
                )

                total_fantasy_points += fantasy_points
                if slot.is_starter:
                    starter_points += fantasy_points

            return {
                "team_id": team_id,
                "total_fantasy_points": round(total_fantasy_points, 2),
                "starter_points": round(starter_points, 2),
                "player_scores": player_scores,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting live fantasy scores for team {team_id}: {e}")
            return {"error": str(e)}

    def _fetch_live_game_data(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Fetch live game data from external API."""
        try:
            # Use cache to avoid hitting API too frequently
            cache_key = f"api_live_game:{game_id}"
            cached = self.cache_service.get(cache_key)
            if cached:
                return cached

            # Fetch from API (implement based on your API structure)
            game_data = self.api_client.get_live_game_stats(game_id)

            if game_data:
                # Cache for 60 seconds
                self.cache_service.set(cache_key, game_data, 60, "live_game_api")

            return game_data

        except Exception as e:
            logger.error(f"Error fetching live game data for {game_id}: {e}")
            return None

    def _update_live_player_stats(self, game_id: str, player_stats_data: List[Dict], is_final: bool = False) -> int:
        """Update live player statistics."""
        updated_count = 0

        try:
            for player_data in player_stats_data:
                player_id = player_data.get("player_id")
                if not player_id:
                    continue

                # Get or create live stats entry
                live_stat = (
                    self.db.query(LivePlayerStats)
                    .filter(and_(LivePlayerStats.game_id == game_id, LivePlayerStats.player_id == player_id))
                    .first()
                )

                if not live_stat:
                    live_stat = LivePlayerStats(game_id=game_id, player_id=player_id)
                    self.db.add(live_stat)

                # Update stats
                live_stat.minutes_played = player_data.get("minutes_played", 0)
                live_stat.points = player_data.get("points", 0)
                live_stat.rebounds = player_data.get("rebounds", 0)
                live_stat.assists = player_data.get("assists", 0)
                live_stat.steals = player_data.get("steals", 0)
                live_stat.blocks = player_data.get("blocks", 0)
                live_stat.field_goals_made = player_data.get("field_goals_made", 0)
                live_stat.field_goals_attempted = player_data.get("field_goals_attempted", 0)
                live_stat.three_pointers_made = player_data.get("three_pointers_made", 0)
                live_stat.three_pointers_attempted = player_data.get("three_pointers_attempted", 0)
                live_stat.free_throws_made = player_data.get("free_throws_made", 0)
                live_stat.free_throws_attempted = player_data.get("free_throws_attempted", 0)
                live_stat.turnovers = player_data.get("turnovers", 0)
                live_stat.personal_fouls = player_data.get("personal_fouls", 0)
                live_stat.is_final = is_final
                live_stat.last_update = datetime.utcnow()

                # Calculate and update fantasy points
                live_stat.update_fantasy_points()

                updated_count += 1

            return updated_count

        except Exception as e:
            logger.error(f"Error updating live player stats for game {game_id}: {e}")
            return 0

    def _finalize_game_stats(self, game_id: str):
        """
        Finalize live stats by converting them to permanent StatLine entries.
        This only happens when a game is completely finished.
        """
        try:
            # Get all live stats for this game
            live_stats = self.db.query(LivePlayerStats).filter(LivePlayerStats.game_id == game_id).all()

            game = self.db.query(Game).filter(Game.id == game_id).first()
            if not game:
                return

            # Convert live stats to permanent StatLine entries
            for live_stat in live_stats:
                # Check if StatLine already exists
                existing_stat = (
                    self.db.query(StatLine)
                    .filter(and_(StatLine.game_id == game_id, StatLine.player_id == live_stat.player_id))
                    .first()
                )

                if existing_stat:
                    # Update existing StatLine with final stats
                    existing_stat.minutes_played = live_stat.minutes_played
                    existing_stat.points = live_stat.points
                    existing_stat.rebounds = live_stat.rebounds
                    existing_stat.assists = live_stat.assists
                    existing_stat.steals = live_stat.steals
                    existing_stat.blocks = live_stat.blocks
                    existing_stat.field_goals_made = live_stat.field_goals_made
                    existing_stat.field_goals_attempted = live_stat.field_goals_attempted
                    existing_stat.three_pointers_made = live_stat.three_pointers_made
                    existing_stat.three_pointers_attempted = live_stat.three_pointers_attempted
                    existing_stat.free_throws_made = live_stat.free_throws_made
                    existing_stat.free_throws_attempted = live_stat.free_throws_attempted
                    existing_stat.turnovers = live_stat.turnovers
                    existing_stat.personal_fouls = live_stat.personal_fouls
                else:
                    # Create new StatLine
                    stat_line = StatLine(
                        player_id=live_stat.player_id,
                        game_id=game_id,
                        game_date=game.date,
                        minutes_played=live_stat.minutes_played,
                        points=live_stat.points,
                        rebounds=live_stat.rebounds,
                        assists=live_stat.assists,
                        steals=live_stat.steals,
                        blocks=live_stat.blocks,
                        field_goals_made=live_stat.field_goals_made,
                        field_goals_attempted=live_stat.field_goals_attempted,
                        three_pointers_made=live_stat.three_pointers_made,
                        three_pointers_attempted=live_stat.three_pointers_attempted,
                        free_throws_made=live_stat.free_throws_made,
                        free_throws_attempted=live_stat.free_throws_attempted,
                        turnovers=live_stat.turnovers,
                        personal_fouls=live_stat.personal_fouls,
                    )
                    self.db.add(stat_line)

                # Mark live stat as final
                live_stat.is_final = True

            logger.info(f"Finalized stats for {len(live_stats)} players in game {game_id}")

        except Exception as e:
            logger.error(f"Error finalizing stats for game {game_id}: {e}")
