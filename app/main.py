import os

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.database import init_db
from app.core.middleware import ChangeLogMiddleware
from app.core.scheduler import list_jobs, scheduler, shutdown_scheduler, start_scheduler
from app.jobs.bonus_calc import calc_weekly_bonuses
from app.jobs.draft_clock import check_draft_clocks, pause_stale_drafts, restore_draft_clocks, start_scheduled_drafts
from app.jobs.ingest import ingest_stat_lines
from app.jobs.ingest_players import ingest_player_profiles
from app.jobs.reset_weekly_moves import reset_weekly_moves

init_db()

app = FastAPI()

# Add CORS middleware
# In production, nginx handles CORS, but keep for development
allowed_origins = ["http://localhost:5173", "http://localhost:5174"]
if os.getenv("ENVIRONMENT") == "production":
    # In production, requests come through nginx proxy
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list all methods
    allow_headers=["*"],
)

# Add Change Log middleware - temporarily disabled to fix database session issues
# app.add_middleware(ChangeLogMiddleware)

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
    # Skip scheduler startup in test environment
    if os.getenv("TESTING") == "true":
        return

    start_scheduler()

    # Schedule nightly job (03:00 UTC) if not already
    if not scheduler.get_job("nightly_ingest"):
        hour = int(os.getenv("INGEST_HOUR_UTC", "3"))
        scheduler.add_job(
            ingest_stat_lines, "cron", hour=hour, id="nightly_ingest", replace_existing=True, misfire_grace_time=3600
        )

    # Schedule scoring engine hourly (configurable via env).
    if not scheduler.get_job("hourly_scoring"):
        from app.jobs.score_engine import run_engine

        # Run every hour on the hour by default
        scoring_interval_minutes = int(os.getenv("SCORING_INTERVAL_MINUTES", "60"))

        scheduler.add_job(
            run_engine,
            "interval",
            minutes=scoring_interval_minutes,
            id="hourly_scoring",
            replace_existing=True,
            misfire_grace_time=300,  # 5 minutes
        )

    # Schedule weekly reset job for Mondays at 05:00 UTC
    if not scheduler.get_job("reset_weekly_moves"):
        reset_hour = int(os.getenv("WEEKLY_RESET_HOUR_UTC", "5"))

        # Use the job wrapper that manages its own database session
        from app.jobs.reset_weekly_moves import reset_weekly_moves_job

        scheduler.add_job(
            reset_weekly_moves_job,
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

    # Schedule weekly player profile ingestion for Tuesdays at 02:00 UTC
    if not scheduler.get_job("weekly_player_ingestion"):
        player_ingest_hour = int(os.getenv("PLAYER_INGEST_HOUR_UTC", "2"))
        scheduler.add_job(
            ingest_player_profiles,
            "cron",
            day_of_week="tue",
            hour=player_ingest_hour,
            id="weekly_player_ingestion",
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
            check_draft_clocks, "interval", seconds=draft_timer_seconds, id="draft_clock_check", replace_existing=True
        )

    # Check for stale drafts hourly
    if not scheduler.get_job("pause_stale_drafts"):
        scheduler.add_job(pause_stale_drafts, "interval", hours=1, id="pause_stale_drafts", replace_existing=True)

    # Check for scheduled drafts to start every minute
    if not scheduler.get_job("start_scheduled_drafts"):
        scheduler.add_job(
            start_scheduled_drafts, "interval", minutes=1, id="start_scheduled_drafts", replace_existing=True
        )

    # Schedule daily analytics calculation at 04:00 UTC (after ingest and scoring)
    if not scheduler.get_job("daily_analytics"):
        analytics_hour = int(os.getenv("ANALYTICS_HOUR_UTC", "4"))

        from app.jobs.analytics_job import run_analytics_calculation

        scheduler.add_job(
            run_analytics_calculation,
            "cron",
            hour=analytics_hour,
            id="daily_analytics",
            replace_existing=True,
            misfire_grace_time=3600,
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

    if not scheduler.get_job("hourly_scoring"):
        from app.jobs.score_engine import run_engine

        # Run every hour on the hour by default
        scoring_interval_minutes = int(os.getenv("SCORING_INTERVAL_MINUTES", "60"))

        scheduler.add_job(
            run_engine,
            "interval",
            minutes=scoring_interval_minutes,
            id="hourly_scoring",
            replace_existing=True,
            misfire_grace_time=300,  # 5 minutes
        )

    # Schedule weekly reset job for Mondays at 05:00 UTC
    if not scheduler.get_job("reset_weekly_moves"):
        reset_hour = int(os.getenv("WEEKLY_RESET_HOUR_UTC", "5"))

        # Use the job wrapper that manages its own database session
        from app.jobs.reset_weekly_moves import reset_weekly_moves_job

        scheduler.add_job(
            reset_weekly_moves_job,
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

    # Schedule weekly player profile ingestion for Tuesdays at 02:00 UTC
    if not scheduler.get_job("weekly_player_ingestion"):
        player_ingest_hour = int(os.getenv("PLAYER_INGEST_HOUR_UTC", "2"))
        scheduler.add_job(
            ingest_player_profiles,
            "cron",
            day_of_week="tue",
            hour=player_ingest_hour,
            id="weekly_player_ingestion",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    # Draft clock jobs - also schedule in this function for tests
    draft_timer_seconds = int(os.getenv("DRAFT_TIMER_SECONDS", "1"))
    if not scheduler.get_job("draft_clock_check"):
        scheduler.add_job(
            check_draft_clocks, "interval", seconds=draft_timer_seconds, id="draft_clock_check", replace_existing=True
        )

    if not scheduler.get_job("pause_stale_drafts"):
        scheduler.add_job(pause_stale_drafts, "interval", hours=1, id="pause_stale_drafts", replace_existing=True)

    # Also add scheduled draft checker to _schedule_nightly for tests
    if not scheduler.get_job("start_scheduled_drafts"):
        scheduler.add_job(
            start_scheduled_drafts, "interval", minutes=1, id="start_scheduled_drafts", replace_existing=True
        )

    # Schedule daily analytics calculation at 04:00 UTC (after ingest and scoring)
    if not scheduler.get_job("daily_analytics"):
        analytics_hour = int(os.getenv("ANALYTICS_HOUR_UTC", "4"))

        from app.jobs.analytics_job import run_analytics_calculation

        scheduler.add_job(
            run_analytics_calculation,
            "cron",
            hour=analytics_hour,
            id="daily_analytics",
            replace_existing=True,
            misfire_grace_time=3600,
        )


# Schedule immediately so that tests without lifespan still see job
# _schedule_nightly()
if os.getenv("TESTING") != "true":
    _schedule_nightly()  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
