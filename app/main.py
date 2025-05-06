from fastapi import FastAPI
import uvicorn
import os

from app.core.database import init_db
from app.core.scheduler import start_scheduler, shutdown_scheduler, scheduler, list_jobs
from app.jobs.ingest import ingest_stat_lines

from app.api import router as api_router

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
            ingest_stat_lines,
            "cron",
            hour=hour,
            id="nightly_ingest",
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
            ingest_stat_lines,
            "cron",
            hour=hour,
            id="nightly_ingest",
            replace_existing=True,
            misfire_grace_time=3600,
        )

# Schedule immediately so that tests without lifespan still see job
_schedule_nightly()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
