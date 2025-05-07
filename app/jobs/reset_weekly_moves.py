import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Team
from app.services.roster import RosterService

logger = logging.getLogger(__name__)


def reset_weekly_moves(db: Session) -> None:
    """
    Reset the moves_this_week counter for all teams to 0.
    This job should run every Monday at a defined UTC time (e.g., 05:00 UTC).
    """
    start_time = datetime.utcnow()
    logger.info(f"Starting weekly reset of moves_this_week counters at {start_time}")

    try:
        service = RosterService(db)
        service.reset_weekly_moves()

        # Log the success
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Successfully reset moves_this_week counters for all teams in {duration:.2f} seconds")
    except Exception as e:
        logger.error(f"Error resetting moves_this_week counters: {str(e)}")
        raise
