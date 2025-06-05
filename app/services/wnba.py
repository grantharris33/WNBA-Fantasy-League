"""WNBA service for teams, standings, and player statistics."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Game, Player, PlayerSeasonStats, PlayerTrends, Standings, StatLine, WNBATeam


class WNBAService:
    """Service for WNBA teams, standings, and player data."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_teams(self) -> List[WNBATeam]:
        """Get all WNBA teams."""
        return self.db.query(WNBATeam).order_by(WNBATeam.display_name).all()

    def get_team_by_id(self, team_id: int) -> Optional[WNBATeam]:
        """Get a specific WNBA team by ID."""
        return self.db.query(WNBATeam).filter(WNBATeam.id == team_id).first()

    def get_team_by_abbreviation(self, abbreviation: str) -> Optional[WNBATeam]:
        """Get a WNBA team by abbreviation."""
        return self.db.query(WNBATeam).filter(WNBATeam.abbreviation == abbreviation).first()

    def get_current_standings(self, season: Optional[int] = None) -> List[Dict]:
        """Get current standings for the season."""
        if season is None:
            season = datetime.now().year

        # Get the most recent standings date
        latest_date = self.db.query(func.max(Standings.date)).filter(Standings.season == season).scalar()

        if not latest_date:
            # Fallback to WNBATeam data if no standings available
            teams = self.db.query(WNBATeam).order_by(WNBATeam.win_percentage.desc(), WNBATeam.wins.desc()).all()

            standings = []
            for rank, team in enumerate(teams, 1):
                standings.append(
                    {
                        "rank": rank,
                        "team_id": team.id,
                        "team_name": team.display_name,
                        "team_abbr": team.abbreviation,
                        "wins": team.wins,
                        "losses": team.losses,
                        "win_percentage": team.win_percentage,
                        "games_behind": team.games_behind or 0.0,
                        "streak": team.streak,
                        "last_10": team.last_10,
                        "conference_rank": team.conference_rank,
                        "home_record": f"{0}-{0}",  # Default if no detailed data
                        "away_record": f"{0}-{0}",
                        "points_for": 0.0,
                        "points_against": 0.0,
                        "point_differential": 0.0,
                    }
                )
            return standings

        # Get standings for the latest date
        standings_query = (
            self.db.query(Standings, WNBATeam)
            .join(WNBATeam, Standings.team_id == WNBATeam.id)
            .filter(Standings.season == season, Standings.date == latest_date)
            .order_by(Standings.win_percentage.desc(), Standings.wins.desc())
        )

        standings = []
        for rank, (standing, team) in enumerate(standings_query.all(), 1):
            standings.append(
                {
                    "rank": rank,
                    "team_id": team.id,
                    "team_name": team.display_name,
                    "team_abbr": team.abbreviation,
                    "wins": standing.wins,
                    "losses": standing.losses,
                    "win_percentage": standing.win_percentage,
                    "games_behind": standing.games_behind,
                    "streak": team.streak,
                    "last_10": team.last_10,
                    "conference_rank": team.conference_rank,
                    "home_record": f"{standing.home_wins}-{standing.home_losses}",
                    "away_record": f"{standing.away_wins}-{standing.away_losses}",
                    "points_for": standing.points_for,
                    "points_against": standing.points_against,
                    "point_differential": standing.point_differential,
                }
            )

        return standings

    def get_team_roster(self, team_id: int, season: Optional[int] = None) -> List[Dict]:
        """Get roster for a specific WNBA team."""
        if season is None:
            season = datetime.now().year

        players = (
            self.db.query(Player)
            .filter(Player.wnba_team_id == team_id)
            .order_by(Player.jersey_number, Player.full_name)
            .all()
        )

        roster = []
        for player in players:
            # Get season stats if available
            season_stats = (
                self.db.query(PlayerSeasonStats)
                .filter(PlayerSeasonStats.player_id == player.id, PlayerSeasonStats.season == season)
                .first()
            )

            roster.append(
                {
                    "player_id": player.id,
                    "full_name": player.full_name,
                    "jersey_number": player.jersey_number,
                    "position": player.position,
                    "height": player.height,
                    "weight": player.weight,
                    "college": player.college,
                    "years_pro": player.years_pro,
                    "status": player.status,
                    "headshot_url": player.headshot_url,
                    # Season averages
                    "games_played": season_stats.games_played if season_stats else 0,
                    "ppg": season_stats.ppg if season_stats else 0.0,
                    "rpg": season_stats.rpg if season_stats else 0.0,
                    "apg": season_stats.apg if season_stats else 0.0,
                    "mpg": season_stats.mpg if season_stats else 0.0,
                    "fg_percentage": season_stats.fg_percentage if season_stats else 0.0,
                }
            )

        return roster

    def get_team_schedule(self, team_id: int, season: Optional[int] = None, limit: int = 10) -> List[Dict]:
        """Get recent and upcoming games for a team."""
        if season is None:
            season = datetime.now().year

        games = (
            self.db.query(Game)
            .filter(
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
                func.extract('year', Game.date) == season,
            )
            .order_by(Game.date.desc())
            .limit(limit)
            .all()
        )

        schedule = []
        for game in games:
            is_home = game.home_team_id == team_id
            opponent_id = game.away_team_id if is_home else game.home_team_id
            opponent = self.db.query(WNBATeam).filter(WNBATeam.id == opponent_id).first()

            team_score = game.home_score if is_home else game.away_score
            opponent_score = game.away_score if is_home else game.home_score

            schedule.append(
                {
                    "game_id": game.id,
                    "date": game.date,
                    "is_home": is_home,
                    "opponent_id": opponent_id,
                    "opponent_name": opponent.display_name if opponent else "Unknown",
                    "opponent_abbr": opponent.abbreviation if opponent else "UNK",
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "status": game.status,
                    "venue": game.venue,
                    "result": self._get_game_result(team_score, opponent_score, game.status),
                }
            )

        return schedule

    def get_team_stats(self, team_id: int, season: Optional[int] = None) -> Dict:
        """Get aggregated team statistics."""
        if season is None:
            season = datetime.now().year

        # Get team info
        team = self.db.query(WNBATeam).filter(WNBATeam.id == team_id).first()
        if not team:
            return {}

        # Get games for this team
        games = (
            self.db.query(Game)
            .filter(
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
                func.extract('year', Game.date) == season,
                Game.status == 'final',
            )
            .all()
        )

        total_points_for = 0
        total_points_against = 0
        wins = 0
        losses = 0
        home_wins = 0
        home_losses = 0
        away_wins = 0
        away_losses = 0

        for game in games:
            is_home = game.home_team_id == team_id
            team_score = game.home_score if is_home else game.away_score
            opponent_score = game.away_score if is_home else game.home_score

            total_points_for += team_score
            total_points_against += opponent_score

            if team_score > opponent_score:
                wins += 1
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1
            else:
                losses += 1
                if is_home:
                    home_losses += 1
                else:
                    away_losses += 1

        games_played = len(games)
        win_percentage = wins / games_played if games_played > 0 else 0.0

        return {
            "team_id": team_id,
            "team_name": team.display_name,
            "team_abbr": team.abbreviation,
            "games_played": games_played,
            "wins": wins,
            "losses": losses,
            "win_percentage": round(win_percentage, 3),
            "home_record": f"{home_wins}-{home_losses}",
            "away_record": f"{away_wins}-{away_losses}",
            "points_per_game": round(total_points_for / games_played, 1) if games_played > 0 else 0.0,
            "points_allowed_per_game": round(total_points_against / games_played, 1) if games_played > 0 else 0.0,
            "point_differential": round((total_points_for - total_points_against) / games_played, 1)
            if games_played > 0
            else 0.0,
        }

    def get_player_game_log(self, player_id: int, limit: int = 10) -> List[Dict]:
        """Get recent game log for a player."""
        stat_lines = (
            self.db.query(StatLine)
            .join(Game)
            .join(Player)
            .filter(StatLine.player_id == player_id)
            .order_by(Game.date.desc())
            .limit(limit)
            .all()
        )

        game_log = []
        for stat in stat_lines:
            game = stat.game
            opponent = None
            if stat.opponent_id:
                opponent = self.db.query(WNBATeam).filter(WNBATeam.id == stat.opponent_id).first()

            game_log.append(
                {
                    "game_id": game.id,
                    "date": game.date,
                    "opponent_id": stat.opponent_id,
                    "opponent_name": opponent.display_name if opponent else "Unknown",
                    "opponent_abbr": opponent.abbreviation if opponent else "UNK",
                    "is_home": stat.is_home_game,
                    "is_starter": stat.is_starter,
                    "minutes_played": stat.minutes_played,
                    "points": stat.points,
                    "rebounds": stat.rebounds,
                    "assists": stat.assists,
                    "steals": stat.steals,
                    "blocks": stat.blocks,
                    "turnovers": stat.turnovers,
                    "field_goals_made": stat.field_goals_made,
                    "field_goals_attempted": stat.field_goals_attempted,
                    "field_goal_percentage": stat.field_goal_percentage,
                    "three_pointers_made": stat.three_pointers_made,
                    "three_pointers_attempted": stat.three_pointers_attempted,
                    "three_point_percentage": stat.three_point_percentage,
                    "free_throws_made": stat.free_throws_made,
                    "free_throws_attempted": stat.free_throws_attempted,
                    "free_throw_percentage": stat.free_throw_percentage,
                    "plus_minus": stat.plus_minus,
                    "did_not_play": stat.did_not_play,
                }
            )

        return game_log

    def get_league_leaders(self, stat_category: str, season: Optional[int] = None, limit: int = 10) -> List[Dict]:
        """Get league leaders in a specific statistical category."""
        if season is None:
            season = datetime.now().year

        # Map stat categories to PlayerSeasonStats fields
        stat_mapping = {
            "points": PlayerSeasonStats.ppg,
            "rebounds": PlayerSeasonStats.rpg,
            "assists": PlayerSeasonStats.apg,
            "steals": PlayerSeasonStats.spg,
            "blocks": PlayerSeasonStats.bpg,
            "field_goal_percentage": PlayerSeasonStats.fg_percentage,
            "three_point_percentage": PlayerSeasonStats.three_point_percentage,
            "free_throw_percentage": PlayerSeasonStats.ft_percentage,
            "minutes": PlayerSeasonStats.mpg,
            "fantasy_points": PlayerSeasonStats.fantasy_ppg,
        }

        if stat_category not in stat_mapping:
            return []

        stat_field = stat_mapping[stat_category]

        leaders = (
            self.db.query(PlayerSeasonStats, Player, WNBATeam)
            .join(Player, PlayerSeasonStats.player_id == Player.id)
            .join(WNBATeam, Player.wnba_team_id == WNBATeam.id)
            .filter(PlayerSeasonStats.season == season, PlayerSeasonStats.games_played >= 5)  # Minimum games threshold
            .order_by(stat_field.desc())
            .limit(limit)
            .all()
        )

        result = []
        for rank, (stats, player, team) in enumerate(leaders, 1):
            # Map stat category to the correct field name
            field_mapping = {
                "points": "ppg",
                "rebounds": "rpg",
                "assists": "apg",
                "steals": "spg",
                "blocks": "bpg",
                "field_goal_percentage": "fg_percentage",
                "three_point_percentage": "three_point_percentage",
                "free_throw_percentage": "ft_percentage",
                "minutes": "mpg",
                "fantasy_points": "fantasy_ppg",
            }

            field_name = field_mapping.get(stat_category, stat_category)
            value = getattr(stats, field_name, 0.0)

            result.append(
                {
                    "rank": rank,
                    "player_id": player.id,
                    "player_name": player.full_name,
                    "team_id": team.id,
                    "team_name": team.display_name,
                    "team_abbr": team.abbreviation,
                    "games_played": stats.games_played,
                    "value": value,
                    "position": player.position,
                }
            )

        return result

    def _get_game_result(self, team_score: int, opponent_score: int, status: str) -> Optional[str]:
        """Get the result of a game (W/L) or None if not final."""
        if status != 'final':
            return None

        if team_score > opponent_score:
            return 'W'
        elif team_score < opponent_score:
            return 'L'
        else:
            return 'T'  # Tie (unlikely in basketball)

    def search_players(
        self,
        query: Optional[str] = None,
        team_id: Optional[int] = None,
        position: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Search for players with various filters."""
        players_query = self.db.query(Player).join(WNBATeam)

        if query:
            players_query = players_query.filter(Player.full_name.ilike(f"%{query}%"))

        if team_id:
            players_query = players_query.filter(Player.wnba_team_id == team_id)

        if position:
            players_query = players_query.filter(Player.position == position)

        players = players_query.order_by(Player.full_name).limit(limit).all()

        result = []
        for player in players:
            # Get current season stats
            current_season = datetime.now().year
            season_stats = (
                self.db.query(PlayerSeasonStats)
                .filter(PlayerSeasonStats.player_id == player.id, PlayerSeasonStats.season == current_season)
                .first()
            )

            result.append(
                {
                    "player_id": player.id,
                    "full_name": player.full_name,
                    "jersey_number": player.jersey_number,
                    "position": player.position,
                    "team_id": player.wnba_team_id,
                    "team_name": player.wnba_team.display_name if player.wnba_team else None,
                    "team_abbr": player.wnba_team.abbreviation if player.wnba_team else None,
                    "height": player.height,
                    "weight": player.weight,
                    "college": player.college,
                    "years_pro": player.years_pro,
                    "status": player.status,
                    "headshot_url": player.headshot_url,
                    # Current season stats
                    "ppg": season_stats.ppg if season_stats else 0.0,
                    "rpg": season_stats.rpg if season_stats else 0.0,
                    "apg": season_stats.apg if season_stats else 0.0,
                    "games_played": season_stats.games_played if season_stats else 0,
                }
            )

        return result
