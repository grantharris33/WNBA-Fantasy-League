"""Add draft models

Revision ID: b6b22f877e2a
Revises:
Create Date: 2023-07-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6b22f877e2a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # DraftState table
    op.create_table('draft_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('current_round', sa.Integer(), nullable=False, default=1),
        sa.Column('current_pick_index', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('seconds_remaining', sa.Integer(), nullable=False, default=60),
        sa.Column('pick_order', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['league.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('league_id')
    )

    # DraftPick table
    op.create_table('draft_pick',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('draft_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('round', sa.Integer(), nullable=False),
        sa.Column('pick_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('is_auto', sa.Integer(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['draft_id'], ['draft_state.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('draft_id', 'player_id', name='uq_draft_player'),
        sa.UniqueConstraint('draft_id', 'round', 'pick_number', name='uq_draft_round_pick')
    )


def downgrade():
    op.drop_table('draft_pick')
    op.drop_table('draft_state')