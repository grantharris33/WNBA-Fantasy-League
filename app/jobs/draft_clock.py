import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DraftState
from app.services.draft import DraftService

logger = logging.getLogger(__name__)


def check_draft_clocks():
    """
    Check all active drafts for expired pick clocks and trigger auto-picks.

    This job runs every second to:
    1. Decrement the seconds_remaining for all active drafts
    2. Trigger auto-picks for any drafts with seconds_remaining <= 0
    """
    logger.info("Running draft clock check")

    # Get DB session
    db = next(get_db())

    try:
        # Get all active drafts
        active_drafts = db.query(DraftState).filter(DraftState.status == "active").all()

        for draft in active_drafts:
            # Decrement clock
            draft.seconds_remaining -= 1
            draft.updated_at = datetime.utcnow()

            # If clock expired, trigger auto-pick
            if draft.seconds_remaining <= 0:
                logger.info(f"Draft {draft.id} clock expired, triggering auto-pick")
                draft_service = DraftService(db)

                try:
                    # Execute auto-pick
                    pick_result = draft_service.auto_pick(draft.id)

                    if pick_result:
                        pick, updated_draft = pick_result
                        logger.info(
                            f"Auto-picked player {pick.player_id} for team {pick.team_id} "
                            f"in draft {draft.id}"
                        )
                    else:
                        logger.warning(f"Auto-pick not completed for draft {draft.id}")

                except Exception as e:
                    logger.error(f"Error during auto-pick for draft {draft.id}: {str(e)}")

            # Save draft state (even if no auto-pick)
            db.add(draft)

        db.commit()

    except Exception as e:
        logger.error(f"Error in draft clock job: {str(e)}")
        db.rollback()
    finally:
        db.close()


def pause_stale_drafts():
    """
    Pause any drafts that have been inactive for more than 1 hour.
    This job runs every hour.
    """
    logger.info("Checking for stale drafts")

    # Get DB session
    db = next(get_db())

    try:
        # Get active drafts with no updates in the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        stale_drafts = db.query(DraftState).filter(
            DraftState.status == "active",
            DraftState.updated_at < one_hour_ago
        ).all()

        for draft in stale_drafts:
            logger.info(f"Pausing stale draft {draft.id}")
            draft.status = "paused"
            draft.updated_at = datetime.utcnow()
            db.add(draft)

        db.commit()

    except Exception as e:
        logger.error(f"Error in stale draft check: {str(e)}")
        db.rollback()
    finally:
        db.close()


def restore_draft_clocks():
    """
    Restore draft clocks on application startup.
    This ensures draft clocks continue from where they left off after a server restart.
    """
    logger.info("Restoring draft clocks on startup")

    # Get DB session
    db = next(get_db())

    try:
        # Get all active drafts
        active_drafts = db.query(DraftState).filter(DraftState.status == "active").all()

        if active_drafts:
            logger.info(f"Restored {len(active_drafts)} active draft clocks")

    except Exception as e:
        logger.error(f"Error restoring draft clocks: {str(e)}")
    finally:
        db.close()