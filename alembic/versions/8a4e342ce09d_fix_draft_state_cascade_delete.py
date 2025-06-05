"""Fix draft_state cascade delete

Revision ID: 8a4e342ce09d
Revises: 66156fba2281
Create Date: 2025-06-02 21:45:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '8a4e342ce09d'
down_revision = '66156fba2281'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support modifying foreign key constraints directly
    # However, the cascade behavior is handled by SQLAlchemy ORM, not the database
    # So we don't need to modify the actual foreign key constraint in SQLite
    # The fix is purely in the model relationship configuration
    pass


def downgrade():
    # No database changes needed
    pass
