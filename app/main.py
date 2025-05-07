import os
import httpx

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.database import init_db
from app.core.scheduler import list_jobs, scheduler, shutdown_scheduler, start_scheduler
from app.jobs.ingest import ingest_stat_lines
from app.jobs.draft_clock import check_draft_clocks, pause_stale_drafts, restore_draft_clocks
from app.jobs.reset_weekly_moves import reset_weekly_moves
from app.jobs.bonus_calc import calc_weekly_bonuses

init_db()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Compatibility patch: Starlette<=0.27 passes unsupported 'app' kw to httpx>=0.25
# ---------------------------------------------------------------------------


def _patch_httpx_for_starlette() -> None:  # pragma: no cover – patch logic
    """Allow httpx.Client / AsyncClient to accept an extra 'app' kw arg.

    Starlette 0.27's TestClient forwards 'app' to httpx.Client which was
    removed in httpx 0.25+.  This shim drops the arg for compatibility so
    we don't need to downgrade httpx in the test environment.
    """

    def _wrap_init(cls):
        original_init = cls.__init__

        if getattr(cls, "_starlette_patch_applied", False):
            return  # already patched

        def patched_init(self, *args, **kwargs):  # type: ignore[override]
            # Starlette passes the ASGI app under the 'app' kwarg – remove it.
            kwargs.pop("app", None)
            return original_init(self, *args, **kwargs)

        cls.__init__ = patched_init  # type: ignore[assignment]
        cls._starlette_patch_applied = True  # type: ignore[attr-defined]

    _wrap_init(httpx.Client)
    _wrap_init(httpx.AsyncClient)


# Apply the patch as early as possible, before FastAPI's TestClient is used.
_patch_httpx_for_starlette()

# ---- Lifespan events ------------------------------------------------------


@app.on_event("startup")
async def _startup() -> None:
    start_scheduler()

    # Schedule nightly job (03:00 UTC) if not already
    if not scheduler.get_job("nightly_ingest"):
        hour = int(os.getenv("INGEST_HOUR_UTC", "3"))
        scheduler.add_job(
            ingest_stat_lines, "cron", hour=hour, id="nightly_ingest", replace_existing=True, misfire_grace_time=3600
        )

    # Schedule scoring engine 30 min after ingest by default (configurable via env).
    if not scheduler.get_job("nightly_scoring"):
        hour = int(os.getenv("INGEST_HOUR_UTC", "3"))
        minute_offset = int(os.getenv("SCORING_MINUTE_OFFSET", "30"))

        # Compute minute and hour adjusting for overflow > 59
        scoring_hour = (hour + (minute_offset // 60)) % 24
        scoring_minute = minute_offset % 60

        from app.jobs.score_engine import run_engine

        scheduler.add_job(
            run_engine,
            "cron",
            hour=scoring_hour,
            minute=scoring_minute,
            id="nightly_scoring",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Schedule weekly reset job for Mondays at 05:00 UTC
    if not scheduler.get_job("reset_weekly_moves"):
        reset_hour = int(os.getenv("WEEKLY_RESET_HOUR_UTC", "5"))

        from app.core.database import get_db
        from functools import partial

        # Create a job with a database session
        db = next(get_db())
        reset_job = partial(reset_weekly_moves, db)

        scheduler.add_job(
            reset_job,
            "cron",
            day_of_week="mon",
            hour=reset_hour,
            id="reset_weekly_moves",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Schedule weekly bonus calculator for Sundays at 23:59 local (05:59 UTC Monday)
    if not scheduler.get_job("weekly_bonus_calc"):
        # Monday 05:59 UTC is equivalent to Sunday 23:59 in most US time zones
        scheduler.add_job(
            calc_weekly_bonuses,
            "cron",
            day_of_week="mon",
            hour=5,
            minute=59,
            id="weekly_bonus_calc",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Draft clock jobs

    # Restore any active draft clocks on startup
    restore_draft_clocks()

    # Check draft clocks every second
    draft_timer_seconds = int(os.getenv("DRAFT_TIMER_SECONDS", "1"))
    if not scheduler.get_job("draft_clock_check"):
        scheduler.add_job(
            check_draft_clocks,
            "interval",
            seconds=draft_timer_seconds,
            id="draft_clock_check",
            replace_existing=True,
        )

    # Check for stale drafts hourly
    if not scheduler.get_job("pause_stale_drafts"):
        scheduler.add_job(
            pause_stale_drafts,
            "interval",
            hours=1,
            id="pause_stale_drafts",
            replace_existing=True,
        )


@app.on_event("shutdown")
async def _shutdown() -> None:
    shutdown_scheduler()


app.include_router(api_router)

# Debug route to list scheduled jobs


@app.get("/jobs")
async def jobs():
    return list_jobs()


def _schedule_nightly() -> None:
    if not scheduler.get_job("nightly_ingest"):
        hour = int(os.getenv("INGEST_HOUR_UTC", "3"))
        scheduler.add_job(
            ingest_stat_lines, "cron", hour=hour, id="nightly_ingest", replace_existing=True, misfire_grace_time=3600
        )

    if not scheduler.get_job("nightly_scoring"):
        hour = int(os.getenv("INGEST_HOUR_UTC", "3"))
        minute_offset = int(os.getenv("SCORING_MINUTE_OFFSET", "30"))

        scoring_hour = (hour + (minute_offset // 60)) % 24
        scoring_minute = minute_offset % 60

        from app.jobs.score_engine import run_engine

        scheduler.add_job(
            run_engine,
            "cron",
            hour=scoring_hour,
            minute=scoring_minute,
            id="nightly_scoring",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Schedule weekly reset job for Mondays at 05:00 UTC
    if not scheduler.get_job("reset_weekly_moves"):
        reset_hour = int(os.getenv("WEEKLY_RESET_HOUR_UTC", "5"))

        from app.core.database import get_db
        from functools import partial

        # Create a job with a database session
        db = next(get_db())
        reset_job = partial(reset_weekly_moves, db)

        scheduler.add_job(
            reset_job,
            "cron",
            day_of_week="mon",
            hour=reset_hour,
            id="reset_weekly_moves",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Schedule weekly bonus calculator for Sundays at 23:59 local (05:59 UTC Monday)
    if not scheduler.get_job("weekly_bonus_calc"):
        # Monday 05:59 UTC is equivalent to Sunday 23:59 in most US time zones
        scheduler.add_job(
            calc_weekly_bonuses,
            "cron",
            day_of_week="mon",
            hour=5,
            minute=59,
            id="weekly_bonus_calc",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Draft clock jobs - also schedule in this function for tests
    draft_timer_seconds = int(os.getenv("DRAFT_TIMER_SECONDS", "1"))
    if not scheduler.get_job("draft_clock_check"):
        scheduler.add_job(
            check_draft_clocks,
            "interval",
            seconds=draft_timer_seconds,
            id="draft_clock_check",
            replace_existing=True,
        )

    if not scheduler.get_job("pause_stale_drafts"):
        scheduler.add_job(
            pause_stale_drafts,
            "interval",
            hours=1,
            id="pause_stale_drafts",
            replace_existing=True,
        )


# Schedule immediately so that tests without lifespan still see job
# _schedule_nightly()
if os.getenv("TESTING") != "true":
    _schedule_nightly()  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
