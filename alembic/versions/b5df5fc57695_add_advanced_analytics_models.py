"""Add advanced analytics models

Revision ID: b5df5fc57695
Revises: feda888bea0d
Create Date: 2025-01-06 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b5df5fc57695'
down_revision = 'feda888bea0d'
branch_labels = None
depends_on = None


def upgrade():
    # Create player_season_stats table
    op.create_table(
        'player_season_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('games_played', sa.Integer(), nullable=True, default=0),
        sa.Column('games_started', sa.Integer(), nullable=True, default=0),
        # Per game averages
        sa.Column('ppg', sa.Float(), nullable=True, default=0.0),
        sa.Column('rpg', sa.Float(), nullable=True, default=0.0),
        sa.Column('apg', sa.Float(), nullable=True, default=0.0),
        sa.Column('spg', sa.Float(), nullable=True, default=0.0),
        sa.Column('bpg', sa.Float(), nullable=True, default=0.0),
        sa.Column('topg', sa.Float(), nullable=True, default=0.0),
        sa.Column('mpg', sa.Float(), nullable=True, default=0.0),
        # Shooting percentages
        sa.Column('fg_percentage', sa.Float(), nullable=True, default=0.0),
        sa.Column('three_point_percentage', sa.Float(), nullable=True, default=0.0),
        sa.Column('ft_percentage', sa.Float(), nullable=True, default=0.0),
        # Advanced metrics
        sa.Column('per', sa.Float(), nullable=True, default=0.0),
        sa.Column('true_shooting_percentage', sa.Float(), nullable=True, default=0.0),
        sa.Column('usage_rate', sa.Float(), nullable=True, default=0.0),
        # Fantasy specific
        sa.Column('fantasy_ppg', sa.Float(), nullable=True, default=0.0),
        sa.Column('consistency_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('ceiling', sa.Float(), nullable=True, default=0.0),
        sa.Column('floor', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'season', name='uq_player_season'),
    )
    op.create_index(op.f('ix_player_season_stats_player_id'), 'player_season_stats', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_season_stats_season'), 'player_season_stats', ['season'], unique=False)

    # Create player_trends table
    op.create_table(
        'player_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('calculated_date', sa.Date(), nullable=False),
        # Last N games averages
        sa.Column('last_5_games_ppg', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_10_games_ppg', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_5_games_fantasy', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_10_games_fantasy', sa.Float(), nullable=True, default=0.0),
        # Trends (positive = improving)
        sa.Column('points_trend', sa.Float(), nullable=True, default=0.0),
        sa.Column('fantasy_trend', sa.Float(), nullable=True, default=0.0),
        sa.Column('minutes_trend', sa.Float(), nullable=True, default=0.0),
        # Hot/cold streaks
        sa.Column('is_hot', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_cold', sa.Boolean(), nullable=True, default=False),
        sa.Column('streak_games', sa.Integer(), nullable=True, default=0),
        # Additional metrics
        sa.Column('last_5_games_rpg', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_5_games_apg', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_10_games_rpg', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_10_games_apg', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'calculated_date', name='uq_player_trend_date'),
    )
    op.create_index(op.f('ix_player_trends_player_id'), 'player_trends', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_trends_calculated_date'), 'player_trends', ['calculated_date'], unique=False)

    # Create matchup_analysis table
    op.create_table(
        'matchup_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('opponent_team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        # Historical performance vs team
        sa.Column('games_played', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_fantasy_points', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_points', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_rebounds', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_assists', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_steals', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_blocks', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_minutes', sa.Float(), nullable=True, default=0.0),
        # Performance variance
        sa.Column('fantasy_points_std', sa.Float(), nullable=True, default=0.0),
        sa.Column('best_fantasy_game', sa.Float(), nullable=True, default=0.0),
        sa.Column('worst_fantasy_game', sa.Float(), nullable=True, default=0.0),
        # Team defensive ratings
        sa.Column('opponent_defensive_rating', sa.Float(), nullable=True, default=0.0),
        sa.Column('opponent_pace', sa.Float(), nullable=True, default=0.0),
        sa.Column('opponent_points_allowed_pg', sa.Float(), nullable=True, default=0.0),
        # Position-specific defensive stats
        sa.Column('opponent_position_defense_rating', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player.id']),
        sa.ForeignKeyConstraint(['opponent_team_id'], ['wnba_team.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'opponent_team_id', 'season', name='uq_player_opponent_season'),
    )
    op.create_index(op.f('ix_matchup_analysis_player_id'), 'matchup_analysis', ['player_id'], unique=False)
    op.create_index(
        op.f('ix_matchup_analysis_opponent_team_id'), 'matchup_analysis', ['opponent_team_id'], unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_matchup_analysis_opponent_team_id'), table_name='matchup_analysis')
    op.drop_index(op.f('ix_matchup_analysis_player_id'), table_name='matchup_analysis')
    op.drop_table('matchup_analysis')

    op.drop_index(op.f('ix_player_trends_calculated_date'), table_name='player_trends')
    op.drop_index(op.f('ix_player_trends_player_id'), table_name='player_trends')
    op.drop_table('player_trends')

    op.drop_index(op.f('ix_player_season_stats_season'), table_name='player_season_stats')
    op.drop_index(op.f('ix_player_season_stats_player_id'), table_name='player_season_stats')
    op.drop_table('player_season_stats')
