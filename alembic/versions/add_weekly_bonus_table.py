"""add weekly bonus table

Revision ID: af9b22f877e3a
Revises: b6b22f877e2a
Create Date: 2024-06-07 00:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'af9b22f877e3a'
down_revision = 'b6b22f877e2a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'weekly_bonus',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('points', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', 'player_id', 'category', name='uq_bonus_week_player_category'),
    )
    op.create_index(op.f('ix_weekly_bonus_id'), 'weekly_bonus', ['id'], unique=False)
    op.create_index(op.f('ix_weekly_bonus_week_id'), 'weekly_bonus', ['week_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_weekly_bonus_week_id'), table_name='weekly_bonus')
    op.drop_index(op.f('ix_weekly_bonus_id'), table_name='weekly_bonus')
    op.drop_table('weekly_bonus')
