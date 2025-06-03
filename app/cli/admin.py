"""CLI commands for admin user management."""

import click
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import User
from app.core.security import hash_password


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


if __name__ == '__main__':
    admin()