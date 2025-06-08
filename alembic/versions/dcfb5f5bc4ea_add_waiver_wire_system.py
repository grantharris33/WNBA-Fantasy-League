"""add waiver wire system

Revision ID: dcfb5f5bc4ea
Revises: 08407d878e2c
Create Date: 2025-01-11 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'dcfb5f5bc4ea'
down_revision = '08407d878e2c'
branch_labels = None
depends_on = None


def upgrade():
    # Add waiver fields to league table
    op.add_column('league', sa.Column('waiver_period_days', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('league', sa.Column('waiver_type', sa.String(), nullable=False, server_default='reverse_standings'))

    # Add waiver field to player table
    op.add_column('player', sa.Column('waiver_expires_at', sa.DateTime(), nullable=True))
    op.create_index('ix_player_waiver_expires_at', 'player', ['waiver_expires_at'], unique=False)

    # Create waiver_claim table
    op.create_table(
        'waiver_claim',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('drop_player_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['drop_player_id'], ['player.id']),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'player_id', 'status', name='uq_team_player_pending_claim'),
    )
    op.create_index(op.f('ix_waiver_claim_id'), 'waiver_claim', ['id'], unique=False)


def downgrade():
    # Drop waiver_claim table
    op.drop_index(op.f('ix_waiver_claim_id'), table_name='waiver_claim')
    op.drop_table('waiver_claim')

    # Remove waiver field from player table
    op.drop_index('ix_player_waiver_expires_at', table_name='player')
    op.drop_column('player', 'waiver_expires_at')

    # Remove waiver fields from league table
    op.drop_column('league', 'waiver_type')
    op.drop_column('league', 'waiver_period_days')
