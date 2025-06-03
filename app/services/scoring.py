from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Mapping, MutableMapping

from sqlalchemy.orm import Session

from app import models
from app.core.database import SessionLocal

"""Fantasy points calculation and team score aggregation utilities.

This module implements the rules engine defined in docs/Story-4.md.
It contains two main public helpers:

* ``compute_fantasy_points`` - pure function that converts a ``StatLine``
  (or compatible mapping) into a single fantasy-points float.
* ``update_weekly_team_scores`` - aggregates all ``StatLine`` rows in a given
  ISO week into a single ``TeamScore`` record per team.

Both helpers are synchronous and safe to call inside a scheduler job or CLI
script. They manage their own database session unless an explicit one is
supplied.
"""

__all__ = ["compute_fantasy_points", "update_weekly_team_scores"]

# ---------------------------------------------------------------------------
# 4-A  Point Formula Function – pure, side-effect free
# ---------------------------------------------------------------------------

# Scoring weights – easy to tweak if league rules change.
_PTS_W = 1.0  # Points
_REB_W = 1.2  # Rebounds
_AST_W = 1.5  # Assists
_STL_W = 3.0  # Steals
_BLK_W = 3.0  # Blocks
_TO_W = -1.0  # Turnovers (negative points)
_TRIPLE_DOUBLE_BONUS = 10.0

# Categories we consider for double / triple-double detection.
_CATEGORIES = ("points", "rebounds", "assists", "steals", "blocks")


def _to_float(val: object | None) -> float:
    """Helper: robustly coerce ``val`` to ``float`` (default 0)."""
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):  # pragma: no cover – defensive
        return 0.0


def compute_fantasy_points(stat: "models.StatLine | Mapping[str, object]") -> float:  # noqa: D401
    """Return fantasy-points **float** for a single stat line.

    The formula follows a fairly standard basketball fantasy scoring system:

    * 1.0 x points
    * 1.2 x rebounds
    * 1.5 x assists
    * 3.0 x steals
    * 3.0 x blocks
    * -1.0 x turnovers
    * +10 bonus for a *triple-double* (≥ 10 in **three** separate categories)
    """

    # Normalise to mapping interface first to simplify code.
    if hasattr(stat, "__dict__") and isinstance(stat, models.StatLine):
        data: MutableMapping[str, object] = {
            "points": stat.points,
            "rebounds": stat.rebounds,
            "assists": stat.assists,
            "steals": stat.steals,
            "blocks": stat.blocks,
            "turnovers": stat.turnovers,
        }
    else:
        data = dict(stat)  # make copy

    pts = _to_float(data.get("points")) * _PTS_W
    reb = _to_float(data.get("rebounds")) * _REB_W
    ast = _to_float(data.get("assists")) * _AST_W
    stl = _to_float(data.get("steals")) * _STL_W
    blk = _to_float(data.get("blocks")) * _BLK_W
    to = _to_float(data.get("turnovers")) * _TO_W

    total = pts + reb + ast + stl + blk + to

    # Triple-double bonus detection.
    cats_10 = sum(_to_float(data.get(k)) >= 10 for k in _CATEGORIES)
    if cats_10 >= 3:
        total += _TRIPLE_DOUBLE_BONUS

    return round(total, 2)  # round for deterministic snapshot tests


# ---------------------------------------------------------------------------
# 4-B  Engine service – weekly aggregation into ``team_score``
# ---------------------------------------------------------------------------


def _week_bounds(target: date) -> tuple[datetime, datetime, int]:
    """Return UTC datetimes for Monday 00:00 - Sunday 23:59 **and** week-id.

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


def update_weekly_team_scores(target_date: date | None = None, *, session: Session | None = None) -> None:
    """Aggregate stat lines for the ISO week containing *target_date*.

    Existing ``team_score`` rows for that week will be overwritten with the
    newly calculated totals so the function is **idempotent**.

    For current week: uses RosterSlot.is_starter to determine starters
    For past weeks: uses WeeklyLineup records to get historical lineup
    """

    owned_session = False
    if session is None:
        session = SessionLocal()
        owned_session = True

    target_date = target_date or (datetime.now(timezone.utc) - timedelta(days=1)).date()
    start_dt, end_dt, week_id = _week_bounds(target_date)

    try:
                # Determine current week
        current_week_id = _week_bounds(datetime.now(timezone.utc).date())[2]

        # Build starter mapping based on whether this is current or past week
        starter_mapping: dict[int, int] = {}  # {player_id: team_id} for starters only

        if week_id >= current_week_id:
            # Current/future week: use RosterSlot table
            roster_query = (
                session.query(models.RosterSlot)
                .filter(models.RosterSlot.is_starter == True)
            )
            starter_mapping = {rs.player_id: rs.team_id for rs in roster_query}
            print(f"DEBUG: Current/future week {week_id}, found {len(starter_mapping)} starters")
        else:
            # Past week: use WeeklyLineup table
            lineup_query = (
                session.query(models.WeeklyLineup)
                .filter(models.WeeklyLineup.week_id == week_id)
                .filter(models.WeeklyLineup.is_starter == True)
            )
            starter_mapping = {wl.player_id: wl.team_id for wl in lineup_query}
            print(f"DEBUG: Past week {week_id}, found {len(starter_mapping)} starters")

        # Fetch all stat lines for the week in one trip.
        stat_q = (
            session.query(models.StatLine)
            .filter(models.StatLine.game_date >= start_dt)
            .filter(models.StatLine.game_date < end_dt)
        )

        team_totals: dict[int, float] = {}
        for line in stat_q:  # SQLAlchemy will stream rows efficiently
            team_id = starter_mapping.get(line.player_id)
            if team_id is None:
                # Player is not a starter for any team this week → ignore
                continue

            pts = compute_fantasy_points(line)
            team_totals[team_id] = team_totals.get(team_id, 0.0) + pts

        # Remove existing rows for that week so inserts below won't hit unique
        # constraint. We do this *after* computing totals to minimise lock time.
        session.query(models.TeamScore).filter_by(week=week_id).delete()

        # Insert fresh rows (bulk add for efficiency)
        new_rows = [
            models.TeamScore(team_id=tid, week=week_id, score=round(total, 2)) for tid, total in team_totals.items()
        ]
        session.bulk_save_objects(new_rows)
        session.commit()
    finally:
        if owned_session:
            session.close()
