import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Team
from app.services.roster import RosterService

logger = logging.getLogger(__name__)


def reset_weekly_moves(db: Session) -> None:
    """
    Reset the moves_this_week counter for all teams to 0 and handle starter carryover.
    This job should run every Monday at a defined UTC time (e.g., 05:00 UTC).
    """
    start_time = datetime.utcnow()
    logger.info(f"Starting weekly reset process at {start_time}")

    try:
        service = RosterService(db)

        # Get current and previous week IDs
        current_week_id = service._get_current_week_id()
        previous_week_id = current_week_id - 1

        logger.info(f"Processing week transition: {previous_week_id} -> {current_week_id}")

        # 1. Save current starters to history for the previous week
        teams_saved = service.save_current_starters_to_history(previous_week_id)
        logger.info(f"Saved starters to history for {teams_saved} teams for week {previous_week_id}")

        # 2. Reset weekly move counters
        service.reset_weekly_moves()
        logger.info("Reset moves_this_week counters for all teams")

        # 3. Carry over starters from previous week for teams without current starters
        teams_carried_over = service.carry_over_starters_from_previous_week(current_week_id)
        logger.info(f"Carried over starters for {teams_carried_over} teams to week {current_week_id}")

        # Log the success
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Successfully completed weekly reset process in {duration:.2f} seconds")
    except Exception as e:
        logger.error(f"Error during weekly reset process: {str(e)}")
        raise
