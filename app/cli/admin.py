"""CLI commands for admin user management."""

import click
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import User, Team
from app.core.security import hash_password
from app.services.roster import RosterService


@click.group()
def admin():
    """Admin management commands."""
    pass


@admin.command()
@click.argument('email')
@click.option('--password', default='admin123', help='Password for the admin user')
def create_admin(email: str, password: str):
    """Create a new admin user."""
    db: Session = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            if existing_user.is_admin:
                click.echo(f"User {email} is already an admin")
                return
            else:
                # Promote existing user to admin
                existing_user.is_admin = True
                db.commit()
                click.echo(f"Promoted user {email} to admin")
                return

        # Create new admin user
        hashed_password = hash_password(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            is_admin=True
        )

        db.add(admin_user)
        db.commit()

        click.echo(f"Created admin user: {email}")

    except Exception as e:
        db.rollback()
        click.echo(f"Error creating admin user: {str(e)}")
    finally:
        db.close()


@admin.command()
def list_admins():
    """List all admin users."""
    db: Session = SessionLocal()

    try:
        admins = db.query(User).filter(User.is_admin == True).all()

        if not admins:
            click.echo("No admin users found")
            return

        click.echo("Admin users:")
        for admin in admins:
            click.echo(f"  - {admin.email} (ID: {admin.id})")

    except Exception as e:
        click.echo(f"Error listing admin users: {str(e)}")
    finally:
        db.close()


@admin.command()
@click.argument('email')
def revoke_admin(email: str):
    """Revoke admin privileges from a user."""
    db: Session = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            click.echo(f"User {email} not found")
            return

        if not user.is_admin:
            click.echo(f"User {email} is not an admin")
            return

        user.is_admin = False
        db.commit()

        click.echo(f"Revoked admin privileges from {email}")

    except Exception as e:
        db.rollback()
        click.echo(f"Error revoking admin privileges: {str(e)}")
    finally:
        db.close()


@admin.command()
@click.argument('team_id', type=int)
@click.argument('week_id', type=int)
@click.argument('moves_to_grant', type=int)
@click.argument('reason')
@click.option('--admin-email', required=True, help='Email of admin user granting the moves')
def grant_moves(team_id: int, week_id: int, moves_to_grant: int, reason: str, admin_email: str):
    """Grant additional moves to a team for a specific week."""
    db: Session = SessionLocal()

    try:
        # Get admin user
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            click.echo(f"Admin user {admin_email} not found")
            return
        if not admin_user.is_admin:
            click.echo(f"User {admin_email} is not an admin")
            return

        # Get team
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            click.echo(f"Team with ID {team_id} not found")
            return

        roster_service = RosterService(db)
        grant = roster_service.grant_admin_moves(
            team_id=team_id,
            week_id=week_id,
            moves_to_grant=moves_to_grant,
            reason=reason,
            admin_user_id=admin_user.id
        )

        click.echo(f"Successfully granted {moves_to_grant} moves to team '{team.name}' for week {week_id}")
        click.echo(f"Reason: {reason}")
        click.echo(f"Grant ID: {grant.id}")

    except Exception as e:
        db.rollback()
        click.echo(f"Error granting moves: {str(e)}")
    finally:
        db.close()


@admin.command()
@click.argument('team_id', type=int)
@click.argument('week_id', type=int)
def move_summary(team_id: int, week_id: int):
    """Get move summary for a team and week."""
    db: Session = SessionLocal()

    try:
        # Get team
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            click.echo(f"Team with ID {team_id} not found")
            return

        roster_service = RosterService(db)
        summary = roster_service.get_team_move_summary(team_id, week_id)

        click.echo(f"\nMove Summary for Team '{team.name}' - Week {week_id}")
        click.echo("=" * 50)
        click.echo(f"Base moves allowed: {summary['base_moves']}")
        click.echo(f"Admin granted moves: {summary['admin_granted_moves']}")
        click.echo(f"Total available moves: {summary['total_available_moves']}")
        click.echo(f"Moves used: {summary['moves_used']}")
        click.echo(f"Moves remaining: {summary['moves_remaining']}")

        if summary['admin_grants']:
            click.echo("\nAdmin Grants:")
            for grant in summary['admin_grants']:
                click.echo(f"  - {grant['moves_granted']} moves: {grant['reason']} (ID: {grant['id']})")

    except Exception as e:
        click.echo(f"Error getting move summary: {str(e)}")
    finally:
        db.close()


@admin.command()
@click.argument('team_id', type=int)
@click.argument('week_id', type=int)
@click.argument('starter_ids')
@click.option('--admin-email', required=True, help='Email of admin user making the change')
@click.option('--bypass-moves/--no-bypass-moves', default=True, help='Bypass move limit checks')
def force_roster(team_id: int, week_id: int, starter_ids: str, admin_email: str, bypass_moves: bool):
    """Force set team roster with admin override."""
    db: Session = SessionLocal()

    try:
        # Get admin user
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            click.echo(f"Admin user {admin_email} not found")
            return
        if not admin_user.is_admin:
            click.echo(f"User {admin_email} is not an admin")
            return

        # Get team
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            click.echo(f"Team with ID {team_id} not found")
            return

        # Parse starter IDs
        try:
            starter_player_ids = [int(x.strip()) for x in starter_ids.split(',')]
        except ValueError:
            click.echo("Invalid starter IDs format. Use comma-separated integers (e.g., '1,2,3,4,5')")
            return

        if len(starter_player_ids) != 5:
            click.echo("Must specify exactly 5 starter player IDs")
            return

        roster_service = RosterService(db)
        starters = roster_service.set_starters_admin_override(
            team_id=team_id,
            starter_player_ids=starter_player_ids,
            admin_user_id=admin_user.id,
            week_id=week_id,
            bypass_move_limit=bypass_moves
        )

        click.echo(f"Successfully set roster for team '{team.name}' - Week {week_id}")
        click.echo(f"Starter player IDs: {starter_player_ids}")
        click.echo(f"Bypass move limits: {bypass_moves}")
        click.echo(f"Starters set: {len(starters)}")

    except Exception as e:
        db.rollback()
        click.echo(f"Error setting roster: {str(e)}")
    finally:
        db.close()


if __name__ == '__main__':
    admin()