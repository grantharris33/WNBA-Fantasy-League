"""Merge notification and analytics heads

Revision ID: 3d3393ec9a95
Revises: add_notification_table, b5df5fc57695
Create Date: 2025-01-06 14:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '3d3393ec9a95'
down_revision = ('add_notification_table', 'b5df5fc57695')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
