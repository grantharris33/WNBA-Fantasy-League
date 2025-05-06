from typing import Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    """Start the global scheduler if it isn't already running."""
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler() -> None:
    """Shutdown the global scheduler if it is running."""
    if scheduler.running:
        scheduler.shutdown()


def list_jobs() -> List[Dict[str, str]]:
    """Return a serialisable list of scheduled jobs suitable for JSON response."""
    if not scheduler.running:
        scheduler.start()

    jobs: List[Dict[str, str]] = []
    for job in scheduler.get_jobs():
        next_run = getattr(job, "next_run_time", None)
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
            }
        )
    return jobs
