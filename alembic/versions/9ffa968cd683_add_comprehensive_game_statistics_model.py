"""Add comprehensive game statistics model

Revision ID: 9ffa968cd683
Revises: cf62ffc445e5
Create Date: 2024-12-30 00:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '9ffa968cd683'
down_revision = 'cf62ffc445e5'
branch_labels = None
depends_on = None


def upgrade():
    # Create game table
    op.create_table(
        'game',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=True),
        sa.Column('away_team_id', sa.Integer(), nullable=True),
        sa.Column('home_score', sa.Integer(), nullable=True, default=0),
        sa.Column('away_score', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(), nullable=True, default='scheduled'),
        sa.Column('venue', sa.String(), nullable=True),
        sa.Column('attendance', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['away_team_id'], ['wnba_team.id']),
        sa.ForeignKeyConstraint(['home_team_id'], ['wnba_team.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_game_date'), 'game', ['date'], unique=False)

    # Drop old unique constraint on stat_line
    op.drop_constraint('uq_stat_line_player_date', 'stat_line', type_='unique')

    # Add new columns to stat_line
    op.add_column('stat_line', sa.Column('game_id', sa.String(), nullable=True))
    op.add_column('stat_line', sa.Column('minutes_played', sa.Float(), nullable=True, default=0.0))
    op.add_column('stat_line', sa.Column('field_goals_made', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('field_goals_attempted', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('field_goal_percentage', sa.Float(), nullable=True, default=0.0))
    op.add_column('stat_line', sa.Column('three_pointers_made', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('three_pointers_attempted', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('three_point_percentage', sa.Float(), nullable=True, default=0.0))
    op.add_column('stat_line', sa.Column('free_throws_made', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('free_throws_attempted', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('free_throw_percentage', sa.Float(), nullable=True, default=0.0))
    op.add_column('stat_line', sa.Column('offensive_rebounds', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('defensive_rebounds', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('turnovers', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('personal_fouls', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('plus_minus', sa.Integer(), nullable=True, default=0))
    op.add_column('stat_line', sa.Column('is_starter', sa.Boolean(), nullable=True, default=False))
    op.add_column('stat_line', sa.Column('did_not_play', sa.Boolean(), nullable=True, default=False))
    op.add_column('stat_line', sa.Column('team_id', sa.Integer(), nullable=True))
    op.add_column('stat_line', sa.Column('opponent_id', sa.Integer(), nullable=True))
    op.add_column('stat_line', sa.Column('is_home_game', sa.Boolean(), nullable=True, default=True))

    # Create new indexes and constraints
    op.create_index(op.f('ix_stat_line_game_id'), 'stat_line', ['game_id'], unique=False)
    op.create_unique_constraint('uq_stat_line_player_game', 'stat_line', ['player_id', 'game_id'])

    # Create foreign key constraints
    op.create_foreign_key(None, 'stat_line', 'game', ['game_id'], ['id'])
    op.create_foreign_key(None, 'stat_line', 'wnba_team', ['team_id'], ['id'])
    op.create_foreign_key(None, 'stat_line', 'wnba_team', ['opponent_id'], ['id'])


def downgrade():
    # Remove foreign keys and indexes
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # game_id
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # team_id
    op.drop_constraint(None, 'stat_line', type_='foreignkey')  # opponent_id
    op.drop_constraint('uq_stat_line_player_game', 'stat_line', type_='unique')
    op.drop_index(op.f('ix_stat_line_game_id'), table_name='stat_line')

    # Remove new columns from stat_line
    op.drop_column('stat_line', 'is_home_game')
    op.drop_column('stat_line', 'opponent_id')
    op.drop_column('stat_line', 'team_id')
    op.drop_column('stat_line', 'did_not_play')
    op.drop_column('stat_line', 'is_starter')
    op.drop_column('stat_line', 'plus_minus')
    op.drop_column('stat_line', 'personal_fouls')
    op.drop_column('stat_line', 'turnovers')
    op.drop_column('stat_line', 'defensive_rebounds')
    op.drop_column('stat_line', 'offensive_rebounds')
    op.drop_column('stat_line', 'free_throw_percentage')
    op.drop_column('stat_line', 'free_throws_attempted')
    op.drop_column('stat_line', 'free_throws_made')
    op.drop_column('stat_line', 'three_point_percentage')
    op.drop_column('stat_line', 'three_pointers_attempted')
    op.drop_column('stat_line', 'three_pointers_made')
    op.drop_column('stat_line', 'field_goal_percentage')
    op.drop_column('stat_line', 'field_goals_attempted')
    op.drop_column('stat_line', 'field_goals_made')
    op.drop_column('stat_line', 'minutes_played')
    op.drop_column('stat_line', 'game_id')

    # Restore old unique constraint
    op.create_unique_constraint('uq_stat_line_player_date', 'stat_line', ['player_id', 'game_date'])

    # Drop game table
    op.drop_index(op.f('ix_game_date'), table_name='game')
    op.drop_table('game')
