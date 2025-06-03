#!/usr/bin/env python3
"""Demo script to showcase the analytics system functionality."""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.analytics import AnalyticsService
from app.models import Player, PlayerSeasonStats, PlayerTrends


def main():
    """Run analytics demo."""
    db = SessionLocal()
    analytics_service = AnalyticsService(db)

    try:
        print("=== WNBA Fantasy League Analytics Demo ===\n")

        # Get a sample player with stats
        player = db.query(Player).join(PlayerSeasonStats).first()

        if not player:
            print("No players with season stats found. Run data ingestion first.")
            return

        print(f"Analyzing player: {player.full_name}")
        print(f"Position: {player.position}")
        print(f"Team: {player.team_abbr}\n")

        # Get season stats
        season = datetime.now().year
        season_stats = db.query(PlayerSeasonStats).filter(
            PlayerSeasonStats.player_id == player.id,
            PlayerSeasonStats.season == season
        ).first()

        if season_stats:
            print("=== Season Statistics ===")
            print(f"Games Played: {season_stats.games_played}")
            print(f"PPG: {season_stats.ppg:.1f}")
            print(f"RPG: {season_stats.rpg:.1f}")
            print(f"APG: {season_stats.apg:.1f}")
            print(f"Fantasy PPG: {season_stats.fantasy_ppg:.1f}")
            print(f"PER: {season_stats.per:.1f}")
            print(f"True Shooting %: {season_stats.true_shooting_percentage:.1f}%")
            print(f"Consistency Score: {season_stats.consistency_score:.1f}")
            print(f"Ceiling: {season_stats.ceiling:.1f}")
            print(f"Floor: {season_stats.floor:.1f}\n")

        # Get trends
        trends = db.query(PlayerTrends).filter(
            PlayerTrends.player_id == player.id
        ).order_by(PlayerTrends.calculated_date.desc()).first()

        if trends:
            print("=== Recent Trends ===")
            print(f"Last 5 Games PPG: {trends.last_5_games_ppg:.1f}")
            print(f"Last 10 Games PPG: {trends.last_10_games_ppg:.1f}")
            print(f"Last 5 Games Fantasy: {trends.last_5_games_fantasy:.1f}")
            print(f"Points Trend: {'+' if trends.points_trend > 0 else ''}{trends.points_trend:.1f}")
            print(f"Fantasy Trend: {'+' if trends.fantasy_trend > 0 else ''}{trends.fantasy_trend:.1f}")

            if trends.is_hot:
                print(f"🔥 HOT STREAK: {trends.streak_games} games!")
            elif trends.is_cold:
                print(f"❄️  COLD STREAK: {trends.streak_games} games")
            print()

        # Calculate fresh analytics for demonstration
        print("=== Calculating Fresh Analytics ===")

        # Update season stats
        print("Updating season statistics...")
        analytics_service.update_player_season_stats(player.id, season)

        # Update trends
        print("Updating performance trends...")
        analytics_service.update_player_trends(player.id)

        # Check hot/cold streaks
        print("Checking for streaks...")
        streak_info = analytics_service.identify_hot_cold_streaks(player.id)

        if streak_info['is_hot']:
            print(f"✅ Player is HOT! {streak_info['streak_games']} game streak")
        elif streak_info['is_cold']:
            print(f"⚠️  Player is COLD. {streak_info['streak_games']} game slump")
        else:
            print("📊 Player performance is stable")

        # Fantasy consistency
        consistency = analytics_service.calculate_fantasy_consistency(player.id)
        if consistency < 5:
            print("💎 Very consistent fantasy performer")
        elif consistency < 10:
            print("👍 Reasonably consistent")
        else:
            print("🎲 High variance player")

        print("\n✅ Analytics demo completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()