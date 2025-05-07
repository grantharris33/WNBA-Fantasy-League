#!/usr/bin/env python
"""Seed script for local development.

Inserts:
* 4 demo users (demo1..4@example.com)
* A league "Demo League" with commissioner demo1
* One team per user in the league

Run with:
    poetry run python scripts/seed_demo.py [--force]
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from app import models
from app.core.database import DB_PATH, SessionLocal, init_db
from app.core.security import hash_password

# Force and database path are managed by app.core.database via DB_FILENAME env var


def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Seed the database with demo data.")
    parser.add_argument("--force", action="store_true", help="Force recreation of demo data")
    args = parser.parse_args()

    print(f"Using database: sqlite:///{DB_PATH}")

    # If force flag is set, delete the database file if it exists
    if args.force and DB_PATH.exists():
        print(f"Removing existing database at {DB_PATH}")
        DB_PATH.unlink()

    # Initialize database schema
    init_db()

    # Create session
    db = SessionLocal()

    # Check for existing data
    user_count = db.query(models.User).count()

    # If data already seeded and not forcing, skip
    if not args.force and user_count > 0:
        print("Demo data already exists. Skipping. (Use --force to recreate)")
        return

    # Clean existing data if force is set
    if args.force and user_count > 0:
        print("Cleaning existing data...")
        # Cascade deletions through FKs
        db.query(models.Team).delete()
        db.query(models.League).delete()
        db.query(models.User).delete()
        db.commit()

    print("Creating demo data...")
    users = []
    for i in range(1, 5):
        email = f"demo{i}@example.com"
        user = models.User(email=email, hashed_password=hash_password("password"))
        db.add(user)
        users.append(user)
    db.flush()  # assign IDs

    league = models.League(name="Demo League", commissioner=users[0])
    db.add(league)
    db.flush()

    teams = []
    for i, user in enumerate(users, start=1):
        team = models.Team(name=f"Team {i}", owner=user, league=league)
        db.add(team)
        teams.append(team)

    db.commit()

    print(f"Created {len(users)} users, 1 league, and {len(teams)} teams")
    print("Seeded demo data successfully.")


if __name__ == "__main__":
    main()
