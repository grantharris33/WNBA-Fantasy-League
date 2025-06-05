"""Add WNBATeam and Standings models

Revision ID: 6bb0a33ec1ca
Revises: 9ffa968cd683
Create Date: 2024-12-30 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '6bb0a33ec1ca'
down_revision = '9ffa968cd683'
branch_labels = None
depends_on = None


def upgrade():
    # Create wnba_team table
    op.create_table(
        'wnba_team',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('abbreviation', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('alternate_color', sa.String(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('venue_name', sa.String(), nullable=True),
        sa.Column('venue_city', sa.String(), nullable=True),
        sa.Column('venue_state', sa.String(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True, default=0),
        sa.Column('losses', sa.Integer(), nullable=True, default=0),
        sa.Column('win_percentage', sa.Float(), nullable=True, default=0.0),
        sa.Column('games_behind', sa.Float(), nullable=True),
        sa.Column('streak', sa.String(), nullable=True),
        sa.Column('last_10', sa.String(), nullable=True),
        sa.Column('conference_rank', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('abbreviation'),
    )

    # Create standings table
    op.create_table(
        'standings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=True, default=0),
        sa.Column('losses', sa.Integer(), nullable=True, default=0),
        sa.Column('win_percentage', sa.Float(), nullable=True, default=0.0),
        sa.Column('games_behind', sa.Float(), nullable=True, default=0.0),
        sa.Column('home_wins', sa.Integer(), nullable=True, default=0),
        sa.Column('home_losses', sa.Integer(), nullable=True, default=0),
        sa.Column('away_wins', sa.Integer(), nullable=True, default=0),
        sa.Column('away_losses', sa.Integer(), nullable=True, default=0),
        sa.Column('division_wins', sa.Integer(), nullable=True, default=0),
        sa.Column('division_losses', sa.Integer(), nullable=True, default=0),
        sa.Column('conference_wins', sa.Integer(), nullable=True, default=0),
        sa.Column('conference_losses', sa.Integer(), nullable=True, default=0),
        sa.Column('points_for', sa.Float(), nullable=True, default=0.0),
        sa.Column('points_against', sa.Float(), nullable=True, default=0.0),
        sa.Column('point_differential', sa.Float(), nullable=True, default=0.0),
        sa.ForeignKeyConstraint(['team_id'], ['wnba_team.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'season', 'date', name='uq_standings_team_season_date'),
    )

    # Add wnba_team_id column to player table
    op.add_column('player', sa.Column('wnba_team_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'player', 'wnba_team', ['wnba_team_id'], ['id'])

    # Update game table foreign keys to reference wnba_team instead of team
    # First drop existing foreign keys
    op.drop_constraint(None, 'game', type_='foreignkey')  # home_team_id
    op.drop_constraint(None, 'game', type_='foreignkey')  # away_team_id

    # Create new foreign keys to wnba_team
    op.create_foreign_key(None, 'game', 'wnba_team', ['home_team_id'], ['id'])
    op.create_foreign_key(None, 'game', 'wnba_team', ['away_team_id'], ['id'])

    # Update stat_line foreign keys to reference wnba_team instead of team for team_id and opponent_id
    # Drop existing foreign keys for team_id and opponent_id
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # team_id
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # opponent_id

    # Create new foreign keys to wnba_team
    op.create_foreign_key(None, 'stat_line', 'wnba_team', ['team_id'], ['id'])
    op.create_foreign_key(None, 'stat_line', 'wnba_team', ['opponent_id'], ['id'])


def downgrade():
    # Remove wnba_team references from stat_line
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # team_id
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # opponent_id

    # Recreate foreign keys to team table
    op.create_foreign_key(None, 'stat_line', 'team', ['team_id'], ['id'])
    op.create_foreign_key(None, 'stat_line', 'team', ['opponent_id'], ['id'])

    # Remove wnba_team references from game
    op.drop_constraint(None, 'game', type_='foreignkey')  # home_team_id
    op.drop_constraint(None, 'game', type_='foreignkey')  # away_team_id

    # Recreate foreign keys to team table
    op.create_foreign_key(None, 'game', 'team', ['home_team_id'], ['id'])
    op.create_foreign_key(None, 'game', 'team', ['away_team_id'], ['id'])

    # Remove wnba_team_id column from player
    op.drop_constraint(None, 'player', type_='foreignkey')  # wnba_team_id
    op.drop_column('player', 'wnba_team_id')

    # Drop tables
    op.drop_table('standings')
    op.drop_table('wnba_team')
