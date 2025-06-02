#!/usr/bin/env python3
"""
Script to update existing leagues with default timer settings.
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import League


def update_league_settings():
    """Update existing leagues to have default timer settings."""
    db: Session = SessionLocal()

    try:
        # Get all leagues
        leagues = db.query(League).all()

        for league in leagues:
            if league.settings is None:
                league.settings = {}

            # Add default timer if not set
            if 'draft_timer_seconds' not in league.settings:
                league.settings['draft_timer_seconds'] = 60

                # Force SQLAlchemy to detect the change
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(league, "settings")

                print(f"Updated league {league.id} ({league.name}) with default timer settings")

        db.commit()
        print(f"Updated {len(leagues)} leagues with default settings")

    except Exception as e:
        print(f"Error updating league settings: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_league_settings()