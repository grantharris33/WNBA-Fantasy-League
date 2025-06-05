"""Daily job for calculating advanced analytics and player metrics."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import IngestLog
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)


def run_analytics_calculation():
    """Run daily analytics calculations for all players."""
    db = next(get_db())

    try:
        logger.info("Starting daily analytics calculation")

        analytics_service = AnalyticsService(db)
        season = datetime.now().year

        # Run all analytics calculations
        analytics_service.calculate_all_analytics(season)

        # Log success
        log_entry = IngestLog(
            provider="analytics_job", message=f"Successfully calculated analytics for season {season}"
        )
        db.add(log_entry)
        db.commit()

        logger.info("Analytics calculation completed successfully")

    except Exception as e:
        logger.error(f"Error in analytics calculation: {e}")

        # Log error
        log_entry = IngestLog(provider="analytics_job", message=f"Error calculating analytics: {str(e)}")
        db.add(log_entry)
        db.commit()

        raise

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_analytics_calculation()
