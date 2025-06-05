"""
Tests for live game update jobs.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.jobs.live_game_updates import LiveGameUpdateJob
from app.models import Game, LiveGameTracker, WNBATeam


class TestLiveGameUpdateJob:
    """Test live game update job functionality."""

    def test_start_tracking_todays_games(self, db: Session):
        """Test setting up tracking for today's games."""
        # Create test teams
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        # Create today's games
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        game_today = Game(
            id="game_today",
            date=datetime.combine(today, datetime.min.time()),
            home_team_id=1,
            away_team_id=2,
            status="scheduled",
        )
        game_yesterday = Game(
            id="game_yesterday",
            date=datetime.combine(yesterday, datetime.min.time()),
            home_team_id=1,
            away_team_id=2,
            status="final",
        )
        game_tomorrow = Game(
            id="game_tomorrow",
            date=datetime.combine(tomorrow, datetime.min.time()),
            home_team_id=1,
            away_team_id=2,
            status="scheduled",
        )

        db.add_all([game_today, game_yesterday, game_tomorrow])
        db.commit()

        # Test job
        with patch('app.jobs.live_game_updates.get_db', return_value=iter([db])):
            job = LiveGameUpdateJob()
            job.db = db  # Override the db connection
            result = job.start_tracking_todays_games()

        assert result["success"] is True
        assert result["games_tracked"] == 1
        assert "game_today" in result["tracking_started"]

        # Verify tracker was created
        tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "game_today").first()

        assert tracker is not None
        assert tracker.is_active is True

    def test_start_tracking_no_games_today(self, db: Session):
        """Test setup when no games are scheduled today."""
        # Create a game for yesterday only
        yesterday = datetime.utcnow().date() - timedelta(days=1)

        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game = Game(
            id="game_yesterday",
            date=datetime.combine(yesterday, datetime.min.time()),
            home_team_id=1,
            away_team_id=2,
            status="final",
        )
        db.add(game)
        db.commit()

        # Test job
        with patch('app.jobs.live_game_updates.get_db', return_value=iter([db])):
            job = LiveGameUpdateJob()
            job.db = db
            result = job.start_tracking_todays_games()

        assert result["success"] is True
        assert result["games_tracked"] == 0
        assert "No games scheduled for today" in result["message"]

    @patch('app.jobs.live_game_updates.LiveGameService.update_live_game')
    def test_run_live_updates(self, mock_update, db: Session):
        """Test running live updates for active games."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game = Game(id="live_game", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="in_progress")
        db.add(game)

        now = datetime.utcnow()
        tracker = LiveGameTracker(
            game_id="live_game",
            game_date=now,
            status="in_progress",
            last_update=now - timedelta(minutes=5),
            next_update=now - timedelta(minutes=1),  # Needs update
            is_active=True,
        )
        db.add(tracker)
        db.commit()

        # Mock successful update
        mock_update.return_value = {
            "success": True,
            "game_id": "live_game",
            "status": "in_progress",
            "home_score": 25,
            "away_score": 22,
            "player_stats_updated": 5,
        }

        # Test job
        with patch('app.jobs.live_game_updates.get_db', return_value=iter([db])):
            job = LiveGameUpdateJob()
            job.db = db
            result = job.run_live_updates()

        assert result["success"] is True
        assert result["games_updated"] == 1
        assert result["games_processed"] == 1
        assert len(result["updates"]) == 1
        assert result["updates"][0]["game_id"] == "live_game"

        # Verify update was called
        mock_update.assert_called_once_with("live_game")

    def test_stop_finished_games(self, db: Session):
        """Test stopping tracking for finished games."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game1 = Game(id="finished_game", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="final")
        game2 = Game(id="active_game", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="in_progress")
        db.add_all([game1, game2])

        now = datetime.utcnow()

        # Finished game tracker (should be stopped)
        tracker1 = LiveGameTracker(
            game_id="finished_game",
            game_date=now,
            status="final",
            last_update=now,
            next_update=now + timedelta(minutes=5),
            is_active=True,
        )

        # Active game tracker (should remain active)
        tracker2 = LiveGameTracker(
            game_id="active_game",
            game_date=now,
            status="in_progress",
            last_update=now,
            next_update=now + timedelta(minutes=5),
            is_active=True,
        )

        db.add_all([tracker1, tracker2])
        db.commit()

        # Test job
        with patch('app.jobs.live_game_updates.get_db', return_value=iter([db])):
            job = LiveGameUpdateJob()
            job.db = db
            result = job.stop_finished_games()

        assert result["success"] is True
        assert result["games_stopped"] == 1

        # Verify finished game tracker was deactivated
        finished_tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "finished_game").first()
        assert finished_tracker.is_active is False

        # Verify active game tracker remains active
        active_tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "active_game").first()
        assert active_tracker.is_active is True

    def test_cleanup_old_trackers(self, db: Session):
        """Test cleaning up old game trackers."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        old_date = datetime.utcnow() - timedelta(days=8)
        recent_date = datetime.utcnow() - timedelta(days=1)

        game_old = Game(id="old_game", date=old_date, home_team_id=1, away_team_id=2, status="final")
        game_recent = Game(id="recent_game", date=recent_date, home_team_id=1, away_team_id=2, status="final")
        db.add_all([game_old, game_recent])

        # Old tracker (should be cleaned up)
        tracker_old = LiveGameTracker(
            game_id="old_game",
            game_date=old_date,
            status="final",
            last_update=old_date,
            next_update=old_date + timedelta(minutes=5),
            is_active=False,
        )

        # Recent tracker (should remain)
        tracker_recent = LiveGameTracker(
            game_id="recent_game",
            game_date=recent_date,
            status="final",
            last_update=recent_date,
            next_update=recent_date + timedelta(minutes=5),
            is_active=False,
        )

        db.add_all([tracker_old, tracker_recent])
        db.commit()

        # Test job
        with patch('app.jobs.live_game_updates.get_db', return_value=iter([db])):
            job = LiveGameUpdateJob()
            job.db = db
            result = job.cleanup_old_trackers(days_old=7)

        assert result["success"] is True
        assert result["trackers_removed"] == 1

        # Verify old tracker was removed
        old_tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "old_game").first()
        assert old_tracker is None

        # Verify recent tracker remains
        recent_tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "recent_game").first()
        assert recent_tracker is not None
