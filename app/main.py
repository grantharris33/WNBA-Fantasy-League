import os

import uvicorn
from fastapi import FastAPI

from app.api import router as api_router
from app.core.database import init_db
from app.core.scheduler import list_jobs, scheduler, shutdown_scheduler, start_scheduler
from app.jobs.ingest import ingest_stat_lines

init_db()

app = FastAPI()

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


# Schedule immediately so that tests without lifespan still see job
# _schedule_nightly()
if os.getenv("TESTING") != "true":
    _schedule_nightly()  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
