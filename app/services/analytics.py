"""Analytics service for calculating advanced player statistics and fantasy metrics."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models import Game, MatchupAnalysis, Player, PlayerSeasonStats, PlayerTrends, StatLine, WNBATeam
from app.services.scoring import compute_fantasy_points


class AnalyticsService:
    """Service for calculating and managing advanced player analytics."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_player_efficiency_rating(self, player_id: int, season: int) -> float:
        """
        Calculate PER (Player Efficiency Rating) using the simplified formula.

        PER = (PTS + REB + AST + STL + BLK - Missed FG - Missed FT - TO) / Games Played
        """
        # Get all stat lines for the player in the season
        stat_lines = (
            self.db.query(StatLine)
            .join(Game)
            .filter(
                StatLine.player_id == player_id,
                func.extract('year', Game.date) == season,
                StatLine.did_not_play == False,
            )
            .all()
        )

        if not stat_lines:
            return 0.0

        total_per = 0.0
        games_played = 0

        for stat in stat_lines:
            if stat.minutes_played > 0:
                # Calculate missed shots
                missed_fg = stat.field_goals_attempted - stat.field_goals_made
                missed_ft = stat.free_throws_attempted - stat.free_throws_made

                # Calculate game PER
                game_per = (
                    stat.points
                    + stat.rebounds
                    + stat.assists
                    + stat.steals
                    + stat.blocks
                    - missed_fg
                    - missed_ft
                    - stat.turnovers
                )

                total_per += game_per
                games_played += 1

        return total_per / games_played if games_played > 0 else 0.0

    def calculate_true_shooting_percentage(self, player_stats: dict) -> float:
        """
        Calculate True Shooting Percentage.

        TS% = Points / (2 * (FGA + 0.44 * FTA))
        """
        points = player_stats.get('points', 0)
        fga = player_stats.get('field_goals_attempted', 0)
        fta = player_stats.get('free_throws_attempted', 0)

        denominator = 2 * (fga + 0.44 * fta)

        if denominator == 0:
            return 0.0

        return (points / denominator) * 100

    def calculate_usage_rate(self, player_id: int, game_id: str) -> float:
        """
        Calculate usage rate for a player in a specific game.

        Usage Rate = ((FGA + 0.44 * FTA + TO) * (Team Minutes / 5)) /
                     (Minutes Played * (Team FGA + 0.44 * Team FTA + Team TO))
        """
        # Get player stats
        player_stat = (
            self.db.query(StatLine).filter(StatLine.player_id == player_id, StatLine.game_id == game_id).first()
        )

        if not player_stat or player_stat.minutes_played == 0:
            return 0.0

        # Get team stats for the game
        team_stats = (
            self.db.query(
                func.sum(StatLine.field_goals_attempted).label('team_fga'),
                func.sum(StatLine.free_throws_attempted).label('team_fta'),
                func.sum(StatLine.turnovers).label('team_to'),
            )
            .filter(StatLine.game_id == game_id, StatLine.team_id == player_stat.team_id)
            .first()
        )

        if not team_stats:
            return 0.0

        # Calculate usage rate
        player_possessions = (
            player_stat.field_goals_attempted + 0.44 * player_stat.free_throws_attempted + player_stat.turnovers
        )

        team_possessions = team_stats.team_fga + 0.44 * team_stats.team_fta + team_stats.team_to

        if team_possessions == 0:
            return 0.0

        # Assume 240 total minutes (48 minutes * 5 players)
        usage_rate = (player_possessions * 240) / (player_stat.minutes_played * team_possessions)

        return usage_rate * 100

    def calculate_fantasy_consistency(self, player_id: int, games: int = 10) -> float:
        """
        Calculate consistency score based on fantasy point variance.
        Lower score = more consistent.
        """
        # Get recent fantasy scores
        recent_stats = (
            self.db.query(StatLine)
            .filter(StatLine.player_id == player_id, StatLine.did_not_play == False)
            .order_by(desc(StatLine.game_date))
            .limit(games)
            .all()
        )

        if len(recent_stats) < 3:  # Need at least 3 games
            return 0.0

        # Calculate fantasy points for each game
        fantasy_points = []
        for stat in recent_stats:
            points = compute_fantasy_points(stat)
            fantasy_points.append(points)

        # Calculate standard deviation
        if fantasy_points:
            return float(np.std(fantasy_points))

        return 0.0

    def identify_hot_cold_streaks(self, player_id: int) -> Dict[str, any]:
        """
        Identify if player is on hot or cold streak.
        Hot: 3+ consecutive games above season average
        Cold: 3+ consecutive games below season average
        """
        # Get player's season average
        season_stats = (
            self.db.query(PlayerSeasonStats)
            .filter(PlayerSeasonStats.player_id == player_id, PlayerSeasonStats.season == datetime.now().year)
            .first()
        )

        if not season_stats:
            return {"is_hot": False, "is_cold": False, "streak_games": 0}

        # Get recent games
        recent_stats = (
            self.db.query(StatLine)
            .filter(StatLine.player_id == player_id, StatLine.did_not_play == False)
            .order_by(desc(StatLine.game_date))
            .limit(10)
            .all()
        )

        if len(recent_stats) < 3:
            return {"is_hot": False, "is_cold": False, "streak_games": 0}

        # Check streak
        streak_type = None
        streak_count = 0

        for stat in recent_stats:
            fantasy_points = compute_fantasy_points(stat)

            if fantasy_points > season_stats.fantasy_ppg * 1.15:  # 15% above average
                if streak_type == "hot":
                    streak_count += 1
                else:
                    streak_type = "hot"
                    streak_count = 1
            elif fantasy_points < season_stats.fantasy_ppg * 0.85:  # 15% below average
                if streak_type == "cold":
                    streak_count += 1
                else:
                    streak_type = "cold"
                    streak_count = 1
            else:
                break  # Streak ended

        return {
            "is_hot": streak_type == "hot" and streak_count >= 3,
            "is_cold": streak_type == "cold" and streak_count >= 3,
            "streak_games": streak_count if streak_count >= 3 else 0,
            "streak_type": streak_type if streak_count >= 3 else None,
        }

    def project_fantasy_points(self, player_id: int, opponent_id: int) -> float:
        """
        Project fantasy points for upcoming matchup based on:
        1. Recent performance (40%)
        2. Season average (30%)
        3. Historical matchup data (20%)
        4. Opponent defensive rating (10%)
        """
        # Get recent performance
        recent_stats = (
            self.db.query(StatLine)
            .filter(StatLine.player_id == player_id, StatLine.did_not_play == False)
            .order_by(desc(StatLine.game_date))
            .limit(5)
            .all()
        )

        recent_avg = 0.0
        if recent_stats:
            recent_points = [compute_fantasy_points(s) for s in recent_stats]
            recent_avg = sum(recent_points) / len(recent_points)

        # Get season average
        season_stats = (
            self.db.query(PlayerSeasonStats)
            .filter(PlayerSeasonStats.player_id == player_id, PlayerSeasonStats.season == datetime.now().year)
            .first()
        )

        season_avg = season_stats.fantasy_ppg if season_stats else recent_avg

        # Get historical matchup data
        matchup_data = (
            self.db.query(MatchupAnalysis)
            .filter(
                MatchupAnalysis.player_id == player_id,
                MatchupAnalysis.opponent_team_id == opponent_id,
                MatchupAnalysis.season == datetime.now().year,
            )
            .first()
        )

        matchup_avg = matchup_data.avg_fantasy_points if matchup_data else season_avg

        # Get opponent defensive rating (simplified)
        opponent_stats = (
            self.db.query(func.avg(StatLine.points).label('points_allowed'))
            .join(Game)
            .filter(Game.away_team_id == opponent_id, func.extract('year', Game.date) == datetime.now().year)
            .first()
        )

        # Calculate defensive factor (1.0 = average, >1.0 = weak defense, <1.0 = strong defense)
        league_avg_points = 80.0  # Approximate WNBA average
        defensive_factor = 1.0
        if opponent_stats and opponent_stats.points_allowed:
            defensive_factor = opponent_stats.points_allowed / league_avg_points

        # Weighted projection
        projection = recent_avg * 0.4 + season_avg * 0.3 + matchup_avg * 0.2 + (season_avg * defensive_factor) * 0.1

        return round(projection, 1)

    def update_player_season_stats(self, player_id: int, season: int) -> PlayerSeasonStats:
        """Update or create season statistics for a player."""
        # Get all games for the season
        stat_lines = (
            self.db.query(StatLine)
            .join(Game)
            .filter(
                StatLine.player_id == player_id,
                func.extract('year', Game.date) == season,
                StatLine.did_not_play == False,
            )
            .all()
        )

        if not stat_lines:
            return None

        # Calculate aggregates
        games_played = len(stat_lines)
        games_started = sum(1 for s in stat_lines if s.is_starter)

        # Calculate per-game averages
        total_stats = {
            'points': sum(s.points for s in stat_lines),
            'rebounds': sum(s.rebounds for s in stat_lines),
            'assists': sum(s.assists for s in stat_lines),
            'steals': sum(s.steals for s in stat_lines),
            'blocks': sum(s.blocks for s in stat_lines),
            'turnovers': sum(s.turnovers for s in stat_lines),
            'minutes': sum(s.minutes_played for s in stat_lines),
            'fgm': sum(s.field_goals_made for s in stat_lines),
            'fga': sum(s.field_goals_attempted for s in stat_lines),
            '3pm': sum(s.three_pointers_made for s in stat_lines),
            '3pa': sum(s.three_pointers_attempted for s in stat_lines),
            'ftm': sum(s.free_throws_made for s in stat_lines),
            'fta': sum(s.free_throws_attempted for s in stat_lines),
        }

        # Calculate shooting percentages
        fg_pct = (total_stats['fgm'] / total_stats['fga'] * 100) if total_stats['fga'] > 0 else 0
        three_pct = (total_stats['3pm'] / total_stats['3pa'] * 100) if total_stats['3pa'] > 0 else 0
        ft_pct = (total_stats['ftm'] / total_stats['fta'] * 100) if total_stats['fta'] > 0 else 0

        # Calculate fantasy points
        fantasy_points = [compute_fantasy_points(s) for s in stat_lines]
        fantasy_avg = sum(fantasy_points) / len(fantasy_points) if fantasy_points else 0
        fantasy_std = float(np.std(fantasy_points)) if len(fantasy_points) > 1 else 0
        fantasy_ceiling = max(fantasy_points) if fantasy_points else 0
        fantasy_floor = min(fantasy_points) if fantasy_points else 0

        # Calculate advanced metrics
        per = self.calculate_player_efficiency_rating(player_id, season)
        ts_pct = self.calculate_true_shooting_percentage(
            {
                'points': total_stats['points'],
                'field_goals_attempted': total_stats['fga'],
                'free_throws_attempted': total_stats['fta'],
            }
        )

        # Get or create season stats record
        season_stats = (
            self.db.query(PlayerSeasonStats)
            .filter(PlayerSeasonStats.player_id == player_id, PlayerSeasonStats.season == season)
            .first()
        )

        if not season_stats:
            season_stats = PlayerSeasonStats(player_id=player_id, season=season)
            self.db.add(season_stats)

        # Update values
        season_stats.games_played = games_played
        season_stats.games_started = games_started
        season_stats.ppg = total_stats['points'] / games_played
        season_stats.rpg = total_stats['rebounds'] / games_played
        season_stats.apg = total_stats['assists'] / games_played
        season_stats.spg = total_stats['steals'] / games_played
        season_stats.bpg = total_stats['blocks'] / games_played
        season_stats.topg = total_stats['turnovers'] / games_played
        season_stats.mpg = total_stats['minutes'] / games_played
        season_stats.fg_percentage = fg_pct
        season_stats.three_point_percentage = three_pct
        season_stats.ft_percentage = ft_pct
        season_stats.per = per
        season_stats.true_shooting_percentage = ts_pct
        season_stats.fantasy_ppg = fantasy_avg
        season_stats.consistency_score = fantasy_std
        season_stats.ceiling = fantasy_ceiling
        season_stats.floor = fantasy_floor
        season_stats.last_updated = datetime.utcnow()

        self.db.commit()
        return season_stats

    def update_player_trends(self, player_id: int) -> PlayerTrends:
        """Update trend data for a player."""
        today = date.today()

        # Get or create trends record
        trends = (
            self.db.query(PlayerTrends)
            .filter(PlayerTrends.player_id == player_id, PlayerTrends.calculated_date == today)
            .first()
        )

        if not trends:
            trends = PlayerTrends(player_id=player_id, calculated_date=today)
            self.db.add(trends)

        # Get last 5 and 10 games
        recent_stats = (
            self.db.query(StatLine)
            .filter(StatLine.player_id == player_id, StatLine.did_not_play == False)
            .order_by(desc(StatLine.game_date))
            .limit(10)
            .all()
        )

        if not recent_stats:
            self.db.commit()
            return trends

        # Calculate averages
        last_5 = recent_stats[:5]
        last_10 = recent_stats

        if last_5:
            trends.last_5_games_ppg = sum(s.points for s in last_5) / len(last_5)
            trends.last_5_games_rpg = sum(s.rebounds for s in last_5) / len(last_5)
            trends.last_5_games_apg = sum(s.assists for s in last_5) / len(last_5)
            trends.last_5_games_fantasy = sum(compute_fantasy_points(s) for s in last_5) / len(last_5)

        if last_10:
            trends.last_10_games_ppg = sum(s.points for s in last_10) / len(last_10)
            trends.last_10_games_rpg = sum(s.rebounds for s in last_10) / len(last_10)
            trends.last_10_games_apg = sum(s.assists for s in last_10) / len(last_10)
            trends.last_10_games_fantasy = sum(compute_fantasy_points(s) for s in last_10) / len(last_10)

        # Calculate trends (simple linear regression slope)
        if len(recent_stats) >= 3:
            points = [s.points for s in recent_stats[:5]]
            fantasy = [compute_fantasy_points(s) for s in recent_stats[:5]]
            minutes = [s.minutes_played for s in recent_stats[:5]]

            # Simple trend calculation (positive = improving)
            trends.points_trend = (points[0] - points[-1]) / len(points) if len(points) > 1 else 0
            trends.fantasy_trend = (fantasy[0] - fantasy[-1]) / len(fantasy) if len(fantasy) > 1 else 0
            trends.minutes_trend = (minutes[0] - minutes[-1]) / len(minutes) if len(minutes) > 1 else 0

        # Check hot/cold streaks
        streak_info = self.identify_hot_cold_streaks(player_id)
        trends.is_hot = streak_info['is_hot']
        trends.is_cold = streak_info['is_cold']
        trends.streak_games = streak_info['streak_games']
        trends.last_updated = datetime.utcnow()

        self.db.commit()
        return trends

    def update_matchup_analysis(self, player_id: int, opponent_team_id: int, season: int) -> MatchupAnalysis:
        """Update matchup analysis for a player against a specific team."""
        # Get all games against this opponent
        matchup_stats = (
            self.db.query(StatLine)
            .filter(
                StatLine.player_id == player_id,
                StatLine.opponent_id == opponent_team_id,
                func.extract('year', StatLine.game_date) == season,
                StatLine.did_not_play == False,
            )
            .all()
        )

        # Get or create matchup record
        matchup = (
            self.db.query(MatchupAnalysis)
            .filter(
                MatchupAnalysis.player_id == player_id,
                MatchupAnalysis.opponent_team_id == opponent_team_id,
                MatchupAnalysis.season == season,
            )
            .first()
        )

        if not matchup:
            matchup = MatchupAnalysis(player_id=player_id, opponent_team_id=opponent_team_id, season=season)
            self.db.add(matchup)

        if matchup_stats:
            # Calculate averages
            games = len(matchup_stats)
            matchup.games_played = games
            matchup.avg_points = sum(s.points for s in matchup_stats) / games
            matchup.avg_rebounds = sum(s.rebounds for s in matchup_stats) / games
            matchup.avg_assists = sum(s.assists for s in matchup_stats) / games
            matchup.avg_steals = sum(s.steals for s in matchup_stats) / games
            matchup.avg_blocks = sum(s.blocks for s in matchup_stats) / games
            matchup.avg_minutes = sum(s.minutes_played for s in matchup_stats) / games

            # Calculate fantasy points
            fantasy_points = [compute_fantasy_points(s) for s in matchup_stats]
            matchup.avg_fantasy_points = sum(fantasy_points) / len(fantasy_points)
            matchup.fantasy_points_std = float(np.std(fantasy_points)) if len(fantasy_points) > 1 else 0
            matchup.best_fantasy_game = max(fantasy_points) if fantasy_points else 0
            matchup.worst_fantasy_game = min(fantasy_points) if fantasy_points else 0

        # Get opponent defensive stats (simplified)
        opponent_games = (
            self.db.query(Game)
            .filter(
                and_(
                    func.extract('year', Game.date) == season,
                    or_(Game.home_team_id == opponent_team_id, Game.away_team_id == opponent_team_id),
                )
            )
            .count()
        )

        if opponent_games > 0:
            # Calculate points allowed per game
            points_allowed = (
                self.db.query(func.avg(StatLine.points))
                .join(Game)
                .filter(StatLine.opponent_id == opponent_team_id, func.extract('year', Game.date) == season)
                .scalar()
                or 0
            )

            matchup.opponent_points_allowed_pg = points_allowed

        matchup.last_updated = datetime.utcnow()
        self.db.commit()
        return matchup

    def calculate_all_analytics(self, season: int = None):
        """Run all analytics calculations for all active players."""
        if season is None:
            season = datetime.now().year

        # Get all active players with recent games
        active_players = (
            self.db.query(Player)
            .join(StatLine)
            .filter(func.extract('year', StatLine.game_date) == season)
            .distinct()
            .all()
        )

        for player in active_players:
            try:
                # Update season stats
                self.update_player_season_stats(player.id, season)

                # Update trends
                self.update_player_trends(player.id)

                # Update matchup analyses for all teams
                teams = self.db.query(WNBATeam).all()
                for team in teams:
                    self.update_matchup_analysis(player.id, team.id, season)

            except Exception as e:
                print(f"Error updating analytics for player {player.id}: {e}")
                self.db.rollback()
                continue
