import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.ws_manager import manager
from app.models import DraftState, League
from app.services.draft import DraftService

logger = logging.getLogger(__name__)

# Global counter to track when to broadcast timer updates
_broadcast_counter = 0


def check_draft_clocks():
    """
    Check all active drafts for expired pick clocks and trigger auto-picks.

    This job runs every second to:
    1. Decrement the seconds_remaining for all active drafts
    2. Trigger auto-picks for any drafts with seconds_remaining <= 0
    3. Broadcast timer updates every 5 seconds to keep clients in sync
    """
    global _broadcast_counter
    _broadcast_counter += 1

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
                            f"Auto-picked player {pick.player_id} for team {pick.team_id} " f"in draft {draft.id}"
                        )

                        # Broadcast the auto-pick event via WebSocket
                        # This includes the updated draft state with the reset timer
                        try:
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)

                            loop.run_until_complete(manager.broadcast_to_league(
                                updated_draft.league_id,
                                {
                                    "event": "pick_made",
                                    "data": {
                                        "draft_id": draft.id,
                                        "pick": {
                                            "id": pick.id,
                                            "team_id": pick.team_id,
                                            "player_id": pick.player_id,
                                            "round": pick.round,
                                            "pick_number": pick.pick_number,
                                            "is_auto": True,
                                        },
                                        "draft_state": updated_draft.as_dict(),
                                    },
                                },
                            ))
                        except Exception as ws_error:
                            logger.error(f"Error broadcasting auto-pick WebSocket event: {ws_error}")
                    else:
                        logger.warning(f"Auto-pick not completed for draft {draft.id}")

                except Exception as e:
                    logger.error(f"Error during auto-pick for draft {draft.id}: {str(e)}")

            # Save draft state (even if no auto-pick)
            db.add(draft)

        # Broadcast timer updates every 5 seconds to keep clients in sync
        if _broadcast_counter % 5 == 0:
            for draft in active_drafts:
                try:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    loop.run_until_complete(manager.broadcast_to_league(
                        draft.league_id,
                        {
                            "event": "timer_sync",
                            "data": {
                                "draft_id": draft.id,
                                "seconds_remaining": draft.seconds_remaining,
                                "current_team_id": draft.current_team_id(),
                                "status": draft.status
                            }
                        }
                    ))
                except Exception as ws_error:
                    logger.error(f"Error broadcasting timer sync for draft {draft.id}: {ws_error}")

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
        stale_drafts = (
            db.query(DraftState).filter(DraftState.status == "active", DraftState.updated_at < one_hour_ago).all()
        )

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


def start_scheduled_drafts():
    """
    Check for leagues with draft_date that has passed and start their drafts.
    This job runs every minute.
    """
    logger.info("Checking for scheduled drafts to start")

    # Get DB session
    db = next(get_db())

    try:
        # Get leagues with draft_date that has passed and no draft started
        now = datetime.utcnow()

        # Get leagues that have draft dates but no draft state yet
        leagues_with_drafts = db.query(DraftState.league_id).subquery()
        leagues_to_start = (
            db.query(League)
            .filter(
                League.draft_date <= now,
                League.draft_date.isnot(None),
                ~League.id.in_(leagues_with_drafts)  # No draft state exists
            )
            .all()
        )

        draft_service = DraftService(db)

        for league in leagues_to_start:
            try:
                # Check if league has enough teams
                if len(league.teams) >= 2:
                    logger.info(f"Starting scheduled draft for league {league.id} ({league.name})")
                    draft_state = draft_service.start_draft(league.id, league.commissioner_id)
                    logger.info(f"Successfully started draft {draft_state.id} for league {league.id}")
                else:
                    logger.warning(f"Cannot start draft for league {league.id} - not enough teams ({len(league.teams)})")
            except Exception as e:
                logger.error(f"Error starting scheduled draft for league {league.id}: {str(e)}")

        db.commit()

    except Exception as e:
        logger.error(f"Error in scheduled draft check: {str(e)}")
        db.rollback()
    finally:
        db.close()
