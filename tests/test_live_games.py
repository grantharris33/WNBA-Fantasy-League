"""
Tests for live game tracking functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models import Game, LiveGameTracker, LivePlayerStats, Player, WNBATeam
from app.services.cache import CacheService
from app.services.live_games import LiveGameService


class TestLiveGameService:
    """Test live game service functionality."""

    def test_start_tracking_game(self, db: Session):
        """Test starting tracking for a game."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game = Game(id="test_game_1", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="scheduled")
        db.add(game)
        db.commit()

        # Test starting tracking
        service = LiveGameService(db)
        result = service.start_tracking_game("test_game_1")

        assert result is True

        # Verify tracker was created
        tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "test_game_1").first()

        assert tracker is not None
        assert tracker.game_id == "test_game_1"
        assert tracker.status == "scheduled"
        assert tracker.is_active is True

    def test_start_tracking_nonexistent_game(self, db: Session):
        """Test starting tracking for a non-existent game."""
        service = LiveGameService(db)
        result = service.start_tracking_game("nonexistent_game")

        assert result is False

    def test_stop_tracking_game(self, db: Session):
        """Test stopping tracking for a game."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game = Game(id="test_game_2", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="scheduled")
        db.add(game)

        now = datetime.utcnow()
        tracker = LiveGameTracker(
            game_id="test_game_2",
            game_date=now,
            status="in_progress",
            last_update=now,
            next_update=now + timedelta(minutes=5),
            is_active=True,
        )
        db.add(tracker)
        db.commit()

        # Test stopping tracking
        service = LiveGameService(db)
        result = service.stop_tracking_game("test_game_2")

        assert result is True

        # Verify tracker was deactivated
        tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "test_game_2").first()

        assert tracker is not None
        assert tracker.is_active is False

    def test_get_games_to_update(self, db: Session):
        """Test getting games that need updates."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game1 = Game(
            id="game_needs_update", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="in_progress"
        )
        game2 = Game(id="game_no_update", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="final")
        db.add_all([game1, game2])

        now = datetime.utcnow()

        # Game that needs update (next_update is in the past)
        tracker1 = LiveGameTracker(
            game_id="game_needs_update",
            game_date=now,
            status="in_progress",
            last_update=now - timedelta(minutes=10),
            next_update=now - timedelta(minutes=5),
            is_active=True,
        )

        # Game that doesn't need update (next_update is in the future)
        tracker2 = LiveGameTracker(
            game_id="game_no_update",
            game_date=now,
            status="final",
            last_update=now,
            next_update=now + timedelta(minutes=5),
            is_active=True,
        )

        db.add_all([tracker1, tracker2])
        db.commit()

        # Test getting games to update
        service = LiveGameService(db)
        games_to_update = service.get_games_to_update()

        assert len(games_to_update) == 1
        assert games_to_update[0].game_id == "game_needs_update"

    @patch('app.services.live_games.LiveGameService._fetch_live_game_data')
    def test_update_live_game(self, mock_fetch, db: Session):
        """Test updating live game data."""
        # Create test data
        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        away_team = WNBATeam(id=2, name="Team B", location="City B", abbreviation="TB", display_name="City B Team B")
        db.add_all([home_team, away_team])

        game = Game(id="test_update_game", date=datetime.utcnow(), home_team_id=1, away_team_id=2, status="in_progress")
        db.add(game)

        now = datetime.utcnow()
        tracker = LiveGameTracker(
            game_id="test_update_game",
            game_date=now,
            status="in_progress",
            last_update=now - timedelta(minutes=5),
            next_update=now - timedelta(minutes=2),
            home_score=10,
            away_score=8,
            quarter=2,
            time_remaining="8:45",
            is_active=True,
        )
        db.add(tracker)
        db.commit()

        # Mock API response
        mock_fetch.return_value = {
            "status": "in_progress",
            "quarter": 2,
            "time_remaining": "7:30",
            "home_score": 12,
            "away_score": 10,
            "player_stats": [],
        }

        # Test updating game
        service = LiveGameService(db)
        result = service.update_live_game("test_update_game")

        assert result["success"] is True
        assert result["home_score"] == 12
        assert result["away_score"] == 10
        assert result["time_remaining"] == "7:30"

        # Verify tracker was updated
        updated_tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == "test_update_game").first()

        assert updated_tracker.home_score == 12
        assert updated_tracker.away_score == 10
        assert updated_tracker.time_remaining == "7:30"

    def test_fantasy_points_calculation(self, db: Session):
        """Test fantasy points calculation for live stats."""
        # Create test data
        player = Player(id=1, full_name="Test Player", position="G", team_abbr="TA")
        db.add(player)

        home_team = WNBATeam(id=1, name="Team A", location="City A", abbreviation="TA", display_name="City A Team A")
        db.add(home_team)

        game = Game(
            id="fantasy_test_game", date=datetime.utcnow(), home_team_id=1, away_team_id=1, status="in_progress"
        )
        db.add(game)

        # Create live stats
        live_stat = LivePlayerStats(
            game_id="fantasy_test_game", player_id=1, points=20, rebounds=8, assists=5, steals=2, blocks=1, turnovers=3
        )
        db.add(live_stat)
        db.commit()

        # Calculate fantasy points
        live_stat.update_fantasy_points()

        # Expected: 20*1.0 + 8*1.2 + 5*1.5 + 2*3.0 + 1*3.0 + 3*(-1.0) = 20 + 9.6 + 7.5 + 6 + 3 - 3 = 43.1
        expected_points = 43.1
        assert abs(live_stat.fantasy_points - expected_points) < 0.01


class TestCacheService:
    """Test cache service functionality."""

    def test_cache_set_and_get(self, db: Session):
        """Test setting and getting cache data."""
        cache_service = CacheService(db)

        test_data = {"key": "value", "number": 123}

        # Test setting cache
        result = cache_service.set("test_key", test_data, ttl_seconds=300)
        assert result is True

        # Test getting cache
        cached_data = cache_service.get("test_key")
        assert cached_data == test_data

    def test_cache_expiration(self, db: Session):
        """Test cache expiration."""
        cache_service = CacheService(db)

        test_data = {"key": "value"}

        # Set cache with very short TTL
        cache_service.set("expire_test", test_data, ttl_seconds=1)

        # Should be available immediately
        cached_data = cache_service.get("expire_test")
        assert cached_data == test_data

        # Manually set expiration to past
        from app.models import ApiCache

        cache_entry = db.query(ApiCache).filter(ApiCache.cache_key == "expire_test").first()
        cache_entry.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

        # Should return None after expiration
        cached_data = cache_service.get("expire_test")
        assert cached_data is None

    def test_cache_delete(self, db: Session):
        """Test cache deletion."""
        cache_service = CacheService(db)

        test_data = {"key": "value"}
        cache_service.set("delete_test", test_data)

        # Verify it exists
        cached_data = cache_service.get("delete_test")
        assert cached_data == test_data

        # Delete it
        result = cache_service.delete("delete_test")
        assert result is True

        # Verify it's gone
        cached_data = cache_service.get("delete_test")
        assert cached_data is None

    def test_clear_expired_entries(self, db: Session):
        """Test clearing expired cache entries."""
        cache_service = CacheService(db)

        # Add some test entries
        cache_service.set("active_key", {"data": "active"}, ttl_seconds=3600)
        cache_service.set("expired_key", {"data": "expired"}, ttl_seconds=1)

        # Manually expire one entry
        from app.models import ApiCache

        expired_entry = db.query(ApiCache).filter(ApiCache.cache_key == "expired_key").first()
        expired_entry.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

        # Clear expired entries
        cleared_count = cache_service.clear_expired()
        assert cleared_count == 1

        # Verify active entry still exists
        cached_data = cache_service.get("active_key")
        assert cached_data is not None

        # Verify expired entry is gone
        cached_data = cache_service.get("expired_key")
        assert cached_data is None

    def test_cache_key_generation(self, db: Session):
        """Test cache key generation."""
        cache_service = CacheService(db)

        # Test with parameters
        key1 = cache_service.create_cache_key("test_endpoint", param1="value1", param2="value2")
        key2 = cache_service.create_cache_key("test_endpoint", param2="value2", param1="value1")

        # Should be the same regardless of parameter order
        assert key1 == key2
        assert "param1=value1" in key1
        assert "param2=value2" in key1

        # Test without parameters
        key3 = cache_service.create_cache_key("simple_endpoint")
        assert key3 == "simple_endpoint"
