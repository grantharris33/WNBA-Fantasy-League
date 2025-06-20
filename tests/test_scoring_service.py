from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

import pytest

from app.services.scoring import compute_fantasy_points, update_weekly_team_scores

# ---------------------------------------------------------------------------
# 4-A – compute_fantasy_points
# ---------------------------------------------------------------------------


def test_compute_fantasy_points_basic():
    sample = {"points": 10, "rebounds": 5, "assists": 4, "steals": 2, "blocks": 1}
    # Formula: 10*1 + 5*1.2 + 4*1.5 + 2*3 + 1*3 = 31
    assert compute_fantasy_points(sample) == 31.0


def test_compute_fantasy_points_triple_double():
    # Triple-double edge case – bonus applied
    sample = {"points": 10, "rebounds": 10, "assists": 10, "steals": 0, "blocks": 0}
    base = 10 * 1 + 10 * 1.2 + 10 * 1.5  # 37
    assert compute_fantasy_points(sample) == base + 10  # 47


# ---------------------------------------------------------------------------
# 4-B – update_weekly_team_scores
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_weekly_team_scores(monkeypatch, tmp_path: Path):
    # Isolate DB
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("TESTING", "true")

    from app import models
    from app.core import database as db

    db.init_db()
    session = db.SessionLocal()

    # Create two teams and players
    league = models.League(name="L1", invite_code="TEST123")
    t1 = models.Team(name="A", league=league)
    t2 = models.Team(name="B", league=league)
    # Use high primary-key values to avoid clashing with earlier tests that
    # may have inserted id=1,2 via the ingest fixtures.
    p1 = models.Player(full_name="P1")
    p2 = models.Player(full_name="P2")

    session.add_all([league, t1, t2, p1, p2])
    session.flush()  # assign PKs

    # Roster slots (mark as starters)
    session.add_all(
        [
            models.RosterSlot(team_id=t1.id, player_id=p1.id, is_starter=True),
            models.RosterSlot(team_id=t2.id, player_id=p2.id, is_starter=True),
        ]
    )

    # Stat lines on same week (use current date to ensure it's treated as current week)
    today = dt.date.today()
    # Find the Monday of this week
    monday = today - dt.timedelta(days=today.weekday())
    game_dt = dt.datetime.combine(monday, dt.time())

    # Create a game first
    game = models.Game(id="test-game-1", date=game_dt)
    session.add(game)
    session.flush()
    sl1 = models.StatLine(
        player_id=p1.id, game_id=game.id, game_date=game_dt, points=10, rebounds=5, assists=0, steals=0, blocks=0
    )
    sl2 = models.StatLine(
        player_id=p2.id, game_id=game.id, game_date=game_dt, points=5, rebounds=5, assists=5, steals=0, blocks=0
    )
    session.add_all([sl1, sl2])
    session.commit()

    # Store IDs before closing the session
    team1_id = t1.id
    team2_id = t2.id

    # Run aggregation with the same session
    update_weekly_team_scores(monday, session=session)

    session.close()

    session2 = db.SessionLocal()
    rows = session2.query(models.TeamScore).all()

    # Debug: check if any scores were created
    print(f"Found {len(rows)} team scores")
    for row in rows:
        print(f"Team {row.team_id}: {row.score} (week {row.week})")

    # Check if stat lines exist
    stat_lines = session2.query(models.StatLine).all()
    print(f"Found {len(stat_lines)} stat lines")

    # Check if roster slots exist with starters
    roster_slots = session2.query(models.RosterSlot).filter(models.RosterSlot.is_starter is True).all()
    print(f"Found {len(roster_slots)} starter roster slots")

    assert len(rows) == 2

    scores = {r.team_id: r.score for r in rows}
    # Expected formulas: t1: 10 + 5*1.2 = 16.0, t2: 5 + 5*1.2 + 5*1.5 = 5 + 6 + 7.5 = 18.5
    assert scores[team1_id] == 16.0
    assert scores[team2_id] == 18.5
    session2.close()
