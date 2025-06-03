from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlayerSeasonStats(Base):
    """Aggregated season statistics for a player."""
    __tablename__ = "player_season_stats"

    id: int = Column(Integer, primary_key=True)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    season: int = Column(Integer, nullable=False)
    games_played: int = Column(Integer, default=0)
    games_started: int = Column(Integer, default=0)

    # Per game averages
    ppg: float = Column(Float, default=0.0)  # Points per game
    rpg: float = Column(Float, default=0.0)  # Rebounds per game
    apg: float = Column(Float, default=0.0)  # Assists per game
    spg: float = Column(Float, default=0.0)  # Steals per game
    bpg: float = Column(Float, default=0.0)  # Blocks per game
    topg: float = Column(Float, default=0.0)  # Turnovers per game
    mpg: float = Column(Float, default=0.0)  # Minutes per game

    # Shooting percentages
    fg_percentage: float = Column(Float, default=0.0)
    three_point_percentage: float = Column(Float, default=0.0)
    ft_percentage: float = Column(Float, default=0.0)

    # Advanced metrics
    per: float = Column(Float, default=0.0)  # Player Efficiency Rating
    true_shooting_percentage: float = Column(Float, default=0.0)
    usage_rate: float = Column(Float, default=0.0)

    # Fantasy specific
    fantasy_ppg: float = Column(Float, default=0.0)
    consistency_score: float = Column(Float, default=0.0)  # Std dev of fantasy points
    ceiling: float = Column(Float, default=0.0)  # Best game
    floor: float = Column(Float, default=0.0)  # Worst game

    # Metadata
    last_updated: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = relationship("Player", backref="season_stats")

    __table_args__ = (
        UniqueConstraint("player_id", "season", name="uq_player_season"),
    )


class PlayerTrends(Base):
    """Recent performance trends for a player."""
    __tablename__ = "player_trends"

    id: int = Column(Integer, primary_key=True)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    calculated_date: date = Column(Date, nullable=False)

    # Last N games averages
    last_5_games_ppg: float = Column(Float, default=0.0)
    last_10_games_ppg: float = Column(Float, default=0.0)
    last_5_games_fantasy: float = Column(Float, default=0.0)
    last_10_games_fantasy: float = Column(Float, default=0.0)

    # Trends (positive = improving)
    points_trend: float = Column(Float, default=0.0)
    fantasy_trend: float = Column(Float, default=0.0)
    minutes_trend: float = Column(Float, default=0.0)

    # Hot/cold streaks
    is_hot: bool = Column(Boolean, default=False)  # 3+ games above average
    is_cold: bool = Column(Boolean, default=False)  # 3+ games below average
    streak_games: int = Column(Integer, default=0)  # Number of games in current streak

    # Additional metrics
    last_5_games_rpg: float = Column(Float, default=0.0)
    last_5_games_apg: float = Column(Float, default=0.0)
    last_10_games_rpg: float = Column(Float, default=0.0)
    last_10_games_apg: float = Column(Float, default=0.0)

    # Metadata
    last_updated: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = relationship("Player", backref="trends")

    __table_args__ = (
        UniqueConstraint("player_id", "calculated_date", name="uq_player_trends_date"),
    )


class MatchupAnalysis(Base):
    """Historical performance analysis against specific teams."""
    __tablename__ = "matchup_analysis"

    id: int = Column(Integer, primary_key=True)
    player_id: int = Column(Integer, ForeignKey("player.id"), nullable=False)
    opponent_team_id: int = Column(Integer, ForeignKey("wnba_team.id"), nullable=False)
    season: int = Column(Integer, nullable=False)

    # Historical performance vs team
    games_played: int = Column(Integer, default=0)
    avg_fantasy_points: float = Column(Float, default=0.0)
    avg_points: float = Column(Float, default=0.0)
    avg_rebounds: float = Column(Float, default=0.0)
    avg_assists: float = Column(Float, default=0.0)
    avg_steals: float = Column(Float, default=0.0)
    avg_blocks: float = Column(Float, default=0.0)
    avg_minutes: float = Column(Float, default=0.0)

    # Performance variance
    fantasy_points_std: float = Column(Float, default=0.0)  # Standard deviation
    best_fantasy_game: float = Column(Float, default=0.0)
    worst_fantasy_game: float = Column(Float, default=0.0)

    # Team defensive ratings
    opponent_defensive_rating: float = Column(Float, default=0.0)
    opponent_pace: float = Column(Float, default=0.0)
    opponent_points_allowed_pg: float = Column(Float, default=0.0)  # Points allowed per game

    # Position-specific defensive stats
    opponent_position_defense_rating: float = Column(Float, default=0.0)  # How well they defend player's position

    # Metadata
    last_updated: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = relationship("Player", backref="matchup_analyses")
    opponent_team = relationship("WNBATeam", backref="matchup_analyses_against")

    __table_args__ = (
        UniqueConstraint("player_id", "opponent_team_id", "season", name="uq_player_opponent_season"),
    )