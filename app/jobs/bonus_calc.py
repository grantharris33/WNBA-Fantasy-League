"""APScheduler task that calculates weekly leader bonuses.

This job runs every Sunday at 23:59 local time (05:59 UTC on Monday) and
calculates bonuses for top performers in various statistical categories
for the week that just ended.

Story Reference: FANTASY-11C – Scheduler Hook.
"""
from __future__ import annotations

import datetime as dt

from app.services.bonus import calculate_weekly_bonuses


async def calc_weekly_bonuses() -> None:  # noqa: D401
    """Coroutine wrapper so APScheduler can run function in async context."""
    # Calculate for previous day (Sunday)
    target_date = (dt.datetime.utcnow() - dt.timedelta(days=1)).date()
    calculate_weekly_bonuses(target_date)