"""enhance player model with comprehensive data

Revision ID: e2382a95aa0d
Revises: 8a4e342ce09d
Create Date: 2024-12-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2382a95aa0d'
down_revision = '8a4e342ce09d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to player table
    op.add_column('player', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('player', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('player', sa.Column('jersey_number', sa.String(), nullable=True))
    op.add_column('player', sa.Column('height', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('weight', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('birth_date', sa.DateTime(), nullable=True))
    op.add_column('player', sa.Column('birth_place', sa.String(), nullable=True))
    op.add_column('player', sa.Column('college', sa.String(), nullable=True))
    op.add_column('player', sa.Column('draft_year', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('draft_round', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('draft_pick', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('years_pro', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('status', sa.String(), nullable=True, default='active'))
    op.add_column('player', sa.Column('headshot_url', sa.String(), nullable=True))
    op.add_column('player', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('player', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('player', sa.Column('team_id', sa.Integer(), nullable=True))

    # Create foreign key constraint for team_id
    op.create_foreign_key('fk_player_team_id', 'player', 'team', ['team_id'], ['id'])

    # Create indexes for commonly queried fields
    op.create_index('ix_player_status', 'player', ['status'])
    op.create_index('ix_player_team_id', 'player', ['team_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_player_team_id', table_name='player')
    op.drop_index('ix_player_status', table_name='player')

    # Drop foreign key constraint
    op.drop_constraint('fk_player_team_id', 'player', type_='foreignkey')

    # Drop columns
    op.drop_column('player', 'team_id')
    op.drop_column('player', 'updated_at')
    op.drop_column('player', 'created_at')
    op.drop_column('player', 'headshot_url')
    op.drop_column('player', 'status')
    op.drop_column('player', 'years_pro')
    op.drop_column('player', 'draft_pick')
    op.drop_column('player', 'draft_round')
    op.drop_column('player', 'draft_year')
    op.drop_column('player', 'college')
    op.drop_column('player', 'birth_place')
    op.drop_column('player', 'birth_date')
    op.drop_column('player', 'weight')
    op.drop_column('player', 'height')
    op.drop_column('player', 'jersey_number')
    op.drop_column('player', 'last_name')
    op.drop_column('player', 'first_name')