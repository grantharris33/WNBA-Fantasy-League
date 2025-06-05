"""Tests for the analytics system."""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models import (
    Player, StatLine, Game, WNBATeam,
    PlayerSeasonStats, PlayerTrends, MatchupAnalysis
)
from app.services.analytics import AnalyticsService


@pytest.fixture
def sample_player(db: Session):
    """Create a sample player for testing."""
    player = Player(
        id=1001,
        full_name="Test Player",
        position="G",
        team_abbr="TST"
    )
    db.add(player)
    db.flush()
    return player


@pytest.fixture
def sample_team(db: Session):
    """Create a sample WNBA team for testing."""
    team = WNBATeam(
        id=101,
        name="Test Team",
        location="Test City",
        abbreviation="TST",
        display_name="Test City Test Team"
    )
    db.add(team)
    db.flush()
    return team


@pytest.fixture
def sample_games_and_stats(db: Session, sample_player, sample_team):
    """Create sample games and stat lines for testing."""
    games = []
    stats = []

    # Create 10 games with varying stats
    for i in range(10):
        game_date = datetime.now() - timedelta(days=i)
        game = Game(
            id=f"game_{i}",
            date=game_date,
            home_team_id=sample_team.id,
            away_team_id=sample_team.id,
            home_score=80 + i,
            away_score=75 + i,
            status="final"
        )
        games.append(game)
        db.add(game)

        # Create stat line with varying performance
        stat = StatLine(
            player_id=sample_player.id,
            game_id=game.id,
            game_date=game_date,
            points=20.0 + (i % 3) * 5,  # 20, 25, 30, 20, 25...
            rebounds=8.0 + (i % 2) * 2,  # 8, 10, 8, 10...
            assists=5.0 + (i % 2),       # 5, 6, 5, 6...
            steals=2.0,
            blocks=1.0,
            minutes_played=30.0 + i % 5,
            field_goals_made=8 + i % 3,
            field_goals_attempted=16,
            three_pointers_made=2,
            three_pointers_attempted=5,
            free_throws_made=4,
            free_throws_attempted=5,
            turnovers=3,
            is_starter=True,
            did_not_play=False,
            team_id=sample_team.id,
            opponent_id=sample_team.id,
            is_home_game=True
        )
        stats.append(stat)
        db.add(stat)

    db.flush()
    return games, stats


def test_calculate_player_efficiency_rating(db: Session, sample_player, sample_games_and_stats):
    """Test PER calculation."""
    analytics_service = AnalyticsService(db)

    # Flush to ensure all data is available in this transaction
    db.flush()
    
    per = analytics_service.calculate_player_efficiency_rating(
        sample_player.id,
        datetime.now().year
    )

    assert per > 0
    # PER should be reasonable for the given stats
    assert 10 < per < 35


def test_calculate_true_shooting_percentage(db: Session):
    """Test true shooting percentage calculation."""
    analytics_service = AnalyticsService(db)

    player_stats = {
        'points': 25,
        'field_goals_attempted': 15,
        'free_throws_attempted': 5
    }

    ts_pct = analytics_service.calculate_true_shooting_percentage(player_stats)

    # TS% = 25 / (2 * (15 + 0.44 * 5)) = 25 / 34.4 = 72.67%
    assert 72 < ts_pct < 73


def test_calculate_fantasy_consistency(db: Session, sample_player, sample_games_and_stats):
    """Test fantasy consistency score calculation."""
    analytics_service = AnalyticsService(db)

    # Flush to ensure all data is available in this transaction
    db.flush()

    consistency = analytics_service.calculate_fantasy_consistency(sample_player.id, games=5)

    assert consistency >= 0
    # Should have some variance given the varying stats
    assert consistency > 0


def test_identify_hot_cold_streaks(db: Session, sample_player, sample_games_and_stats):
    """Test hot/cold streak identification."""
    analytics_service = AnalyticsService(db)

    # First update season stats to have a baseline
    analytics_service.update_player_season_stats(sample_player.id, datetime.now().year)

    streak_info = analytics_service.identify_hot_cold_streaks(sample_player.id)

    assert isinstance(streak_info, dict)
    assert 'is_hot' in streak_info
    assert 'is_cold' in streak_info
    assert 'streak_games' in streak_info


def test_update_player_season_stats(db: Session, sample_player, sample_games_and_stats):
    """Test updating player season statistics."""
    analytics_service = AnalyticsService(db)

    # Flush to ensure all data is available in this transaction
    db.flush()

    season_stats = analytics_service.update_player_season_stats(
        sample_player.id,
        datetime.now().year
    )

    assert season_stats is not None
    assert season_stats.player_id == sample_player.id
    assert season_stats.games_played == 10
    assert season_stats.ppg > 0
    assert season_stats.rpg > 0
    assert season_stats.apg > 0
    assert season_stats.fantasy_ppg > 0
    assert season_stats.per > 0
    assert season_stats.true_shooting_percentage > 0


def test_update_player_trends(db: Session, sample_player, sample_games_and_stats):
    """Test updating player trends."""
    analytics_service = AnalyticsService(db)

    # Flush to ensure all data is available in this transaction
    db.flush()

    trends = analytics_service.update_player_trends(sample_player.id)

    assert trends is not None
    assert trends.player_id == sample_player.id
    assert trends.last_5_games_ppg > 0
    assert trends.last_10_games_ppg > 0
    assert trends.last_5_games_fantasy > 0


def test_project_fantasy_points(db: Session, sample_player, sample_team, sample_games_and_stats):
    """Test fantasy point projection."""
    analytics_service = AnalyticsService(db)

    # Flush to ensure all data is available in this transaction
    db.flush()

    # First calculate season stats
    analytics_service.update_player_season_stats(sample_player.id, datetime.now().year)

    projection = analytics_service.project_fantasy_points(
        sample_player.id,
        sample_team.id
    )

    assert projection > 0
    # Projection should be reasonable based on the sample data
    assert 20 < projection < 60


def test_analytics_api_endpoints(client, db: Session, sample_player, sample_games_and_stats):
    """Test analytics API endpoints."""
    # Flush to ensure all data is available in this transaction
    db.flush()
    
    # Test get player analytics
    response = client.get(f"/api/v1/players/{sample_player.id}/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data['player_id'] == sample_player.id
    assert data['ppg'] > 0

    # Test get player trends
    response = client.get(f"/api/v1/players/{sample_player.id}/trends")
    assert response.status_code == 200
    data = response.json()
    assert data['player_id'] == sample_player.id
    assert 'last_5_games_ppg' in data

    # Test trigger calculation
    response = client.post(f"/api/v1/analytics/calculate?player_id={sample_player.id}")
    assert response.status_code == 200