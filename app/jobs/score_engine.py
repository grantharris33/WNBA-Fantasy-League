"""APScheduler task that aggregates nightly stat lines into weekly team scores.

It is registered by ``app.main`` alongside the ingest job so that the full
pipeline runs automatically every night once the stat lines have been pulled.

Story Reference: FANTASY-4C – Cron Trigger (nightly recompute).
"""
from __future__ import annotations

import datetime as dt

from app.services.scoring import update_weekly_team_scores


async def run_engine() -> None:  # noqa: D401
    """Coroutine wrapper so APScheduler can run function in async context."""
    target_date = (dt.datetime.utcnow() - dt.timedelta(days=1)).date()
    update_weekly_team_scores(target_date)
