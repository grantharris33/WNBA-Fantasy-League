"""API endpoints for WNBA teams, standings, and player data."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    DetailedPlayerStatsOut,
    LeagueLeaderOut,
    Pagination,
    PlayerGameLogOut,
    PlayerSearchResultOut,
    StandingsOut,
    TeamRosterPlayerOut,
    TeamScheduleGameOut,
    TeamStatsOut,
    WNBATeamOut,
)
from app.core.database import get_db
from app.models import Player, PlayerSeasonStats, WNBATeam
from app.services.analytics import AnalyticsService
from app.services.wnba import WNBAService

router = APIRouter(prefix="/api/v1/wnba", tags=["wnba"])


@router.get("/teams", response_model=List[WNBATeamOut])
async def get_all_teams(db: Session = Depends(get_db)) -> List[WNBATeamOut]:
    """Get all WNBA teams."""
    wnba_service = WNBAService(db)
    teams = wnba_service.get_all_teams()
    return [WNBATeamOut.from_orm(team) for team in teams]


@router.get("/teams/{team_id}", response_model=WNBATeamOut)
async def get_team(team_id: int = Path(..., description="Team ID"), db: Session = Depends(get_db)) -> WNBATeamOut:
    """Get a specific WNBA team by ID."""
    wnba_service = WNBAService(db)
    team = wnba_service.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return WNBATeamOut.from_orm(team)


@router.get("/teams/by-abbreviation/{abbreviation}", response_model=WNBATeamOut)
async def get_team_by_abbreviation(
    abbreviation: str = Path(..., description="Team abbreviation"), db: Session = Depends(get_db)
) -> WNBATeamOut:
    """Get a WNBA team by abbreviation."""
    wnba_service = WNBAService(db)
    team = wnba_service.get_team_by_abbreviation(abbreviation.upper())
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return WNBATeamOut.from_orm(team)


@router.get("/standings", response_model=List[StandingsOut])
async def get_standings(
    season: Optional[int] = Query(None, description="Season year (defaults to current)"), db: Session = Depends(get_db)
) -> List[StandingsOut]:
    """Get current standings for the season."""
    wnba_service = WNBAService(db)
    standings = wnba_service.get_current_standings(season)
    return [StandingsOut(**standing) for standing in standings]


@router.get("/teams/{team_id}/roster", response_model=List[TeamRosterPlayerOut])
async def get_team_roster(
    team_id: int = Path(..., description="Team ID"),
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    db: Session = Depends(get_db),
) -> List[TeamRosterPlayerOut]:
    """Get roster for a specific WNBA team."""
    wnba_service = WNBAService(db)
    roster = wnba_service.get_team_roster(team_id, season)
    return [TeamRosterPlayerOut(**player) for player in roster]


@router.get("/teams/{team_id}/schedule", response_model=List[TeamScheduleGameOut])
async def get_team_schedule(
    team_id: int = Path(..., description="Team ID"),
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    limit: int = Query(10, ge=1, le=50, description="Number of games to return"),
    db: Session = Depends(get_db),
) -> List[TeamScheduleGameOut]:
    """Get recent and upcoming games for a team."""
    wnba_service = WNBAService(db)
    schedule = wnba_service.get_team_schedule(team_id, season, limit)
    return [TeamScheduleGameOut(**game) for game in schedule]


@router.get("/teams/{team_id}/stats", response_model=TeamStatsOut)
async def get_team_stats(
    team_id: int = Path(..., description="Team ID"),
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    db: Session = Depends(get_db),
) -> TeamStatsOut:
    """Get aggregated team statistics."""
    wnba_service = WNBAService(db)
    stats = wnba_service.get_team_stats(team_id, season)
    if not stats:
        raise HTTPException(status_code=404, detail="Team or stats not found")
    return TeamStatsOut(**stats)


@router.get("/players/{player_id}/game-log", response_model=List[PlayerGameLogOut])
async def get_player_game_log(
    player_id: int = Path(..., description="Player ID"),
    limit: int = Query(10, ge=1, le=50, description="Number of games to return"),
    db: Session = Depends(get_db),
) -> List[PlayerGameLogOut]:
    """Get recent game log for a player."""
    wnba_service = WNBAService(db)
    game_log = wnba_service.get_player_game_log(player_id, limit)
    return [PlayerGameLogOut(**game) for game in game_log]


@router.get("/players/{player_id}/stats", response_model=DetailedPlayerStatsOut)
async def get_player_detailed_stats(
    player_id: int = Path(..., description="Player ID"),
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    db: Session = Depends(get_db),
) -> DetailedPlayerStatsOut:
    """Get detailed player statistics including advanced metrics."""
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
            # Return basic player info with zero stats
            return DetailedPlayerStatsOut(
                player_id=player.id,
                player_name=player.full_name,
                team_id=player.wnba_team_id,
                team_name=player.wnba_team.display_name if player.wnba_team else None,
                team_abbr=player.wnba_team.abbreviation if player.wnba_team else None,
                position=player.position,
                jersey_number=player.jersey_number,
                height=player.height,
                weight=player.weight,
                college=player.college,
                years_pro=player.years_pro,
                status=player.status,
                headshot_url=player.headshot_url,
                season=season,
            )

    return DetailedPlayerStatsOut(
        player_id=player.id,
        player_name=player.full_name,
        team_id=player.wnba_team_id,
        team_name=player.wnba_team.display_name if player.wnba_team else None,
        team_abbr=player.wnba_team.abbreviation if player.wnba_team else None,
        position=player.position,
        jersey_number=player.jersey_number,
        height=player.height,
        weight=player.weight,
        college=player.college,
        years_pro=player.years_pro,
        status=player.status,
        headshot_url=player.headshot_url,
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


@router.get("/league-leaders", response_model=List[LeagueLeaderOut])
async def get_league_leaders(
    stat_category: str = Query(..., description="Statistical category (points, rebounds, assists, etc.)"),
    season: Optional[int] = Query(None, description="Season year (defaults to current)"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return"),
    db: Session = Depends(get_db),
) -> List[LeagueLeaderOut]:
    """Get league leaders in a specific statistical category."""
    valid_categories = [
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
        "field_goal_percentage",
        "three_point_percentage",
        "free_throw_percentage",
        "minutes",
        "fantasy_points",
    ]

    if stat_category not in valid_categories:
        raise HTTPException(
            status_code=400, detail=f"Invalid stat category. Valid options: {', '.join(valid_categories)}"
        )

    wnba_service = WNBAService(db)
    leaders = wnba_service.get_league_leaders(stat_category, season, limit)
    return [LeagueLeaderOut(**leader) for leader in leaders]


@router.get("/players/search", response_model=Pagination[PlayerSearchResultOut])
async def search_players(
    query: Optional[str] = Query(None, description="Search by player name"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(50, ge=1, le=200, description="Number of players to return"),
    offset: int = Query(0, ge=0, description="Number of players to skip"),
    db: Session = Depends(get_db),
) -> Pagination[PlayerSearchResultOut]:
    """Search for players with various filters."""
    wnba_service = WNBAService(db)

    # Get total count for pagination
    players_query = db.query(Player)

    if query:
        players_query = players_query.filter(Player.full_name.ilike(f"%{query}%"))
    if team_id:
        players_query = players_query.filter(Player.wnba_team_id == team_id)
    if position:
        players_query = players_query.filter(Player.position == position)

    total = players_query.count()

    # Get search results
    search_results = wnba_service.search_players(query=query, team_id=team_id, position=position, limit=limit)[
        offset : offset + limit
    ]  # Apply offset manually

    items = [PlayerSearchResultOut(**player) for player in search_results]

    return Pagination[PlayerSearchResultOut](total=total, limit=limit, offset=offset, items=items)


@router.get("/players/trending", response_model=List[PlayerSearchResultOut])
async def get_trending_players(
    limit: int = Query(20, ge=1, le=50, description="Number of players to return"), db: Session = Depends(get_db)
) -> List[PlayerSearchResultOut]:
    """Get trending players based on recent performance."""
    wnba_service = WNBAService(db)

    # Get top performers by fantasy points for trending
    leaders = wnba_service.get_league_leaders("fantasy_points", limit=limit)

    trending = []
    for leader in leaders:
        player_data = wnba_service.search_players(limit=1)  # Get first player as template
        if player_data:
            # Get the actual player data
            player = db.query(Player).filter(Player.id == leader["player_id"]).first()
            if player:
                current_season = datetime.now().year
                season_stats = (
                    db.query(PlayerSeasonStats)
                    .filter(PlayerSeasonStats.player_id == player.id, PlayerSeasonStats.season == current_season)
                    .first()
                )

                trending.append(
                    PlayerSearchResultOut(
                        player_id=player.id,
                        full_name=player.full_name,
                        jersey_number=player.jersey_number,
                        position=player.position,
                        team_id=player.wnba_team_id,
                        team_name=leader["team_name"],
                        team_abbr=leader["team_abbr"],
                        height=player.height,
                        weight=player.weight,
                        college=player.college,
                        years_pro=player.years_pro,
                        status=player.status,
                        headshot_url=player.headshot_url,
                        ppg=season_stats.ppg if season_stats else 0.0,
                        rpg=season_stats.rpg if season_stats else 0.0,
                        apg=season_stats.apg if season_stats else 0.0,
                        games_played=season_stats.games_played if season_stats else 0,
                    )
                )

    return trending
