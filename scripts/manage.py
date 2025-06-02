#!/usr/bin/env python3
"""Lightweight management CLI for development / ops tasks.

DATA INGESTION:
* ``backfill <YYYY>`` – ingest player stats for entire season and recompute team scores
* ``ingest-range <start> <end>`` – ingest player data for specific date range

USER MANAGEMENT:
* ``add-user <email> [--password] [--admin] [--league-name] [--team-name]`` – add a new user
* ``remove-user <email>`` – remove a user and all associated data
* ``list-users`` – list all users in the database
* ``list-leagues`` – list all leagues in the database

DATABASE QUERIES:
* ``show-tables`` – show all database tables with row counts
* ``show-data <table> [--limit]`` – show head/tail data from a specific table
* ``show-stats`` – show overall database statistics and insights
* ``show-players [--position] [--search] [--limit]`` – show player data with filtering
* ``show-games [--limit] [--player]`` – show recent games and stat lines
* ``verify-data`` – run data integrity checks
* ``clear-data <table> [--confirm]`` – clear data from a specific table

Examples::

    # Data ingestion
    poetry run python scripts/manage.py backfill 2025
    poetry run python scripts/manage.py ingest-range 2025-05-01 2025-05-31

    # User management
    poetry run python scripts/manage.py add-user test@example.com --password mypass --admin
    poetry run python scripts/manage.py add-user player@example.com --league-name "Demo League" --team-name "Player Team"
    poetry run python scripts/manage.py remove-user test@example.com
    poetry run python scripts/manage.py list-users

    # Database queries
    poetry run python scripts/manage.py show-tables
    poetry run python scripts/manage.py show-data players --limit 20
    poetry run python scripts/manage.py show-stats
    poetry run python scripts/manage.py show-players --position G --search "Wilson"
    poetry run python scripts/manage.py show-games --player "Stewart"
    poetry run python scripts/manage.py verify-data
    poetry run python scripts/manage.py clear-data statlines --confirm
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

import asyncio
from sqlalchemy import func

from app.services.scoring import update_weekly_team_scores  # noqa: E402  pylint: disable=wrong-import-position
from app.models import User, League, Team, Player, StatLine, IngestLog, DraftState, RosterSlot, TeamScore, WeeklyBonus  # noqa: E402  pylint: disable=wrong-import-position
from app.core.database import SessionLocal, init_db  # noqa: E402  pylint: disable=wrong-import-position
from app.core.security import hash_password  # noqa: E402  pylint: disable=wrong-import-position
from app.jobs.ingest import ingest_stat_lines  # noqa: E402  pylint: disable=wrong-import-position


def backfill_season(season: int):
    """Backfill player data and recompute team scores for a whole *season* (calendar year).

    This function:
    1. Ingests player stats for every day of the season
    2. Recomputes weekly team_score rows for the season

    The operation is idempotent - existing data will be updated.
    """
    print(f"Starting backfill for season {season}")
    print("=" * 80)

    # Initialize database
    init_db()

    # Count existing data before we start
    db = SessionLocal()
    try:
        initial_players = db.query(Player).count()
        initial_stat_lines = db.query(StatLine).count()
        print(f"Initial state: {initial_players} players, {initial_stat_lines} stat lines")
    finally:
        db.close()

    # Step 1: Ingest player data for the entire season
    print(f"\nStep 1: Ingesting player data for {season}")
    print("-" * 40)

    start_date = dt.date(season, 1, 1)
    end_date = dt.date(season, 12, 31)
    current_date = start_date

    ingested_days = 0
    failed_days = 0

            # Create a single event loop for all async operations
    async def ingest_all_dates():
        nonlocal ingested_days, failed_days, current_date
        while current_date <= end_date:
            try:
                print(f"Ingesting data for {current_date.strftime('%Y-%m-%d')}...", end=" ")
                await ingest_stat_lines(current_date)
                print("✓")
                ingested_days += 1
            except Exception as e:
                print(f"✗ Error: {e}")
                failed_days += 1

            current_date += dt.timedelta(days=1)

    asyncio.run(ingest_all_dates())

    print(f"\nIngestion complete: {ingested_days} days processed, {failed_days} days failed")

    # Check how much data we have now
    db = SessionLocal()
    try:
        final_players = db.query(Player).count()
        final_stat_lines = db.query(StatLine).count()
        season_stat_lines = db.query(StatLine).filter(
            StatLine.game_date >= dt.datetime(season, 1, 1),
            StatLine.game_date < dt.datetime(season + 1, 1, 1)
        ).count()

        print(f"After ingestion: {final_players} players (+{final_players - initial_players}), "
              f"{final_stat_lines} total stat lines (+{final_stat_lines - initial_stat_lines})")
        print(f"Stat lines for {season}: {season_stat_lines}")

        # Show some example players for verification
        sample_players = db.query(Player).limit(5).all()
        if sample_players:
            print(f"\nSample players imported:")
            for player in sample_players:
                print(f"  - {player.full_name} ({player.position or 'N/A'})")
    finally:
        db.close()

    # Step 2: Recompute weekly team scores
    print(f"\nStep 2: Recomputing weekly team scores for {season}")
    print("-" * 40)

    weeks_run: list[int] = []

    # Determine the number of ISO weeks in the target ISO year `season`
    last_week_check_date = dt.date(season, 12, 28)
    _, num_iso_weeks_in_season, _ = last_week_check_date.isocalendar()

    for week_num in range(1, num_iso_weeks_in_season + 1):
        try:
            # Get the date for Monday of week_num in the specified ISO year `season`
            monday_of_iso_week = dt.datetime.strptime(f'{season}-{week_num}-1', "%G-%V-%u").date()
            print(f"Updating scores for week {week_num} ({monday_of_iso_week})...", end=" ")
            update_weekly_team_scores(monday_of_iso_week)
            print("✓")
            weeks_run.append(week_num)
        except ValueError:
            print(f"Warning: Invalid ISO week {season}-{week_num}. Skipping.")
            continue
        except Exception as e:
            print(f"✗ Error updating week {week_num}: {e}")
            continue

    if weeks_run:
        print(f"\nScore calculation complete: processed {len(weeks_run)} ISO weeks ({weeks_run[0]}–{weeks_run[-1]})")
    else:
        print(f"\nScore calculation complete: no ISO weeks processed")

    # Show final statistics
    print(f"\n{'='*80}")
    print(f"BACKFILL SUMMARY FOR {season}")
    print(f"{'='*80}")
    print(f"✓ Player data ingestion: {ingested_days} days processed, {failed_days} failed")
    print(f"✓ Score calculation: {len(weeks_run)} weeks processed")

    # Show any recent ingest errors
    db = SessionLocal()
    try:
        recent_errors = db.query(IngestLog).filter(
            IngestLog.message.like("ERROR:%")
        ).order_by(IngestLog.timestamp.desc()).limit(5).all()

        if recent_errors:
            print(f"\nRecent ingest errors (showing last 5):")
            for error in recent_errors:
                print(f"  {error.timestamp}: {error.message}")
    finally:
        db.close()

    print(f"\nBackfill complete for season {season}!")


def show_tables():
    """Show all database tables with row counts."""
    print("Database Tables Overview")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    try:
        tables_info = [
            ("Users", User),
            ("Leagues", League),
            ("Teams", Team),
            ("Players", Player),
            ("Stat Lines", StatLine),
            ("Draft States", DraftState),
            ("Roster Slots", RosterSlot),
            ("Team Scores", TeamScore),
            ("Weekly Bonuses", WeeklyBonus),
            ("Ingest Logs", IngestLog),
        ]

        print(f"{'Table':<15} {'Count':<10} {'Description'}")
        print("-" * 60)

        for table_name, model_class in tables_info:
            try:
                count = db.query(model_class).count()
                descriptions = {
                    "Users": "Registered users",
                    "Leagues": "Fantasy leagues",
                    "Teams": "Teams in leagues",
                    "Players": "WNBA players",
                    "Stat Lines": "Game statistics",
                    "Draft States": "League draft status",
                    "Roster Slots": "Player-team assignments",
                    "Team Scores": "Weekly fantasy scores",
                    "Weekly Bonuses": "Bonus points",
                    "Ingest Logs": "Data import logs",
                }
                desc = descriptions.get(table_name, "")
                print(f"{table_name:<15} {count:<10} {desc}")
            except Exception as e:
                print(f"{table_name:<15} {'ERROR':<10} {str(e)[:30]}")

    finally:
        db.close()


def show_data(table_name: str, limit: int = 10):
    """Show head/tail data from a specific table."""
    table_map = {
        "users": (User, ["id", "email", "is_admin", "created_at"]),
        "leagues": (League, ["id", "name", "commissioner_id", "max_teams", "is_active", "created_at"]),
        "teams": (Team, ["id", "name", "owner_id", "league_id", "moves_this_week"]),
        "players": (Player, ["id", "full_name", "position", "team_abbr"]),
        "statlines": (StatLine, ["id", "player_id", "game_date", "points", "rebounds", "assists"]),
        "draftstates": (DraftState, ["id", "league_id", "status", "current_round", "current_pick_index"]),
        "rosterslots": (RosterSlot, ["id", "team_id", "player_id", "position", "is_starter"]),
        "teamscores": (TeamScore, ["id", "team_id", "week", "score"]),
        "weeklybonuses": (WeeklyBonus, ["id", "week_id", "player_id", "team_id", "category", "points"]),
        "ingestlogs": (IngestLog, ["id", "timestamp", "provider", "message"]),
    }

    if table_name.lower() not in table_map:
        print(f"❌ Unknown table: {table_name}")
        print(f"Available tables: {', '.join(table_map.keys())}")
        return

    model_class, columns = table_map[table_name.lower()]

    print(f"Table: {table_name.upper()}")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    try:
        total_count = db.query(model_class).count()

        if total_count == 0:
            print("📋 No data found in this table")
            return

        print(f"Total rows: {total_count}")
        print(f"Showing first {min(limit, total_count)} rows:")
        print("-" * 80)

        # Print header
        header = " | ".join(f"{col:<15}" for col in columns)
        print(header)
        print("-" * len(header))

        # Get and display data
        records = db.query(model_class).limit(limit).all()

        for record in records:
            row_data = []
            for col in columns:
                value = getattr(record, col, "N/A")
                if value is None:
                    value = "NULL"
                elif isinstance(value, dt.datetime):
                    value = value.strftime("%Y-%m-%d %H:%M")
                elif isinstance(value, str) and len(value) > 15:
                    value = value[:12] + "..."
                row_data.append(str(value)[:15])

            row = " | ".join(f"{val:<15}" for val in row_data)
            print(row)

        if total_count > limit:
            print(f"\n... and {total_count - limit} more rows")

    except Exception as e:
        print(f"❌ Error querying table: {e}")
    finally:
        db.close()


def show_stats():
    """Show overall database statistics and insights."""
    print("Database Statistics & Insights")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    try:
        # Basic counts
        users_count = db.query(User).count()
        leagues_count = db.query(League).count()
        teams_count = db.query(Team).count()
        players_count = db.query(Player).count()
        stat_lines_count = db.query(StatLine).count()

        print(f"📊 OVERVIEW")
        print(f"Users: {users_count} | Leagues: {leagues_count} | Teams: {teams_count}")
        print(f"Players: {players_count} | Stat Lines: {stat_lines_count}")

        # League statistics
        if leagues_count > 0:
            print(f"\n🏀 LEAGUE STATS")
            active_leagues = db.query(League).filter(League.is_active == True).count()
            print(f"Active leagues: {active_leagues}/{leagues_count}")

            # Teams per league
            avg_teams = db.query(Team).count() / leagues_count if leagues_count > 0 else 0
            print(f"Average teams per league: {avg_teams:.1f}")

        # Player statistics
        if players_count > 0:
            print(f"\n👥 PLAYER STATS")

            # Position breakdown
            positions = db.query(Player.position, func.count(Player.id)).group_by(Player.position).all()
            print("Position breakdown:")
            for pos, count in positions:
                pos_name = pos or "Unknown"
                print(f"  {pos_name}: {count}")

            # Players with stats
            players_with_stats = db.query(StatLine.player_id).distinct().count()
            print(f"Players with game stats: {players_with_stats}/{players_count}")

        # Game statistics
        if stat_lines_count > 0:
            print(f"\n📈 GAME STATS")

            # Date range
            date_range = db.query(
                func.min(StatLine.game_date),
                func.max(StatLine.game_date)
            ).first()
            if date_range[0] and date_range[1]:
                print(f"Date range: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")

            # Top scorer
            top_scorer = db.query(StatLine).order_by(StatLine.points.desc()).first()
            if top_scorer:
                player_name = db.query(Player).filter(Player.id == top_scorer.player_id).first().full_name
                print(f"Highest single-game points: {top_scorer.points} by {player_name}")

        # Draft statistics
        draft_count = db.query(DraftState).count()
        if draft_count > 0:
            print(f"\n🎯 DRAFT STATS")
            active_drafts = db.query(DraftState).filter(DraftState.status == "active").count()
            completed_drafts = db.query(DraftState).filter(DraftState.status == "completed").count()
            print(f"Active drafts: {active_drafts}")
            print(f"Completed drafts: {completed_drafts}")

        # Recent activity
        print(f"\n🕒 RECENT ACTIVITY")
        recent_users = db.query(User).filter(User.created_at >= dt.datetime.utcnow() - dt.timedelta(days=7)).count()
        print(f"New users (last 7 days): {recent_users}")

        recent_stat_lines = db.query(StatLine).filter(StatLine.game_date >= dt.datetime.utcnow() - dt.timedelta(days=7)).count()
        print(f"New stat lines (last 7 days): {recent_stat_lines}")

        # Ingest errors
        recent_errors = db.query(IngestLog).filter(
            IngestLog.message.like("ERROR:%"),
            IngestLog.timestamp >= dt.datetime.utcnow() - dt.timedelta(days=7)
        ).count()
        if recent_errors > 0:
            print(f"⚠️  Recent ingest errors (last 7 days): {recent_errors}")

    except Exception as e:
        print(f"❌ Error generating statistics: {e}")
    finally:
        db.close()


def show_players(position: str = None, limit: int = 20, search: str = None):
    """Show player data with optional filtering."""
    print("WNBA Players")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    try:
        query = db.query(Player)

        # Apply filters
        if position:
            query = query.filter(Player.position == position.upper())

        if search:
            query = query.filter(Player.full_name.ilike(f"%{search}%"))

        total_count = query.count()

        if total_count == 0:
            print("📋 No players found matching criteria")
            return

        players = query.order_by(Player.full_name).limit(limit).all()

        # Get stats for these players
        player_ids = [p.id for p in players]
        stats_query = db.query(
            StatLine.player_id,
            func.count(StatLine.id).label('games'),
            func.avg(StatLine.points).label('avg_points'),
            func.sum(StatLine.points).label('total_points')
        ).filter(StatLine.player_id.in_(player_ids)).group_by(StatLine.player_id)

        stats_dict = {stat.player_id: stat for stat in stats_query.all()}

        print(f"Showing {len(players)}/{total_count} players")
        if position:
            print(f"Position filter: {position}")
        if search:
            print(f"Search filter: '{search}'")

        print("-" * 80)
        print(f"{'Name':<25} {'Pos':<4} {'Team':<5} {'Games':<6} {'Avg Pts':<8} {'Total Pts'}")
        print("-" * 80)

        for player in players:
            stats = stats_dict.get(player.id)

            name = player.full_name[:24]
            pos = player.position or "N/A"
            team = player.team_abbr or "N/A"

            if stats:
                games = stats.games
                avg_pts = f"{stats.avg_points:.1f}" if stats.avg_points else "0.0"
                total_pts = f"{stats.total_points:.0f}" if stats.total_points else "0"
            else:
                games = 0
                avg_pts = "0.0"
                total_pts = "0"

            print(f"{name:<25} {pos:<4} {team:<5} {games:<6} {avg_pts:<8} {total_pts}")

        if total_count > limit:
            print(f"\n... and {total_count - limit} more players")

        # Show position summary
        print(f"\n📊 Position Summary:")
        positions = db.query(Player.position, func.count(Player.id)).group_by(Player.position).all()
        for pos, count in sorted(positions):
            pos_name = pos or "Unknown"
            print(f"  {pos_name}: {count} players")

    except Exception as e:
        print(f"❌ Error querying players: {e}")
    finally:
        db.close()


def show_games(limit: int = 20, player_name: str = None):
    """Show recent games and stat lines."""
    print("Recent Games & Stat Lines")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    try:
        query = db.query(StatLine).join(Player)

        if player_name:
            query = query.filter(Player.full_name.ilike(f"%{player_name}%"))

        stat_lines = query.order_by(StatLine.game_date.desc()).limit(limit).all()

        if not stat_lines:
            print("📋 No stat lines found")
            return

        print(f"Showing {len(stat_lines)} most recent stat lines")
        if player_name:
            print(f"Player filter: '{player_name}'")

        print("-" * 80)
        print(f"{'Date':<12} {'Player':<20} {'Pos':<4} {'Pts':<4} {'Reb':<4} {'Ast':<4} {'Stl':<4} {'Blk'}")
        print("-" * 80)

        for stat in stat_lines:
            date = stat.game_date.strftime('%Y-%m-%d')
            name = stat.player.full_name[:19]
            pos = stat.player.position or "N/A"

            print(f"{date:<12} {name:<20} {pos:<4} {stat.points:<4.0f} {stat.rebounds:<4.0f} {stat.assists:<4.0f} {stat.steals:<4.0f} {stat.blocks:<4.0f}")

    except Exception as e:
        print(f"❌ Error querying games: {e}")
    finally:
        db.close()


def verify_data():
    """Run data integrity checks."""
    print("Data Integrity Verification")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    try:
        issues_found = 0

        print("🔍 Running integrity checks...\n")

        # Check 1: Users without teams in active leagues
        users_without_teams = db.query(User).outerjoin(Team).filter(Team.id == None).count()
        if users_without_teams > 0:
            print(f"ℹ️  {users_without_teams} users have no teams (this may be normal)")

        # Check 2: Teams without owners
        teams_without_owners = db.query(Team).filter(Team.owner_id == None).count()
        if teams_without_owners > 0:
            print(f"⚠️  {teams_without_owners} teams have no owners")
            issues_found += 1

        # Check 3: Teams in non-existent leagues
        orphaned_teams = db.query(Team).outerjoin(League).filter(League.id == None).count()
        if orphaned_teams > 0:
            print(f"❌ {orphaned_teams} teams reference non-existent leagues")
            issues_found += 1

        # Check 4: Stat lines for non-existent players
        orphaned_stats = db.query(StatLine).outerjoin(Player).filter(Player.id == None).count()
        if orphaned_stats > 0:
            print(f"❌ {orphaned_stats} stat lines reference non-existent players")
            issues_found += 1

        # Check 5: Roster slots for non-existent teams/players
        orphaned_roster_teams = db.query(RosterSlot).outerjoin(Team).filter(Team.id == None).count()
        orphaned_roster_players = db.query(RosterSlot).outerjoin(Player).filter(Player.id == None).count()

        if orphaned_roster_teams > 0:
            print(f"❌ {orphaned_roster_teams} roster slots reference non-existent teams")
            issues_found += 1

        if orphaned_roster_players > 0:
            print(f"❌ {orphaned_roster_players} roster slots reference non-existent players")
            issues_found += 1

        # Check 6: Draft states for non-existent leagues
        orphaned_drafts = db.query(DraftState).outerjoin(League).filter(League.id == None).count()
        if orphaned_drafts > 0:
            print(f"❌ {orphaned_drafts} draft states reference non-existent leagues")
            issues_found += 1

        # Check 7: Duplicate roster assignments
        duplicate_rosters = db.query(RosterSlot.team_id, RosterSlot.player_id, func.count()).group_by(
            RosterSlot.team_id, RosterSlot.player_id
        ).having(func.count() > 1).count()

        if duplicate_rosters > 0:
            print(f"⚠️  {duplicate_rosters} duplicate player-team roster assignments")
            issues_found += 1

        # Summary
        print(f"\n{'='*80}")
        if issues_found == 0:
            print("✅ All integrity checks passed! Database looks healthy.")
        else:
            print(f"⚠️  Found {issues_found} potential issues that may need attention.")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
    finally:
        db.close()


def clear_data(table_name: str, confirm: bool = False):
    """Clear data from a specific table (with confirmation)."""
    table_map = {
        "statlines": (StatLine, "Stat Lines"),
        "ingestlogs": (IngestLog, "Ingest Logs"),
        "teamscores": (TeamScore, "Team Scores"),
        "weeklybonuses": (WeeklyBonus, "Weekly Bonuses"),
        "rosterslots": (RosterSlot, "Roster Slots"),
        "draftstates": (DraftState, "Draft States"),
    }

    if table_name.lower() not in table_map:
        print(f"❌ Cannot clear table: {table_name}")
        print(f"Clearable tables: {', '.join(table_map.keys())}")
        print("ℹ️  Critical tables (users, leagues, teams, players) cannot be cleared via this command")
        return

    model_class, display_name = table_map[table_name.lower()]

    init_db()
    db = SessionLocal()

    try:
        count = db.query(model_class).count()

        if count == 0:
            print(f"📋 Table {display_name} is already empty")
            return

        print(f"⚠️  About to delete {count} records from {display_name}")

        if not confirm:
            response = input("Are you sure? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return

        deleted = db.query(model_class).delete()
        db.commit()

        print(f"✅ Deleted {deleted} records from {display_name}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing data: {e}")
    finally:
        db.close()


def ingest_data_range(start_date: str, end_date: str):
    """Ingest player data for a specific date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
        end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}")
        return

    if start > end:
        print("Error: Start date must be before or equal to end date")
        return

    print(f"Ingesting player data from {start} to {end}")
    print("=" * 60)

    # Initialize database
    init_db()

    # Count existing data
    db = SessionLocal()
    try:
        initial_players = db.query(Player).count()
        initial_stat_lines = db.query(StatLine).count()
        print(f"Initial state: {initial_players} players, {initial_stat_lines} stat lines")
    finally:
        db.close()

    current_date = start
    ingested_days = 0
    failed_days = 0

        # Create a single event loop for all async operations
    async def ingest_range_dates():
        nonlocal current_date, ingested_days, failed_days
        while current_date <= end:
            try:
                print(f"Ingesting {current_date.strftime('%Y-%m-%d')}...", end=" ")
                await ingest_stat_lines(current_date)
                print("✓")
                ingested_days += 1
            except Exception as e:
                print(f"✗ Error: {e}")
                failed_days += 1

            current_date += dt.timedelta(days=1)

    asyncio.run(ingest_range_dates())

    # Final statistics
    db = SessionLocal()
    try:
        final_players = db.query(Player).count()
        final_stat_lines = db.query(StatLine).count()
        range_stat_lines = db.query(StatLine).filter(
            StatLine.game_date >= dt.datetime.combine(start, dt.time()),
            StatLine.game_date < dt.datetime.combine(end + dt.timedelta(days=1), dt.time())
        ).count()

        print(f"\nFinal state: {final_players} players (+{final_players - initial_players}), "
              f"{final_stat_lines} total stat lines (+{final_stat_lines - initial_stat_lines})")
        print(f"Stat lines in range: {range_stat_lines}")

        # Show some example players
        if final_players > initial_players:
            sample_players = db.query(Player).order_by(Player.id.desc()).limit(5).all()
            print(f"\nRecently added/updated players:")
            for player in sample_players:
                print(f"  - {player.full_name} ({player.position or 'N/A'})")
    finally:
        db.close()

    print(f"\nIngest complete: {ingested_days} days processed, {failed_days} failed")


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

        print(f"✓ Created user: {email} (ID: {new_user.id}, Admin: {is_admin})")

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
                print(f"✓ Created league: {league_name} (ID: {league.id}, Commissioner: {email})")
            else:
                print(f"ℹ Using existing league: {league_name} (ID: {league.id})")

            # Create team for user
            if not team_name:
                team_name = f"{email}'s Team"

            # Check if team name already exists in this league
            existing_team = db.query(Team).filter(Team.league_id == league.id, Team.name == team_name).first()
            if existing_team:
                print(f"⚠ Warning: Team '{team_name}' already exists in league '{league_name}'. Skipping team creation.")
            else:
                team = Team(
                    name=team_name,
                    owner=new_user,
                    league=league
                )
                db.add(team)
                db.flush()
                print(f"✓ Created team: {team_name} (ID: {team.id}) in league '{league_name}'")

        db.commit()
        print(f"✓ Successfully added user: {email}")

    except Exception as e:
        db.rollback()
        print(f"✗ Error adding user: {e}")
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
    backfill_parser = subparsers.add_parser("backfill", help="Ingest player data and recompute team scores for a whole season.")
    backfill_parser.add_argument("season", type=int, help="The calendar year of the season to backfill (e.g., 2025).")

    # Ingest range command
    ingest_parser = subparsers.add_parser("ingest-range", help="Ingest player data for a specific date range.")
    ingest_parser.add_argument("start_date", help="Start date in YYYY-MM-DD format")
    ingest_parser.add_argument("end_date", help="End date in YYYY-MM-DD format")

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

    # Database query commands
    subparsers.add_parser("show-tables", help="Show all database tables with row counts.")

    show_data_parser = subparsers.add_parser("show-data", help="Show head/tail data from a specific table.")
    show_data_parser.add_argument("table", help="Table name (users, leagues, teams, players, statlines, etc.)")
    show_data_parser.add_argument("--limit", type=int, default=10, help="Number of rows to show (default: 10)")

    subparsers.add_parser("show-stats", help="Show overall database statistics and insights.")

    show_players_parser = subparsers.add_parser("show-players", help="Show player data with optional filtering.")
    show_players_parser.add_argument("--position", help="Filter by position (G, F, C)")
    show_players_parser.add_argument("--search", help="Search player names")
    show_players_parser.add_argument("--limit", type=int, default=20, help="Number of players to show")

    show_games_parser = subparsers.add_parser("show-games", help="Show recent games and stat lines.")
    show_games_parser.add_argument("--limit", type=int, default=20, help="Number of stat lines to show")
    show_games_parser.add_argument("--player", help="Filter by player name")

    subparsers.add_parser("verify-data", help="Run data integrity checks.")

    clear_data_parser = subparsers.add_parser("clear-data", help="Clear data from a specific table (with confirmation).")
    clear_data_parser.add_argument("table", help="Table to clear (statlines, ingestlogs, teamscores, etc.)")
    clear_data_parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    if args.command == "backfill":
        backfill_season(args.season)
    elif args.command == "ingest-range":
        ingest_data_range(args.start_date, args.end_date)
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
    elif args.command == "show-tables":
        show_tables()
    elif args.command == "show-data":
        show_data(args.table, args.limit)
    elif args.command == "show-stats":
        show_stats()
    elif args.command == "show-players":
        show_players(args.position, args.limit, args.search)
    elif args.command == "show-games":
        show_games(args.limit, args.player)
    elif args.command == "verify-data":
        verify_data()
    elif args.command == "clear-data":
        clear_data(args.table, args.confirm)
    elif args.command is None:
        parser.print_help()


if __name__ == "__main__":
    main()  # pragma: no cover
