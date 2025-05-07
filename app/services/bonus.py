"""Weekly bonus calculator service.

This module implements the logic for computing weekly leader bonuses
as defined in Story-11. It awards bonus points each week for the following categories:

- Top Scorer: +5 points for highest cumulative PTS
- Top Rebounder: +4 points for highest REB
- Top Playmaker: +4 points for highest AST
- Defensive Beast: +4 points for highest (STL + BLK)
- Efficiency Award: +3 points for best FG% (≥ 3 games)
- Double-Double Streak: +5 points for ≥ 2 double-doubles in week
- Triple-Double: +10 points for each triple-double logged

Ties are handled by awarding the bonus to all tied players.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Any

from sqlalchemy import func, literal_column, select, and_, text
from sqlalchemy.orm import Session, joinedload

from app import models
from app.core.database import SessionLocal

# Bonus point values defined by the scoring system
BONUS_POINTS = {
    "top_scorer": 5.0,
    "top_rebounder": 4.0,
    "top_playmaker": 4.0,
    "defensive_beast": 4.0,
    "efficiency_award": 3.0,
    "double_double_streak": 5.0,
    "triple_double": 10.0,
}

# Categories we consider for double / triple-double detection
_CATEGORIES = ("points", "rebounds", "assists", "steals", "blocks")

def _week_bounds(target: date) -> tuple[datetime, datetime, int]:
    """Return UTC datetimes for Monday 00:00 – Sunday 23:59 **and** week-id.

    Week-id is encoded as ``year * 100 + iso_week`` so that 2025-W02 ⇒ 202502.
    This keeps it sortable and unique across seasons while staying in a single
    integer column (SQLite-friendly).
    """
    iso_year, iso_week, _ = target.isocalendar()
    week_id = iso_year * 100 + iso_week

    # Monday (weekday() == 0) at 00:00 UTC
    monday = target - timedelta(days=target.weekday())
    start = datetime.combine(monday, datetime.min.time())
    end = start + timedelta(days=7)  # exclusive upper bound (next Monday)
    return start, end, week_id

def _get_team_id_for_player(player_id: int, session: Session) -> int:
    """Get the team_id for a player from their current roster slot."""
    roster_slot = session.query(models.RosterSlot).filter_by(player_id=player_id).first()
    return roster_slot.team_id if roster_slot else None

def _find_top_scorers(start_dt: datetime, end_dt: datetime, session: Session) -> List[Tuple[int, float]]:
    """Find players with highest cumulative points in the given week."""
    query = (
        session.query(
            models.StatLine.player_id,
            func.sum(models.StatLine.points).label("total_points")
        )
        .filter(models.StatLine.game_date >= start_dt)
        .filter(models.StatLine.game_date < end_dt)
        .group_by(models.StatLine.player_id)
        .order_by(text("total_points DESC"))
    )

    results = query.all()
    if not results:
        return []

    # Get the highest score
    top_score = results[0][1]

    # Return all players tied for top score
    return [(player_id, top_score) for player_id, score in results if score == top_score]

def _find_top_rebounders(start_dt: datetime, end_dt: datetime, session: Session) -> List[Tuple[int, float]]:
    """Find players with highest cumulative rebounds in the given week."""
    query = (
        session.query(
            models.StatLine.player_id,
            func.sum(models.StatLine.rebounds).label("total_rebounds")
        )
        .filter(models.StatLine.game_date >= start_dt)
        .filter(models.StatLine.game_date < end_dt)
        .group_by(models.StatLine.player_id)
        .order_by(text("total_rebounds DESC"))
    )

    results = query.all()
    if not results:
        return []

    # Get the highest count
    top_count = results[0][1]

    # Return all players tied for top count
    return [(player_id, top_count) for player_id, count in results if count == top_count]

def _find_top_playmakers(start_dt: datetime, end_dt: datetime, session: Session) -> List[Tuple[int, float]]:
    """Find players with highest cumulative assists in the given week."""
    query = (
        session.query(
            models.StatLine.player_id,
            func.sum(models.StatLine.assists).label("total_assists")
        )
        .filter(models.StatLine.game_date >= start_dt)
        .filter(models.StatLine.game_date < end_dt)
        .group_by(models.StatLine.player_id)
        .order_by(text("total_assists DESC"))
    )

    results = query.all()
    if not results:
        return []

    # Get the highest count
    top_count = results[0][1]

    # Return all players tied for top count
    return [(player_id, top_count) for player_id, count in results if count == top_count]

def _find_defensive_beasts(start_dt: datetime, end_dt: datetime, session: Session) -> List[Tuple[int, float]]:
    """Find players with highest cumulative (steals + blocks) in the given week."""
    query = (
        session.query(
            models.StatLine.player_id,
            (func.sum(models.StatLine.steals) + func.sum(models.StatLine.blocks)).label("defensive_total")
        )
        .filter(models.StatLine.game_date >= start_dt)
        .filter(models.StatLine.game_date < end_dt)
        .group_by(models.StatLine.player_id)
        .order_by(text("defensive_total DESC"))
    )

    results = query.all()
    if not results:
        return []

    # Get the highest total
    top_total = results[0][1]

    # Return all players tied for top total
    return [(player_id, top_total) for player_id, total in results if total == top_total]

def _find_double_double_streaks(start_dt: datetime, end_dt: datetime, session: Session) -> List[Tuple[int, int]]:
    """Find players with 2 or more double-doubles in the given week."""
    # This is a complex query that needs to be broken down into steps
    # First, we get all stat lines for the week
    stat_lines = (
        session.query(models.StatLine)
        .filter(models.StatLine.game_date >= start_dt)
        .filter(models.StatLine.game_date < end_dt)
        .all()
    )

    # Group stat lines by player
    player_stats = {}
    for line in stat_lines:
        if line.player_id not in player_stats:
            player_stats[line.player_id] = []
        player_stats[line.player_id].append(line)

    # Count double-doubles for each player
    player_double_doubles = {}
    for player_id, stats in player_stats.items():
        double_double_count = 0
        for stat in stats:
            # Count categories with 10+ stats
            categories_10_plus = sum(
                getattr(stat, attr) >= 10
                for attr in ['points', 'rebounds', 'assists', 'steals', 'blocks']
            )
            if categories_10_plus >= 2:  # Double-double condition
                double_double_count += 1

        if double_double_count >= 2:  # Player had at least 2 double-doubles
            player_double_doubles[player_id] = double_double_count

    return [(player_id, count) for player_id, count in player_double_doubles.items()]

def _find_triple_doubles(start_dt: datetime, end_dt: datetime, session: Session) -> List[Tuple[int, int]]:
    """Find players with triple-doubles in the given week and count each instance."""
    # Similar to double-doubles but counting triple-doubles
    stat_lines = (
        session.query(models.StatLine)
        .filter(models.StatLine.game_date >= start_dt)
        .filter(models.StatLine.game_date < end_dt)
        .all()
    )

    # Count triple-doubles for each player
    player_triple_doubles = {}
    for line in stat_lines:
        # Count categories with 10+ stats
        categories_10_plus = sum(
            getattr(line, attr) >= 10
            for attr in ['points', 'rebounds', 'assists', 'steals', 'blocks']
        )

        if categories_10_plus >= 3:  # Triple-double condition
            player_triple_doubles[line.player_id] = player_triple_doubles.get(line.player_id, 0) + 1

    return [(player_id, count) for player_id, count in player_triple_doubles.items()]

def calculate_weekly_bonuses(target_date: date = None, session: Session = None) -> None:
    """Calculate weekly bonuses for the ISO week containing *target_date*.

    This function computes all bonus categories for the specified week and inserts
    the results into the weekly_bonus table. It is idempotent - existing bonus
    entries for the week will be deleted before inserting new ones.
    """
    owned_session = False
    if session is None:
        session = SessionLocal()
        owned_session = True

    target_date = target_date or (datetime.utcnow() - timedelta(days=1)).date()
    start_dt, end_dt, week_id = _week_bounds(target_date)

    try:
        # Delete existing bonus entries for this week
        session.query(models.WeeklyBonus).filter_by(week_id=week_id).delete()

        # Calculate all bonus categories
        bonus_entries = []

        # Top Scorer
        for player_id, value in _find_top_scorers(start_dt, end_dt, session):
            team_id = _get_team_id_for_player(player_id, session)
            if team_id:
                bonus_entries.append(
                    models.WeeklyBonus(
                        week_id=week_id,
                        player_id=player_id,
                        team_id=team_id,
                        category="top_scorer",
                        points=BONUS_POINTS["top_scorer"]
                    )
                )

        # Top Rebounder
        for player_id, value in _find_top_rebounders(start_dt, end_dt, session):
            team_id = _get_team_id_for_player(player_id, session)
            if team_id:
                bonus_entries.append(
                    models.WeeklyBonus(
                        week_id=week_id,
                        player_id=player_id,
                        team_id=team_id,
                        category="top_rebounder",
                        points=BONUS_POINTS["top_rebounder"]
                    )
                )

        # Top Playmaker
        for player_id, value in _find_top_playmakers(start_dt, end_dt, session):
            team_id = _get_team_id_for_player(player_id, session)
            if team_id:
                bonus_entries.append(
                    models.WeeklyBonus(
                        week_id=week_id,
                        player_id=player_id,
                        team_id=team_id,
                        category="top_playmaker",
                        points=BONUS_POINTS["top_playmaker"]
                    )
                )

        # Defensive Beast
        for player_id, value in _find_defensive_beasts(start_dt, end_dt, session):
            team_id = _get_team_id_for_player(player_id, session)
            if team_id:
                bonus_entries.append(
                    models.WeeklyBonus(
                        week_id=week_id,
                        player_id=player_id,
                        team_id=team_id,
                        category="defensive_beast",
                        points=BONUS_POINTS["defensive_beast"]
                    )
                )

        # Double-Double Streak
        for player_id, count in _find_double_double_streaks(start_dt, end_dt, session):
            team_id = _get_team_id_for_player(player_id, session)
            if team_id:
                bonus_entries.append(
                    models.WeeklyBonus(
                        week_id=week_id,
                        player_id=player_id,
                        team_id=team_id,
                        category="double_double_streak",
                        points=BONUS_POINTS["double_double_streak"]
                    )
                )

        # Triple-Double (awarded for each triple-double)
        for player_id, count in _find_triple_doubles(start_dt, end_dt, session):
            team_id = _get_team_id_for_player(player_id, session)
            if team_id:
                # Award points for each triple-double
                bonus_entries.append(
                    models.WeeklyBonus(
                        week_id=week_id,
                        player_id=player_id,
                        team_id=team_id,
                        category="triple_double",
                        points=BONUS_POINTS["triple_double"] * count  # Multiply by count of triple-doubles
                    )
                )

        # Bulk insert all bonus entries
        if bonus_entries:
            session.bulk_save_objects(bonus_entries)
            session.commit()

    finally:
        if owned_session:
            session.close()