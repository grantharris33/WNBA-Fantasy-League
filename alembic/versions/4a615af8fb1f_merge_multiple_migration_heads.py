"""Merge multiple migration heads

Revision ID: 4a615af8fb1f
Revises: c9a22f877e2b, af9b22f877e3a, d2e8f7a92b1e
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4a615af8fb1f'
down_revision = ('c9a22f877e2b', 'af9b22f877e3a', 'd2e8f7a92b1e')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no changes needed
    pass


def downgrade():
    # This is a merge migration - no changes needed
    pass