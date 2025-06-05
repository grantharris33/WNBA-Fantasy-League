#!/usr/bin/env python3
"""
Test script for comprehensive game statistics ingestion and retrieval.
"""

import asyncio
import datetime as dt

from sqlalchemy import text

from app import models
from app.core.database import SessionLocal
from app.jobs.ingest import ingest_stat_lines
from app.services.scoring import compute_fantasy_points


async def test_comprehensive_stats():
    """Test comprehensive stats ingestion and database storage."""

    # Test ingestion for a recent date - try different dates
    test_dates = [
        dt.date(2025, 5, 9),  # Mid-season
        dt.date(2025, 5, 16),  # Earlier in season
        dt.date(2025, 5, 23),  # Playoffs
    ]

    for test_date in test_dates:
        print(f"\nTesting comprehensive stats ingestion for {test_date}")

        try:
            await ingest_stat_lines(test_date)
            print("✅ Ingestion completed successfully")
        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            continue

        # Check database for results using raw SQL to avoid SQLAlchemy issues
        session = SessionLocal()
        try:
            # Check games first
            games_count = session.execute(
                text("SELECT COUNT(*) FROM game WHERE date(date) = :date"), {"date": test_date.isoformat()}
            ).scalar()

            print(f"Found {games_count} games for {test_date}")

            if games_count > 0:
                games = session.execute(
                    text(
                        """
                    SELECT id, status, home_team_id, home_score, away_team_id, away_score, venue
                    FROM game
                    WHERE date(date) = :date
                """
                    ),
                    {"date": test_date.isoformat()},
                ).fetchall()

                for game in games:
                    game_id, status, home_id, home_score, away_id, away_score, venue = game
                    print(f"\nGame {game_id}: {status}")
                    print(f"  Home: {home_id} ({home_score})")
                    print(f"  Away: {away_id} ({away_score})")
                    print(f"  Venue: {venue}")

                    # Check stat lines
                    stat_count = session.execute(
                        text("SELECT COUNT(*) FROM stat_line WHERE game_id = :game_id"), {"game_id": game_id}
                    ).scalar()

                    print(f"  Found {stat_count} stat lines")

                    if stat_count > 0:
                        # Get a few examples using raw SQL
                        results = session.execute(
                            text(
                                """
                            SELECT p.full_name, s.points, s.rebounds, s.assists,
                                   s.field_goals_made, s.field_goals_attempted, s.field_goal_percentage,
                                   s.three_pointers_made, s.three_pointers_attempted, s.did_not_play,
                                   s.turnovers, s.steals, s.blocks, s.minutes_played
                            FROM stat_line s
                            JOIN player p ON p.id = s.player_id
                            WHERE s.game_id = :game_id
                            LIMIT 3
                        """
                            ),
                            {"game_id": game_id},
                        ).fetchall()

                        for row in results:
                            name, pts, reb, ast, fgm, fga, fgp, tpm, tpa, dnp, to, stl, blk, mins = row
                            print(
                                f"    {name}: {pts}pts, {reb}reb, {ast}ast, "
                                f"FG: {fgm}/{fga} ({fgp:.1f}%), "
                                f"3PT: {tpm}/{tpa}, TO: {to}, STL: {stl}, BLK: {blk}, "
                                f"MIN: {mins}, DNP: {bool(dnp)}"
                            )

                            # Test fantasy scoring with turnovers
                            if not dnp:
                                fantasy_pts = compute_fantasy_points(
                                    {
                                        "points": pts,
                                        "rebounds": reb,
                                        "assists": ast,
                                        "steals": stl,
                                        "blocks": blk,
                                        "turnovers": to,
                                    }
                                )
                                print(f"      Fantasy Points: {fantasy_pts}")

                        # Test comprehensive stats coverage
                        comprehensive_stats = session.execute(
                            text(
                                """
                            SELECT COUNT(*) as total,
                                   SUM(CASE WHEN minutes_played > 0 THEN 1 ELSE 0 END) as with_minutes,
                                   SUM(CASE WHEN field_goals_attempted > 0 THEN 1 ELSE 0 END) as with_fg,
                                   SUM(CASE WHEN three_pointers_attempted > 0 THEN 1 ELSE 0 END) as with_3pt,
                                   SUM(CASE WHEN free_throws_attempted > 0 THEN 1 ELSE 0 END) as with_ft,
                                   SUM(CASE WHEN turnovers > 0 THEN 1 ELSE 0 END) as with_turnovers,
                                   SUM(CASE WHEN did_not_play = 1 THEN 1 ELSE 0 END) as dnp_count
                            FROM stat_line
                            WHERE game_id = :game_id
                        """
                            ),
                            {"game_id": game_id},
                        ).fetchone()

                        total, with_minutes, with_fg, with_3pt, with_ft, with_turnovers, dnp_count = comprehensive_stats
                        print("  Comprehensive stats coverage:")
                        print(f"    Total players: {total}")
                        print(f"    With minutes: {with_minutes}")
                        print(f"    With field goals: {with_fg}")
                        print(f"    With 3-pointers: {with_3pt}")
                        print(f"    With free throws: {with_ft}")
                        print(f"    With turnovers: {with_turnovers}")
                        print(f"    DNP players: {dnp_count}")

                print(f"\n✅ Database verification completed successfully for {test_date}")
                break  # Found data, stop trying other dates

        except Exception as e:
            print(f"❌ Database verification failed: {e}")
            import traceback

            traceback.print_exc()
        finally:
            session.close()

    # Check ingest logs
    session = SessionLocal()
    try:
        logs = session.query(models.IngestLog).order_by(models.IngestLog.timestamp.desc()).limit(10).all()
        print(f"\nRecent ingest logs ({len(logs)} entries):")
        for log in logs:
            print(f"  {log.timestamp}: {log.message}")
    except Exception as e:
        print(f"Error reading logs: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(test_comprehensive_stats())
