#!/usr/bin/env python3
"""Lightweight management CLI for development / ops tasks.

Currently supports:

* ``backfill <YYYY>`` – iterate over every ISO week in the given season and
  recompute ``team_score`` totals via the scoring engine.
* ``add-user <email> [--password] [--admin] [--league-name] [--team-name]`` – add a new user
* ``remove-user <email>`` – remove a user and all associated data
* ``list-users`` – list all users in the database
* ``list-leagues`` – list all leagues in the database

Examples::

    poetry run python scripts/manage.py backfill 2024
    poetry run python scripts/manage.py add-user test@example.com --password mypass --admin
    poetry run python scripts/manage.py add-user player@example.com --league-name "Demo League" --team-name "Player Team"
    poetry run python scripts/manage.py remove-user test@example.com
    poetry run python scripts/manage.py list-users
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import uuid
from pathlib import Path

# Ensure project root on path when running script directly
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.append(str(_PROJECT_ROOT))

from app.services.scoring import update_weekly_team_scores  # noqa: E402  pylint: disable=wrong-import-position
from app.models import User, League, Team  # noqa: E402  pylint: disable=wrong-import-position
from app.core.database import SessionLocal, init_db  # noqa: E402  pylint: disable=wrong-import-position
from app.core.security import hash_password  # noqa: E402  pylint: disable=wrong-import-position


def backfill_season(season: int):
    """Recompute weekly ``team_score`` rows for a whole *season* (calendar year).

    The command loops for ISO weeks of the given **season** (ISO year)
    and invokes ``update_weekly_team_scores`` for the Monday of each valid week.
    Existing rows will be overwritten, so the operation is idempotent.
    """
    weeks_run: list[int] = []

    # Determine the number of ISO weeks in the target ISO year `season`
    # The ISO week number of Dec 28th will be 52 or 53.
    last_week_check_date = dt.date(season, 12, 28)
    _, num_iso_weeks_in_season, _ = last_week_check_date.isocalendar()

    for week_num in range(1, num_iso_weeks_in_season + 1):
        try:
            # Get the date for Monday of week_num in the specified ISO year `season`
            monday_of_iso_week = dt.datetime.strptime(f'{season}-{week_num}-1', "%G-%V-%u").date()
        except ValueError:
            # This should ideally not happen if num_iso_weeks_in_season is correct
            # and strptime is working as expected for valid ISO weeks.
            print(
                f"Warning: strptime failed for supposedly valid ISO week {season}-{week_num}. Skipping."
            )  # Add a print for diagnostics
            continue

        update_weekly_team_scores(monday_of_iso_week)
        weeks_run.append(week_num)

    if weeks_run:
        print(
            f"Backfill complete – processed {len(weeks_run)} ISO weeks ({weeks_run[0]}–{weeks_run[-1]}) for ISO season {season}."
        )
    else:
        print(f"Backfill complete – no ISO weeks processed for ISO season {season}.")


def add_user(email: str, password: str = "password", is_admin: bool = False, league_name: str = None, team_name: str = None):
    """Add a new user to the database.

    Args:
        email: User email address
        password: User password (default: "password")
        is_admin: Whether user should be admin (default: False)
        league_name: If provided, add user to this league (create if doesn't exist)
        team_name: If league_name provided, create team with this name for the user
    """
    init_db()
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Error: User with email '{email}' already exists (ID: {existing_user.id})")
            return

        # Create new user
        hashed_password = hash_password(password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            is_admin=is_admin
        )
        db.add(new_user)
        db.flush()  # Get the user ID

        print(f"Created user: {email} (ID: {new_user.id}, Admin: {is_admin})")

        # Handle league and team creation if requested
        if league_name:
            league = db.query(League).filter(League.name == league_name).first()

            if not league:
                # Create new league with this user as commissioner
                invite_code = str(uuid.uuid4())[:8].upper()
                league = League(
                    name=league_name,
                    commissioner=new_user,
                    invite_code=invite_code
                )
                db.add(league)
                db.flush()
                print(f"Created league: {league_name} (ID: {league.id}, Commissioner: {email})")
            else:
                print(f"Using existing league: {league_name} (ID: {league.id})")

            # Create team for user
            if not team_name:
                team_name = f"{email}'s Team"

            # Check if team name already exists in this league
            existing_team = db.query(Team).filter(Team.league_id == league.id, Team.name == team_name).first()
            if existing_team:
                print(f"Warning: Team '{team_name}' already exists in league '{league_name}'. Skipping team creation.")
            else:
                team = Team(
                    name=team_name,
                    owner=new_user,
                    league=league
                )
                db.add(team)
                db.flush()
                print(f"Created team: {team_name} (ID: {team.id}) in league '{league_name}'")

        db.commit()
        print(f"Successfully added user: {email}")

    except Exception as e:
        db.rollback()
        print(f"Error adding user: {e}")
    finally:
        db.close()


def remove_user(email: str):
    """Remove a user and all associated data from the database.

    Args:
        email: Email of user to remove
    """
    init_db()
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email '{email}' not found")
            return

        user_id = user.id
        teams_count = len(user.teams)
        leagues_count = len(user.leagues_owned)

        print(f"Removing user: {email} (ID: {user_id})")
        print(f"  - Teams owned: {teams_count}")
        print(f"  - Leagues commissioned: {leagues_count}")

        # SQLAlchemy will handle cascade deletions for teams and leagues
        db.delete(user)
        db.commit()

        print(f"Successfully removed user: {email}")

    except Exception as e:
        db.rollback()
        print(f"Error removing user: {e}")
    finally:
        db.close()


def list_users():
    """List all users in the database."""
    init_db()
    db = SessionLocal()

    try:
        users = db.query(User).order_by(User.id).all()

        if not users:
            print("No users found in database")
            return

        print(f"Found {len(users)} users:")
        print("-" * 80)
        print(f"{'ID':<4} {'Email':<30} {'Admin':<6} {'Teams':<6} {'Leagues':<8} {'Created':<20}")
        print("-" * 80)

        for user in users:
            teams_count = len(user.teams)
            leagues_count = len(user.leagues_owned)
            created_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "N/A"

            print(f"{user.id:<4} {user.email:<30} {'Yes' if user.is_admin else 'No':<6} {teams_count:<6} {leagues_count:<8} {created_str:<20}")

    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        db.close()


def list_leagues():
    """List all leagues in the database."""
    init_db()
    db = SessionLocal()

    try:
        leagues = db.query(League).order_by(League.id).all()

        if not leagues:
            print("No leagues found in database")
            return

        print(f"Found {len(leagues)} leagues:")
        print("-" * 100)
        print(f"{'ID':<4} {'Name':<25} {'Commissioner':<25} {'Teams':<6} {'Max':<4} {'Active':<7} {'Created':<20}")
        print("-" * 100)

        for league in leagues:
            teams_count = len(league.teams)
            commissioner_email = league.commissioner.email if league.commissioner else "None"
            created_str = league.created_at.strftime("%Y-%m-%d %H:%M:%S") if league.created_at else "N/A"

            print(f"{league.id:<4} {league.name:<25} {commissioner_email:<25} {teams_count:<6} {league.max_teams:<4} {'Yes' if league.is_active else 'No':<7} {created_str:<20}")

    except Exception as e:
        print(f"Error listing leagues: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Management CLI for development / ops tasks.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backfill command
    backfill_parser = subparsers.add_parser("backfill", help="Recompute weekly team_score rows for a whole season.")
    backfill_parser.add_argument("season", type=int, help="The calendar year of the season to backfill (e.g., 2024).")

    # Add user command
    add_user_parser = subparsers.add_parser("add-user", help="Add a new user to the database.")
    add_user_parser.add_argument("email", help="User email address")
    add_user_parser.add_argument("--password", default="password", help="User password (default: 'password')")
    add_user_parser.add_argument("--admin", action="store_true", help="Make user an admin")
    add_user_parser.add_argument("--league-name", help="Add user to this league (create if doesn't exist)")
    add_user_parser.add_argument("--team-name", help="Create team with this name for the user (requires --league-name)")

    # Remove user command
    remove_user_parser = subparsers.add_parser("remove-user", help="Remove a user and all associated data.")
    remove_user_parser.add_argument("email", help="Email of user to remove")

    # List users command
    subparsers.add_parser("list-users", help="List all users in the database.")

    # List leagues command
    subparsers.add_parser("list-leagues", help="List all leagues in the database.")

    args = parser.parse_args()

    if args.command == "backfill":
        backfill_season(args.season)
    elif args.command == "add-user":
        add_user(
            email=args.email,
            password=args.password,
            is_admin=args.admin,
            league_name=args.league_name,
            team_name=args.team_name
        )
    elif args.command == "remove-user":
        remove_user(args.email)
    elif args.command == "list-users":
        list_users()
    elif args.command == "list-leagues":
        list_leagues()
    elif args.command is None:
        parser.print_help()


if __name__ == "__main__":
    main()  # pragma: no cover
