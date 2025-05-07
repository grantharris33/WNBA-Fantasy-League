"""add is_starter to roster_slot and moves_this_week to team

Revision ID: c9a22f877e2b
Revises: b6b22f877e2a
Create Date: 2023-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9a22f877e2b'
down_revision = 'b6b22f877e2a'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_starter column to roster_slot table
    op.add_column('roster_slot', sa.Column('is_starter', sa.Integer(), nullable=False, server_default='0'))

    # Add moves_this_week column to team table
    op.add_column('team', sa.Column('moves_this_week', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # Drop the columns
    op.drop_column('roster_slot', 'is_starter')
    op.drop_column('team', 'moves_this_week')