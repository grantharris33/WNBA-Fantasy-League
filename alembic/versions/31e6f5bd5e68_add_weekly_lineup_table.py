"""add weekly lineup table

Revision ID: 31e6f5bd5e68
Revises: c9a22f877e2b
Create Date: 2025-01-11 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '31e6f5bd5e68'
down_revision = 'f148c9022616'
branch_labels = None
depends_on = None


def upgrade():
    # Create weekly_lineup table
    op.create_table(
        'weekly_lineup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('is_starter', sa.Boolean(), nullable=False),
        sa.Column('locked_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'week_id', 'player_id', name='uq_weekly_lineup_team_week_player'),
    )
    op.create_index(op.f('ix_weekly_lineup_id'), 'weekly_lineup', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_weekly_lineup_id'), table_name='weekly_lineup')
    op.drop_table('weekly_lineup')
