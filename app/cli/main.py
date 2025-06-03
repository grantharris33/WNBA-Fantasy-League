#!/usr/bin/env python3
"""
CLI management interface for the WNBA Fantasy League application.

Provides commands for data ingestion, user management, database operations,
and the new backfill system.
"""

import asyncio
import datetime as dt
from datetime import date, datetime
from pathlib import Path
import sys
from typing import Optional

import click
from sqlalchemy import func

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models import (
    User, League, Team, Player, StatLine, IngestLog,
    DraftState, RosterSlot, TeamScore, WeeklyBonus,
    IngestionRun, IngestionQueue
)
from app.services.backfill import BackfillService
from app.services.scoring import update_weekly_team_scores
from app.jobs.ingest import ingest_stat_lines
from app.jobs.ingest_teams import ingest_wnba_teams
from app.jobs.ingest_players import ingest_player_profiles
from app.cli.admin import admin


@click.group()
def cli():
    """WNBA Fantasy League Management CLI."""
    pass


# =============================================================================
# BACKFILL COMMANDS
# =============================================================================

@cli.group()
def backfill():
    """Historical data backfill and recovery commands."""
    pass


@backfill.command()
@click.option('--season', type=int, required=True, help='Season year to backfill')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without actually doing it')
def season(season: int, start_date: Optional[datetime], end_date: Optional[datetime], dry_run: bool):
    """Backfill historical data for a season."""
    click.echo(f"Starting backfill for season {season}")

    if dry_run:
        click.echo("🔍 DRY RUN MODE - No data will be ingested")

    init_db()

    start_date_obj = start_date.date() if start_date else None
    end_date_obj = end_date.date() if end_date else None

    async def run_backfill():
        async with BackfillService() as service:
            run = await service.backfill_season(
                year=season,
                start_date=start_date_obj,
                end_date=end_date_obj,
                dry_run=dry_run
            )

            click.echo(f"\n📊 Backfill Summary:")
            click.echo(f"Status: {run.status}")
            click.echo(f"Games found: {run.games_found}")
            click.echo(f"Games processed: {run.games_processed}")
            click.echo(f"Players updated: {run.players_updated}")

            if run.errors and run.errors != "[]":
                click.echo(f"⚠️  Errors encountered: {run.errors}")

    asyncio.run(run_backfill())


@backfill.command()
@click.option('--check-missing', is_flag=True, help='Check for missing games in recent days')
@click.option('--days-back', type=int, default=7, help='Number of days to check back')
def health_check(check_missing: bool, days_back: int):
    """Check ingestion system health and find missing games."""
    click.echo("🏥 Ingestion Health Check")
    click.echo("=" * 50)

    init_db()

    async def run_health_check():
        async with BackfillService() as service:
            health = service.get_ingestion_health(days_back)

            click.echo(f"📅 Period: Last {health['period_days']} days")
            click.echo(f"🏃 Recent runs: {health['recent_runs']}")
            click.echo(f"✅ Successful: {health['successful_runs']}")
            click.echo(f"❌ Failed: {health['failed_runs']}")
            click.echo(f"📈 Recent stat lines: {health['recent_stat_lines']}")
            click.echo(f"⚠️  Recent errors: {health['recent_errors']}")

            if health['last_successful_run']:
                click.echo(f"🕒 Last successful run: {health['last_successful_run']}")

            queue_status = health.get('queue_status', {})
            if queue_status:
                click.echo(f"\n📋 Queue Status:")
                for status, count in queue_status.items():
                    click.echo(f"  {status}: {count}")

            if check_missing:
                click.echo(f"\n🔍 Checking for missing games...")
                end_date = date.today()
                start_date = end_date - dt.timedelta(days=days_back)

                missing_games = await service.find_missing_games(start_date, end_date)

                if missing_games:
                    click.echo(f"❌ Found {len(missing_games)} missing games:")
                    for game_id in missing_games[:10]:  # Show first 10
                        click.echo(f"  - {game_id}")
                    if len(missing_games) > 10:
                        click.echo(f"  ... and {len(missing_games) - 10} more")
                else:
                    click.echo("✅ No missing games found")

    asyncio.run(run_health_check())


@backfill.command()
@click.argument('game_id')
@click.option('--force', is_flag=True, help='Force reprocessing even if game exists')
def reprocess_game(game_id: str, force: bool):
    """Reprocess a specific game."""
    click.echo(f"🔄 Reprocessing game {game_id}")

    init_db()

    async def run_reprocess():
        async with BackfillService() as service:
            result = await service.reprocess_game(game_id, force)

            click.echo(f"Status: {result['status']}")
            if result['status'] == 'skipped':
                click.echo(f"Reason: {result['reason']}")
            elif result['status'] == 'queued':
                click.echo(f"Game date: {result['game_date']}")
                click.echo(f"Force mode: {result['force']}")
            elif result['status'] == 'failed':
                click.echo(f"Error: {result['reason']}")

    asyncio.run(run_reprocess())


# =============================================================================
# DATA INGESTION COMMANDS
# =============================================================================

@cli.group()
def ingest():
    """Data ingestion commands."""
    pass


@ingest.command()
@click.argument('start_date')
@click.argument('end_date')
def range(start_date: str, end_date: str):
    """Ingest player data for a specific date range (YYYY-MM-DD format)."""
    try:
        start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
        end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as e:
        click.echo(f"❌ Error: Invalid date format. Use YYYY-MM-DD. {e}")
        return

    if start > end:
        click.echo("❌ Error: Start date must be before or equal to end date")
        return

    click.echo(f"📅 Ingesting data from {start} to {end}")

    init_db()

    async def run_ingest():
        current_date = start
        success_count = 0
        error_count = 0

        while current_date <= end:
            try:
                click.echo(f"Processing {current_date}...", nl=False)
                await ingest_stat_lines(current_date)
                click.echo(" ✅")
                success_count += 1
            except Exception as e:
                click.echo(f" ❌ Error: {e}")
                error_count += 1

            current_date += dt.timedelta(days=1)

        click.echo(f"\n📊 Summary: {success_count} successful, {error_count} failed")

    asyncio.run(run_ingest())


@ingest.command()
def teams():
    """Ingest all WNBA team information."""
    click.echo("🏀 Starting WNBA teams ingestion...")

    init_db()

    async def run_teams_ingest():
        try:
            await ingest_wnba_teams()
            click.echo("✅ Teams ingestion completed successfully")
        except Exception as e:
            click.echo(f"❌ Error during teams ingestion: {e}")
            raise

    asyncio.run(run_teams_ingest())


@ingest.command()
def players():
    """Ingest all WNBA player profiles and biographical data."""
    click.echo("👥 Starting WNBA players ingestion...")
    click.echo("⚠️  This may take several minutes due to API rate limits...")

    init_db()

    async def run_players_ingest():
        try:
            await ingest_player_profiles()
            click.echo("✅ Players ingestion completed successfully")
        except Exception as e:
            click.echo(f"❌ Error during players ingestion: {e}")
            raise

    asyncio.run(run_players_ingest())


@ingest.command()
def all():
    """Ingest all WNBA teams and player data (not stat lines)."""
    click.echo("🏀 Starting complete WNBA teams and players ingestion...")
    click.echo("⚠️  This may take several minutes due to API rate limits...")

    init_db()

    async def run_all_ingest():
        try:
            # First ingest teams
            click.echo("\n1️⃣ Ingesting teams...")
            await ingest_wnba_teams()
            click.echo("✅ Teams ingestion completed")

            # Then ingest players
            click.echo("\n2️⃣ Ingesting players...")
            await ingest_player_profiles()
            click.echo("✅ Players ingestion completed")

            click.echo("\n🎉 All teams and players data ingestion completed successfully!")

        except Exception as e:
            click.echo(f"❌ Error during ingestion: {e}")
            raise

    asyncio.run(run_all_ingest())


# =============================================================================
# USER MANAGEMENT COMMANDS
# =============================================================================

@cli.group()
def users():
    """User management commands."""
    pass


@users.command()
@click.argument('email')
@click.option('--password', default='password', help='User password')
@click.option('--admin', is_flag=True, help='Make user an admin')
@click.option('--league-name', help='Add user to this league (create if needed)')
@click.option('--team-name', help='Create team with this name')
def add(email: str, password: str, admin: bool, league_name: Optional[str], team_name: Optional[str]):
    """Add a new user."""
    init_db()
    db = SessionLocal()

    try:
        # Check if user exists
        if db.query(User).filter(User.email == email).first():
            click.echo(f"❌ User {email} already exists")
            return

        # Create user
        hashed_password = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_admin=admin
        )
        db.add(user)
        db.flush()

        click.echo(f"✅ Created user: {email} (Admin: {admin})")

        # Handle league/team creation
        if league_name:
            league = db.query(League).filter(League.name == league_name).first()

            if not league:
                import uuid
                league = League(
                    name=league_name,
                    commissioner=user,
                    invite_code=str(uuid.uuid4())[:8].upper()
                )
                db.add(league)
                db.flush()
                click.echo(f"✅ Created league: {league_name}")

            if team_name:
                team = Team(
                    name=team_name,
                    owner=user,
                    league=league
                )
                db.add(team)
                click.echo(f"✅ Created team: {team_name}")

        db.commit()

    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@users.command()
@click.argument('email')
def remove(email: str):
    """Remove a user and all associated data."""
    init_db()
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User {email} not found")
            return

        click.echo(f"Removing user: {email}")
        db.delete(user)
        db.commit()
        click.echo("✅ User removed successfully")

    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@users.command()
def list():
    """List all users."""
    init_db()
    db = SessionLocal()

    try:
        users = db.query(User).order_by(User.id).all()

        if not users:
            click.echo("No users found")
            return

        click.echo(f"Found {len(users)} users:")
        click.echo("-" * 80)
        click.echo(f"{'ID':<4} {'Email':<30} {'Admin':<6} {'Teams':<6} {'Created':<20}")
        click.echo("-" * 80)

        for user in users:
            teams_count = len(user.teams)
            created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            admin_str = "Yes" if user.is_admin else "No"

            click.echo(f"{user.id:<4} {user.email:<30} {admin_str:<6} {teams_count:<6} {created:<20}")

    finally:
        db.close()


# =============================================================================
# LINEUP MANAGEMENT COMMANDS
# =============================================================================

@cli.group()
def lineup():
    """Weekly lineup management commands."""
    pass


@lineup.command()
@click.option('--week-id', type=int, help='Specific week ID to lock (format: YYYYWW, e.g., 202502)')
@click.option('--current', is_flag=True, help='Lock current week')
@click.option('--dry-run', is_flag=True, help='Show what would be locked without actually doing it')
def lock(week_id: Optional[int], current: bool, dry_run: bool):
    """Lock lineups for a specific week."""
    if not week_id and not current:
        click.echo("❌ Error: Must specify either --week-id or --current")
        return

    if week_id and current:
        click.echo("❌ Error: Cannot specify both --week-id and --current")
        return

    init_db()

    from app.services.lineup import LineupService

    db = SessionLocal()
    try:
        lineup_service = LineupService(db)

        if current:
            week_id = lineup_service.get_current_week_id()
            click.echo(f"🗓️  Using current week: {week_id}")

        if dry_run:
            click.echo("🔍 DRY RUN MODE - No lineups will be locked")

            # Get all teams
            teams = db.query(Team).all()
            click.echo(f"📊 Would process {len(teams)} teams for week {week_id}")

            for team in teams:
                # Check if already locked
                from app.models import WeeklyLineup
                existing = db.query(WeeklyLineup).filter(
                    WeeklyLineup.team_id == team.id,
                    WeeklyLineup.week_id == week_id
                ).first()

                status = "already locked" if existing else "would lock"
                click.echo(f"  - {team.name}: {status}")
        else:
            click.echo(f"🔒 Locking lineups for week {week_id}...")
            teams_processed = lineup_service.lock_weekly_lineups(week_id)
            click.echo(f"✅ Successfully locked lineups for {teams_processed} teams")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@lineup.command()
@click.option('--week-id', type=int, help='Week ID to check (format: YYYYWW)')
@click.option('--team-id', type=int, help='Specific team ID to check')
def status(week_id: Optional[int], team_id: Optional[int]):
    """Check lineup lock status for teams."""
    init_db()

    from app.services.lineup import LineupService

    db = SessionLocal()
    try:
        lineup_service = LineupService(db)

        if not week_id:
            week_id = lineup_service.get_current_week_id()
            click.echo(f"🗓️  Using current week: {week_id}")

        # Query teams
        teams_query = db.query(Team)
        if team_id:
            teams_query = teams_query.filter(Team.id == team_id)
        teams = teams_query.all()

        if not teams:
            click.echo("❌ No teams found")
            return

        click.echo(f"📊 Lineup status for week {week_id}:")
        click.echo("=" * 50)

        locked_count = 0
        unlocked_count = 0

        for team in teams:
            from app.models import WeeklyLineup
            lineup = db.query(WeeklyLineup).filter(
                WeeklyLineup.team_id == team.id,
                WeeklyLineup.week_id == week_id
            ).first()

            if lineup:
                click.echo(f"🔒 {team.name}: LOCKED (at {lineup.locked_at})")
                locked_count += 1
            else:
                click.echo(f"🔓 {team.name}: UNLOCKED")
                unlocked_count += 1

        click.echo("=" * 50)
        click.echo(f"📈 Summary: {locked_count} locked, {unlocked_count} unlocked")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


# =============================================================================
# DATABASE COMMANDS
# =============================================================================

@cli.group()
def db():
    """Database inspection and management commands."""
    pass


@db.command()
def tables():
    """Show all database tables with row counts."""
    init_db()
    db = SessionLocal()

    try:
        tables_info = [
            ("Users", User),
            ("Leagues", League),
            ("Teams", Team),
            ("Players", Player),
            ("Stat Lines", StatLine),
            ("Ingestion Runs", IngestionRun),
            ("Ingestion Queue", IngestionQueue),
            ("Draft States", DraftState),
            ("Roster Slots", RosterSlot),
            ("Team Scores", TeamScore),
            ("Weekly Bonuses", WeeklyBonus),
            ("Ingest Logs", IngestLog),
        ]

        click.echo("📊 Database Tables Overview")
        click.echo("=" * 60)
        click.echo(f"{'Table':<20} {'Count':<10} {'Description'}")
        click.echo("-" * 60)

        for table_name, model_class in tables_info:
            try:
                count = db.query(model_class).count()
                descriptions = {
                    "Users": "Registered users",
                    "Leagues": "Fantasy leagues",
                    "Teams": "Teams in leagues",
                    "Players": "WNBA players",
                    "Stat Lines": "Game statistics",
                    "Ingestion Runs": "Backfill tracking",
                    "Ingestion Queue": "Queued games",
                    "Draft States": "League draft status",
                    "Roster Slots": "Player assignments",
                    "Team Scores": "Weekly scores",
                    "Weekly Bonuses": "Bonus points",
                    "Ingest Logs": "Import logs",
                }
                desc = descriptions.get(table_name, "")
                click.echo(f"{table_name:<20} {count:<10} {desc}")
            except Exception as e:
                click.echo(f"{table_name:<20} {'ERROR':<10} {str(e)[:30]}")

    finally:
        db.close()


@db.command()
@click.argument('table')
@click.option('--limit', type=int, default=10, help='Number of rows to show')
def show(table: str, limit: int):
    """Show data from a specific table."""
    table_map = {
        "users": (User, ["id", "email", "is_admin", "created_at"]),
        "leagues": (League, ["id", "name", "commissioner_id", "max_teams", "is_active"]),
        "teams": (Team, ["id", "name", "owner_id", "league_id"]),
        "players": (Player, ["id", "full_name", "position", "team_abbr"]),
        "statlines": (StatLine, ["id", "player_id", "game_date", "points", "rebounds", "assists"]),
        "ingestion_runs": (IngestionRun, ["id", "target_date", "status", "games_found", "games_processed"]),
        "ingestion_queue": (IngestionQueue, ["id", "game_id", "game_date", "status", "attempts"]),
    }

    if table.lower() not in table_map:
        click.echo(f"❌ Unknown table: {table}")
        click.echo(f"Available tables: {', '.join(table_map.keys())}")
        return

    model_class, columns = table_map[table.lower()]

    init_db()
    db = SessionLocal()

    try:
        total_count = db.query(model_class).count()

        if total_count == 0:
            click.echo("📋 No data found")
            return

        records = db.query(model_class).limit(limit).all()

        click.echo(f"📊 {table.upper()} (showing {len(records)}/{total_count})")
        click.echo("-" * 80)

        # Print header
        header = " | ".join(f"{col:<15}" for col in columns)
        click.echo(header)
        click.echo("-" * len(header))

        # Print data
        for record in records:
            row_data = []
            for col in columns:
                value = getattr(record, col, "N/A")
                if value is None:
                    value = "NULL"
                elif isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M")
                elif isinstance(value, str) and len(value) > 15:
                    value = value[:12] + "..."
                row_data.append(str(value)[:15])

            row = " | ".join(f"{val:<15}" for val in row_data)
            click.echo(row)

    finally:
        db.close()


@db.command()
def stats():
    """Show database statistics and insights."""
    init_db()
    db = SessionLocal()

    try:
        # Basic counts
        stats_data = {
            'users': db.query(User).count(),
            'leagues': db.query(League).count(),
            'teams': db.query(Team).count(),
            'players': db.query(Player).count(),
            'stat_lines': db.query(StatLine).count(),
            'ingestion_runs': db.query(IngestionRun).count(),
            'queue_items': db.query(IngestionQueue).count(),
        }

        click.echo("📊 Database Statistics")
        click.echo("=" * 50)

        for key, value in stats_data.items():
            click.echo(f"{key.replace('_', ' ').title()}: {value}")

        # Recent activity
        recent_stats = db.query(StatLine).filter(
            StatLine.game_date >= datetime.utcnow() - dt.timedelta(days=7)
        ).count()

        click.echo(f"\n🕒 Recent Activity (7 days)")
        click.echo(f"New stat lines: {recent_stats}")

        # Latest data
        latest_stat = db.query(StatLine).order_by(StatLine.game_date.desc()).first()
        if latest_stat:
            click.echo(f"Latest game data: {latest_stat.game_date.strftime('%Y-%m-%d')}")

    finally:
        db.close()


# Add admin commands to the main CLI
cli.add_command(admin)


if __name__ == '__main__':
    cli()