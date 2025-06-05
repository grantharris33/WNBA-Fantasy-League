#!/usr/bin/env python
"""Simplified MVP seed script that works with existing models.

Creates basic demo data for testing:
- Users with one admin
- Sample leagues
- Teams in leagues
- Basic players

Run with:
    poetry run python scripts/seed_mvp.py [--force]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from sqlalchemy import text

from app import models
from app.core.database import DB_PATH, SessionLocal, init_db
from app.core.security import hash_password


def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Seed the database with MVP demo data.")
    parser.add_argument("--force", action="store_true", help="Force recreation of demo data")
    args = parser.parse_args()

    print(f"Using database: sqlite:///{DB_PATH}")
    print("Creating MVP demo data...")

    # Initialize database schema
    init_db()

    # Create session
    db = SessionLocal()

    try:
        # Check for existing data
        user_count = db.query(models.User).count()

        # If data already seeded and not forcing, skip
        if not args.force and user_count > 0:
            print("Demo data already exists. Skipping. (Use --force to recreate)")
            return

        # Clean existing data if force is set
        if args.force and user_count > 0:
            print("Cleaning existing data...")
            # Clear tables in correct order
            db.execute(text("DELETE FROM roster_slot"))
            db.execute(text("DELETE FROM team"))
            db.execute(text("DELETE FROM league"))
            db.execute(text("DELETE FROM player"))
            db.execute(text("DELETE FROM user"))
            db.commit()

        # Create users
        print("Creating users...")
        users = []

        # Admin user
        admin = models.User(
            email="me@grantharris.tech", hashed_password=hash_password("Thisisapassword1"), is_admin=True
        )
        db.add(admin)
        users.append(admin)

        # Demo users
        demo_users = [
            ("demo@example.com", "demo123"),
            ("alice@example.com", "alice123"),
            ("bob@example.com", "bob123"),
            ("charlie@example.com", "charlie123"),
        ]

        for email, password in demo_users:
            user = models.User(email=email, hashed_password=hash_password(password), is_admin=False)
            db.add(user)
            users.append(user)

        db.flush()
        print(f"  Created {len(users)} users")

        # Create simple player list
        print("Creating players...")
        player_names = [
            ("Sabrina Ionescu", "G"),
            ("A'ja Wilson", "F"),
            ("Breanna Stewart", "F"),
            ("Jewell Loyd", "G"),
            ("Kelsey Plum", "G"),
            ("Diana Taurasi", "G"),
            ("Nneka Ogwumike", "F"),
            ("Brittney Griner", "C"),
            ("Jonquel Jones", "C"),
            ("Alyssa Thomas", "F"),
            ("Napheesa Collier", "F"),
            ("Skylar Diggins-Smith", "G"),
            ("Candace Parker", "F"),
            ("Jackie Young", "G"),
            ("Courtney Williams", "G"),
            ("Arike Ogunbowale", "G"),
            ("Rhyne Howard", "G"),
            ("Kahleah Copper", "F"),
            ("DeWanna Bonner", "F"),
            ("Tina Charles", "C"),
        ]

        players = []
        for i, (name, position) in enumerate(player_names, start=1):
            player = models.Player(id=i, full_name=name, position=position, status="active")
            db.add(player)
            players.append(player)

        db.flush()
        print(f"  Created {len(players)} players")

        # Create leagues
        print("Creating leagues...")

        # Active league
        league1 = models.League(
            name="MVP Demo League",
            invite_code="MVP-DEMO",
            commissioner=admin,
            max_teams=6,
            draft_date=datetime.now(timezone.utc),
            settings={"draft_type": "snake", "scoring_type": "h2h", "draft_rounds": 10, "roster_size": 10},
        )
        db.add(league1)

        # Another league
        league2 = models.League(
            name="Test League",
            invite_code="TEST-123",
            commissioner=users[1],  # demo user
            max_teams=4,
            settings={"draft_type": "snake", "scoring_type": "roto", "draft_rounds": 8, "roster_size": 8},
        )
        db.add(league2)

        db.flush()
        print("  Created 2 leagues")

        # Create teams
        print("Creating teams...")
        team_names = ["Warriors", "Dynasty", "All-Stars", "Champions", "Legends", "Elite"]

        # Teams for league 1
        for i, (user, team_name) in enumerate(zip(users[:5], team_names[:5])):
            team = models.Team(name=team_name, owner=user, league=league1)
            db.add(team)

            # Add some players to rosters
            if i < 3:  # Only first 3 teams get players
                for j in range(3):
                    player_idx = (i * 3 + j) % len(players)
                    roster_slot = models.RosterSlot(team=team, player=players[player_idx], is_starter=(j < 2))
                    db.add(roster_slot)

        # Teams for league 2
        for user, team_name in zip(users[1:4], ["Team A", "Team B", "Team C"]):
            team = models.Team(name=team_name, owner=user, league=league2)
            db.add(team)

        db.flush()
        print("  Created teams and sample rosters")

        # Commit all changes
        db.commit()

        print("\n✅ MVP demo data created successfully!")
        print("\nDemo Users:")
        print("- Admin: me@grantharris.tech / Thisisapassword1")
        print("- Demo: demo@example.com / demo123")
        print("- Others: alice/bob/charlie@example.com / {name}123")
        print("\nLeagues:")
        print("- MVP Demo League (6 teams max)")
        print("- Test League (4 teams max)")

    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
