"""Tests for the weekly bonus calculator service."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from sqlalchemy.orm import Session

from app.models import Player, RosterSlot, StatLine, Team, WeeklyBonus
from app.services.bonus import calculate_weekly_bonuses


@pytest.fixture
def test_data(db: Session) -> None:
    """
    Set up test data for bonus calculator tests.

    Creates:
    - 3 Teams
    - 5 Players (assigned to teams)
    - StatLines for a specific week with known values
    """
    # Create teams
    teams = [Team(id=1, name="Team A"), Team(id=2, name="Team B"), Team(id=3, name="Team C")]
    db.add_all(teams)

    # Create players
    players = [
        Player(id=101, full_name="Player 1", position="G"),
        Player(id=102, full_name="Player 2", position="F"),
        Player(id=103, full_name="Player 3", position="C"),
        Player(id=104, full_name="Player 4", position="G"),
        Player(id=105, full_name="Player 5", position="F"),
    ]
    db.add_all(players)

    # Create roster slots (assign players to teams)
    roster_slots = [
        RosterSlot(team_id=1, player_id=101, position="G"),
        RosterSlot(team_id=1, player_id=102, position="F"),
        RosterSlot(team_id=2, player_id=103, position="C"),
        RosterSlot(team_id=2, player_id=104, position="G"),
        RosterSlot(team_id=3, player_id=105, position="F"),
    ]
    db.add_all(roster_slots)

    # Create stat lines for a specific week (2023-05-01 to 2023-05-07)
    # This is the week we'll freeze time to for testing

    # Player 1: Top scorer, top playmaker
    p1_stats = [
        StatLine(
            player_id=101,
            game_id="test_game_1",
            game_date=datetime(2023, 5, 2, 18, 0),
            points=30.0,
            rebounds=5.0,
            assists=12.0,
            steals=2.0,
            blocks=1.0,
        ),
        StatLine(
            player_id=101,
            game_id="test_game_2",
            game_date=datetime(2023, 5, 5, 18, 0),
            points=25.0,
            rebounds=4.0,
            assists=10.0,
            steals=1.0,
            blocks=0.0,
        ),
    ]

    # Player 2: Top rebounder, double-double streak
    p2_stats = [
        StatLine(
            player_id=102,
            game_id="test_game_3",
            game_date=datetime(2023, 5, 1, 18, 0),
            points=15.0,
            rebounds=15.0,
            assists=2.0,
            steals=1.0,
            blocks=1.0,
        ),
        StatLine(
            player_id=102,
            game_id="test_game_4",
            game_date=datetime(2023, 5, 4, 18, 0),
            points=12.0,
            rebounds=18.0,
            assists=3.0,
            steals=0.0,
            blocks=1.0,
        ),
    ]

    # Player 3: Defensive beast (tied with Player 5), triple-double
    p3_stats = [
        StatLine(
            player_id=103,
            game_id="test_game_5",
            game_date=datetime(2023, 5, 3, 18, 0),
            points=22.0,
            rebounds=12.0,
            assists=10.0,
            steals=3.0,
            blocks=2.0,
        )
    ]

    # Player 4: Average performance
    p4_stats = [
        StatLine(
            player_id=104,
            game_id="test_game_6",
            game_date=datetime(2023, 5, 2, 18, 0),
            points=18.0,
            rebounds=3.0,
            assists=8.0,
            steals=1.0,
            blocks=0.0,
        )
    ]

    # Player 5: Defensive beast (tied with Player 3)
    p5_stats = [
        StatLine(
            player_id=105,
            game_id="test_game_7",
            game_date=datetime(2023, 5, 6, 18, 0),
            points=10.0,
            rebounds=8.0,
            assists=5.0,
            steals=3.0,
            blocks=2.0,
        )
    ]

    all_stats = p1_stats + p2_stats + p3_stats + p4_stats + p5_stats
    db.add_all(all_stats)
    db.commit()


@freeze_time("2023-05-07 23:59:59")  # Sunday
def test_calculate_weekly_bonuses(db: Session, test_data) -> None:
    """Test the weekly bonus calculator with a frozen time at the end of a week."""
    # Run the bonus calculator
    calculate_weekly_bonuses(session=db)

    # Get the calculated bonuses
    bonuses = db.query(WeeklyBonus).all()

    # Convert to easy-to-check dictionary
    bonus_dict = {}
    for bonus in bonuses:
        key = (bonus.player_id, bonus.category)
        bonus_dict[key] = bonus.points

    # Output the actual bonuses for debugging
    print("Actual bonuses:", bonus_dict)

    # Check that bonuses were created
    assert len(bonus_dict) > 0

    # Check Player 1 (top scorer and top playmaker)
    assert bonus_dict.get((101, "top_scorer")) == 5.0
    assert bonus_dict.get((101, "top_playmaker")) == 4.0

    # Check Player 2 (top rebounder and double-double streak)
    assert bonus_dict.get((102, "top_rebounder")) == 4.0
    assert bonus_dict.get((102, "double_double_streak")) == 5.0

    # Check Player 3 (defensive beast and triple-double)
    assert bonus_dict.get((103, "defensive_beast")) == 4.0
    assert bonus_dict.get((103, "triple_double")) == 10.0

    # Player 1 may also get a double-double streak
    # Player 5 may also get a defensive beast (tie)


@freeze_time("2023-05-07 23:59:59")  # Sunday
def test_calculate_weekly_bonuses_idempotency(db: Session, test_data) -> None:
    """Test that running the calculator multiple times doesn't create duplicate bonuses."""
    # Run it once
    calculate_weekly_bonuses(session=db)
    first_count = db.query(WeeklyBonus).count()

    # Run it again
    calculate_weekly_bonuses(session=db)
    second_count = db.query(WeeklyBonus).count()

    # The counts should be the same (no duplicates)
    assert first_count == second_count
    assert first_count > 0  # Sanity check that bonuses were created
