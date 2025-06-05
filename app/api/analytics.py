"""API endpoints for player analytics and advanced statistics."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import MatchupAnalysis, Player, PlayerSeasonStats, PlayerTrends, RosterSlot, WNBATeam
from app.services.analytics import AnalyticsService

router = APIRouter()


class PlayerAnalyticsResponse(BaseModel):
    """Response model for player analytics."""

    player_id: int
    player_name: str
    season: int
    games_played: int
    games_started: int

    # Per game averages
    ppg: float
    rpg: float
    apg: float
    spg: float
    bpg: float
    topg: float
    mpg: float

    # Shooting percentages
    fg_percentage: float
    three_point_percentage: float
    ft_percentage: float

    # Advanced metrics
    per: float
    true_shooting_percentage: float
    usage_rate: float

    # Fantasy specific
    fantasy_ppg: float
    consistency_score: float
    ceiling: float
    floor: float

    class Config:
        from_attributes = True


class PlayerTrendsResponse(BaseModel):
    """Response model for player trends."""

    player_id: int
    player_name: str
    calculated_date: str

    # Last N games averages
    last_5_games_ppg: float
    last_10_games_ppg: float
    last_5_games_fantasy: float
    last_10_games_fantasy: float
    last_5_games_rpg: float
    last_5_games_apg: float

    # Trends
    points_trend: float
    fantasy_trend: float
    minutes_trend: float

    # Hot/cold streaks
    is_hot: bool
    is_cold: bool
    streak_games: int

    class Config:
        from_attributes = True


class ProjectionResponse(BaseModel):
    """Response model for fantasy projections."""

    player_id: int
    player_name: str
    opponent_team: str
    projected_fantasy_points: float
    season_average: float
    last_5_games_average: float
    matchup_history_average: Optional[float]

    class Config:
        from_attributes = True


class MatchupHistoryResponse(BaseModel):
    """Response model for matchup history."""

    player_id: int
    opponent_team: str
    games_played: int
    avg_fantasy_points: float
    avg_points: float
    avg_rebounds: float
    avg_assists: float
    best_fantasy_game: float
    worst_fantasy_game: float

    class Config:
        from_attributes = True


@router.get("/api/v1/players/{player_id}/analytics", response_model=PlayerAnalyticsResponse)
async def get_player_analytics(
    player_id: int,
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    db: Session = Depends(get_db),
):
    """Get comprehensive analytics for a player."""
    if season is None:
        season = datetime.now().year

    # Get player
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get season stats
    season_stats = (
        db.query(PlayerSeasonStats)
        .filter(PlayerSeasonStats.player_id == player_id, PlayerSeasonStats.season == season)
        .first()
    )

    if not season_stats:
        # Calculate on demand if not available
        analytics_service = AnalyticsService(db)
        season_stats = analytics_service.update_player_season_stats(player_id, season)

        if not season_stats:
            raise HTTPException(status_code=404, detail=f"No statistics found for player in {season} season")

    return PlayerAnalyticsResponse(
        player_id=player.id,
        player_name=player.full_name,
        season=season_stats.season,
        games_played=season_stats.games_played,
        games_started=season_stats.games_started,
        ppg=season_stats.ppg,
        rpg=season_stats.rpg,
        apg=season_stats.apg,
        spg=season_stats.spg,
        bpg=season_stats.bpg,
        topg=season_stats.topg,
        mpg=season_stats.mpg,
        fg_percentage=season_stats.fg_percentage,
        three_point_percentage=season_stats.three_point_percentage,
        ft_percentage=season_stats.ft_percentage,
        per=season_stats.per,
        true_shooting_percentage=season_stats.true_shooting_percentage,
        usage_rate=season_stats.usage_rate,
        fantasy_ppg=season_stats.fantasy_ppg,
        consistency_score=season_stats.consistency_score,
        ceiling=season_stats.ceiling,
        floor=season_stats.floor,
    )


@router.get("/api/v1/players/{player_id}/trends", response_model=PlayerTrendsResponse)
async def get_player_trends(player_id: int, db: Session = Depends(get_db)):
    """Get recent performance trends for a player."""
    # Get player
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get latest trends
    trends = (
        db.query(PlayerTrends)
        .filter(PlayerTrends.player_id == player_id)
        .order_by(PlayerTrends.calculated_date.desc())
        .first()
    )

    if not trends:
        # Calculate on demand
        analytics_service = AnalyticsService(db)
        trends = analytics_service.update_player_trends(player_id)

    return PlayerTrendsResponse(
        player_id=player.id,
        player_name=player.full_name,
        calculated_date=trends.calculated_date.isoformat(),
        last_5_games_ppg=trends.last_5_games_ppg,
        last_10_games_ppg=trends.last_10_games_ppg,
        last_5_games_fantasy=trends.last_5_games_fantasy,
        last_10_games_fantasy=trends.last_10_games_fantasy,
        last_5_games_rpg=trends.last_5_games_rpg,
        last_5_games_apg=trends.last_5_games_apg,
        points_trend=trends.points_trend,
        fantasy_trend=trends.fantasy_trend,
        minutes_trend=trends.minutes_trend,
        is_hot=trends.is_hot,
        is_cold=trends.is_cold,
        streak_games=trends.streak_games,
    )


@router.get("/api/v1/analytics/projections", response_model=List[ProjectionResponse])
async def get_weekly_projections(
    week: Optional[int] = Query(None, description="Week number (defaults to current)"),
    team_id: Optional[int] = Query(None, description="Filter by fantasy team"),
    db: Session = Depends(get_db),
):
    """Get fantasy projections for players."""
    analytics_service = AnalyticsService(db)

    # Get players to project (either from a specific team or top players)
    if team_id:
        players = db.query(Player).join(RosterSlot).filter(RosterSlot.team_id == team_id).all()
    else:
        # Get top 50 players by fantasy average
        season = datetime.now().year
        players = (
            db.query(Player)
            .join(PlayerSeasonStats)
            .filter(PlayerSeasonStats.season == season)
            .order_by(PlayerSeasonStats.fantasy_ppg.desc())
            .limit(50)
            .all()
        )

    projections = []

    for player in players:
        # Get next opponent (simplified - would need schedule integration)
        # For now, project against league average
        opponent_id = 1  # Placeholder

        projection = analytics_service.project_fantasy_points(player.id, opponent_id)

        # Get additional context
        season_stats = (
            db.query(PlayerSeasonStats)
            .filter(PlayerSeasonStats.player_id == player.id, PlayerSeasonStats.season == datetime.now().year)
            .first()
        )

        trends = (
            db.query(PlayerTrends)
            .filter(PlayerTrends.player_id == player.id)
            .order_by(PlayerTrends.calculated_date.desc())
            .first()
        )

        projections.append(
            ProjectionResponse(
                player_id=player.id,
                player_name=player.full_name,
                opponent_team="TBD",  # Would come from schedule
                projected_fantasy_points=projection,
                season_average=season_stats.fantasy_ppg if season_stats else 0,
                last_5_games_average=trends.last_5_games_fantasy if trends else 0,
                matchup_history_average=None,  # Would come from matchup analysis
            )
        )

    return projections


@router.get("/api/v1/players/{player_id}/matchup-history", response_model=List[MatchupHistoryResponse])
async def get_matchup_history(
    player_id: int,
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    db: Session = Depends(get_db),
):
    """Get historical performance against all teams."""
    if season is None:
        season = datetime.now().year

    # Get player
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get all matchup analyses
    matchups = (
        db.query(MatchupAnalysis)
        .join(WNBATeam)
        .filter(
            MatchupAnalysis.player_id == player_id, MatchupAnalysis.season == season, MatchupAnalysis.games_played > 0
        )
        .all()
    )

    results = []
    for matchup in matchups:
        team = db.query(WNBATeam).filter(WNBATeam.id == matchup.opponent_team_id).first()

        results.append(
            MatchupHistoryResponse(
                player_id=player.id,
                opponent_team=team.display_name if team else "Unknown",
                games_played=matchup.games_played,
                avg_fantasy_points=matchup.avg_fantasy_points,
                avg_points=matchup.avg_points,
                avg_rebounds=matchup.avg_rebounds,
                avg_assists=matchup.avg_assists,
                best_fantasy_game=matchup.best_fantasy_game,
                worst_fantasy_game=matchup.worst_fantasy_game,
            )
        )

    return results


@router.post("/api/v1/analytics/calculate")
async def trigger_analytics_calculation(
    player_id: Optional[int] = Query(None, description="Calculate for specific player only"),
    db: Session = Depends(get_db),
):
    """Manually trigger analytics calculation."""
    analytics_service = AnalyticsService(db)
    season = datetime.now().year

    try:
        if player_id:
            # Calculate for specific player
            analytics_service.update_player_season_stats(player_id, season)
            analytics_service.update_player_trends(player_id)

            # Update matchup analyses
            teams = db.query(WNBATeam).all()
            for team in teams:
                analytics_service.update_matchup_analysis(player_id, team.id, season)

            return {"message": f"Analytics calculated for player {player_id}"}
        else:
            # Calculate for all players
            analytics_service.calculate_all_analytics(season)
            return {"message": "Analytics calculated for all players"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
