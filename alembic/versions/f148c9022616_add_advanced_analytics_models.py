"""Add advanced analytics models

Revision ID: f148c9022616
Revises: 0a81dd8f0b1e
Create Date: 2024-01-15 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'f148c9022616'
down_revision = '0a81dd8f0b1e'
branch_labels = None
depends_on = None


def upgrade():
    # Create player_season_stats table
    op.create_table(
        'player_season_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('games_started', sa.Integer(), nullable=True),
        # Per game averages
        sa.Column('ppg', sa.Float(), nullable=True),
        sa.Column('rpg', sa.Float(), nullable=True),
        sa.Column('apg', sa.Float(), nullable=True),
        sa.Column('spg', sa.Float(), nullable=True),
        sa.Column('bpg', sa.Float(), nullable=True),
        sa.Column('topg', sa.Float(), nullable=True),
        sa.Column('mpg', sa.Float(), nullable=True),
        # Shooting percentages
        sa.Column('fg_percentage', sa.Float(), nullable=True),
        sa.Column('three_point_percentage', sa.Float(), nullable=True),
        sa.Column('ft_percentage', sa.Float(), nullable=True),
        # Advanced metrics
        sa.Column('per', sa.Float(), nullable=True),
        sa.Column('true_shooting_percentage', sa.Float(), nullable=True),
        sa.Column('usage_rate', sa.Float(), nullable=True),
        # Fantasy specific
        sa.Column('fantasy_ppg', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('ceiling', sa.Float(), nullable=True),
        sa.Column('floor', sa.Float(), nullable=True),
        # Metadata
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'season', name='uq_player_season'),
    )

    # Create player_trends table
    op.create_table(
        'player_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('calculated_date', sa.Date(), nullable=False),
        # Last N games averages
        sa.Column('last_5_games_ppg', sa.Float(), nullable=True),
        sa.Column('last_10_games_ppg', sa.Float(), nullable=True),
        sa.Column('last_5_games_fantasy', sa.Float(), nullable=True),
        sa.Column('last_10_games_fantasy', sa.Float(), nullable=True),
        # Trends
        sa.Column('points_trend', sa.Float(), nullable=True),
        sa.Column('fantasy_trend', sa.Float(), nullable=True),
        sa.Column('minutes_trend', sa.Float(), nullable=True),
        # Hot/cold streaks
        sa.Column('is_hot', sa.Boolean(), nullable=True),
        sa.Column('is_cold', sa.Boolean(), nullable=True),
        sa.Column('streak_games', sa.Integer(), nullable=True),
        # Additional metrics
        sa.Column('last_5_games_rpg', sa.Float(), nullable=True),
        sa.Column('last_5_games_apg', sa.Float(), nullable=True),
        sa.Column('last_10_games_rpg', sa.Float(), nullable=True),
        sa.Column('last_10_games_apg', sa.Float(), nullable=True),
        # Metadata
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'calculated_date', name='uq_player_trends_date'),
    )

    # Create matchup_analysis table
    op.create_table(
        'matchup_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('opponent_team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        # Historical performance
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('avg_fantasy_points', sa.Float(), nullable=True),
        sa.Column('avg_points', sa.Float(), nullable=True),
        sa.Column('avg_rebounds', sa.Float(), nullable=True),
        sa.Column('avg_assists', sa.Float(), nullable=True),
        sa.Column('avg_steals', sa.Float(), nullable=True),
        sa.Column('avg_blocks', sa.Float(), nullable=True),
        sa.Column('avg_minutes', sa.Float(), nullable=True),
        # Performance variance
        sa.Column('fantasy_points_std', sa.Float(), nullable=True),
        sa.Column('best_fantasy_game', sa.Float(), nullable=True),
        sa.Column('worst_fantasy_game', sa.Float(), nullable=True),
        # Team defensive ratings
        sa.Column('opponent_defensive_rating', sa.Float(), nullable=True),
        sa.Column('opponent_pace', sa.Float(), nullable=True),
        sa.Column('opponent_points_allowed_pg', sa.Float(), nullable=True),
        # Position-specific defensive stats
        sa.Column('opponent_position_defense_rating', sa.Float(), nullable=True),
        # Metadata
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.ForeignKeyConstraint(['opponent_team_id'], ['wnba_team.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'opponent_team_id', 'season', name='uq_player_opponent_season'),
    )


def downgrade():
    op.drop_table('matchup_analysis')
    op.drop_table('player_trends')
    op.drop_table('player_season_stats')
