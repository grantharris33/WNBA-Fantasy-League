from typing import Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    """Start the global scheduler if it isn't already running."""
    if not scheduler.running:
        scheduler.start()
        _schedule_live_game_jobs()


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


def _schedule_live_game_jobs() -> None:
    """Schedule live game update jobs."""
    from app.jobs.live_game_updates import (
        cleanup_old_live_data,
        run_live_game_updates,
        setup_todays_game_tracking,
        stop_finished_game_tracking,
    )

    # Live game updates every 2 minutes during typical game hours (7 PM - 11 PM ET, 12 AM - 4 AM UTC)
    scheduler.add_job(
        run_live_game_updates,
        "cron",
        hour="0-4,23",  # 12 AM - 4 AM and 11 PM UTC (covers prime time games)
        minute="*/2",  # Every 2 minutes
        id="live_game_updates",
        name="Live Game Updates",
        replace_existing=True,
    )

    # Setup today's game tracking at 10 AM ET (3 PM UTC) daily
    scheduler.add_job(
        setup_todays_game_tracking,
        "cron",
        hour=15,
        minute=0,
        id="setup_game_tracking",
        name="Setup Today's Game Tracking",
        replace_existing=True,
    )

    # Stop finished game tracking every 30 minutes
    scheduler.add_job(
        stop_finished_game_tracking,
        "interval",
        minutes=30,
        id="stop_finished_games",
        name="Stop Finished Game Tracking",
        replace_existing=True,
    )

    # Clean up old live data daily at 6 AM UTC
    scheduler.add_job(
        cleanup_old_live_data,
        "cron",
        hour=6,
        minute=0,
        id="cleanup_live_data",
        name="Cleanup Old Live Data",
        replace_existing=True,
    )
