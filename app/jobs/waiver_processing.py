"""Waiver wire processing scheduled job."""

import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.models import IngestLog
from app.services.waiver import WaiverService

logger = logging.getLogger(__name__)


def process_daily_waivers() -> dict[str, any]:
    """Process all pending waiver claims for all leagues.

    This function runs daily at 3 AM UTC to process waiver claims.

    Returns:
        Dictionary with processing results
    """
    db = SessionLocal()
    log_message = ""

    try:
        waiver_service = WaiverService(db)

        logger.info("Starting daily waiver processing")
        start_time = datetime.utcnow()

        # Process all waivers (no league filter)
        results = waiver_service.process_waivers()

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        # Create summary message
        log_message = (
            f"Waiver processing completed in {processing_time:.2f}s. "
            f"Total claims: {results['total_claims']}, "
            f"Successful: {results['successful_claims']}, "
            f"Failed: {results['failed_claims']}, "
            f"Leagues processed: {results['processed_leagues']}"
        )

        if results.get("errors"):
            log_message += f". Errors: {len(results['errors'])}"
            for error in results["errors"][:3]:  # Log first 3 errors
                logger.error(f"Waiver processing error: {error}")

        logger.info(log_message)

        # Log successful completion
        ingest_log = IngestLog(provider="waiver_processor", message=log_message)
        db.add(ingest_log)
        db.commit()

        return results

    except Exception as e:
        error_message = f"Fatal error during waiver processing: {str(e)}"
        logger.error(error_message, exc_info=True)

        # Log the error
        try:
            ingest_log = IngestLog(provider="waiver_processor", message=f"ERROR: {error_message}")
            db.add(ingest_log)
            db.commit()
        except Exception:
            db.rollback()
            logger.error("Failed to log waiver processing error to database")

        return {
            "total_claims": 0,
            "successful_claims": 0,
            "failed_claims": 0,
            "processed_leagues": 0,
            "errors": [error_message],
        }

    finally:
        db.close()


def process_league_waivers(league_id: int) -> dict[str, any]:
    """Process waiver claims for a specific league.

    Args:
        league_id: ID of the league to process

    Returns:
        Dictionary with processing results
    """
    db = SessionLocal()

    try:
        waiver_service = WaiverService(db)

        logger.info(f"Processing waivers for league {league_id}")
        start_time = datetime.utcnow()

        results = waiver_service.process_waivers(league_id)

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        log_message = (
            f"League {league_id} waiver processing completed in {processing_time:.2f}s. "
            f"Total claims: {results['total_claims']}, "
            f"Successful: {results['successful_claims']}, "
            f"Failed: {results['failed_claims']}"
        )

        logger.info(log_message)

        # Log completion
        ingest_log = IngestLog(provider="waiver_processor", message=log_message)
        db.add(ingest_log)
        db.commit()

        return results

    except Exception as e:
        error_message = f"Error processing waivers for league {league_id}: {str(e)}"
        logger.error(error_message, exc_info=True)

        # Log the error
        try:
            ingest_log = IngestLog(provider="waiver_processor", message=f"ERROR: {error_message}")
            db.add(ingest_log)
            db.commit()
        except Exception:
            db.rollback()

        return {
            "total_claims": 0,
            "successful_claims": 0,
            "failed_claims": 0,
            "processed_leagues": 0,
            "errors": [error_message],
        }

    finally:
        db.close()


# Convenience function for manual testing
def test_waiver_processing() -> None:
    """Test waiver processing functionality."""
    result = process_daily_waivers()
    print(f"Waiver processing test results: {result}")


if __name__ == "__main__":
    # Allow running the job directly for testing
    test_waiver_processing()
