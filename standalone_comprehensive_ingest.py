#!/usr/bin/env python3
"""
Standalone comprehensive statistics ingestion script.
This bypasses SQLAlchemy ORM issues to directly populate the database.
"""

import asyncio
import datetime as dt
import sqlite3
from typing import Any, Dict, List

from app.external_apis.rapidapi_client import wnba_client


def _parse_comprehensive_stats(stats: List[str]) -> dict[str, Any]:
    """Parse all 14 statistical categories from the API response."""

    def _to_float(val: str) -> float:
        try:
            if "-" in val:
                val = val.split("-")[0]
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def _to_int(val: str) -> int:
        try:
            if "-" in val:
                val = val.split("-")[0]
            return int(val)
        except (ValueError, TypeError):
            return 0

    def _parse_shooting(val: str) -> tuple[int, int, float]:
        """Parse shooting stats like '2-7' to return (made, attempted, percentage)"""
        try:
            if "-" in val:
                made, attempted = val.split("-")
                made, attempted = int(made), int(attempted)
                percentage = (made / attempted * 100) if attempted > 0 else 0.0
                return made, attempted, percentage
            else:
                made = int(val) if val else 0
                return made, 0, 0.0
        except (ValueError, TypeError):
            return 0, 0, 0.0

    if len(stats) < 14:
        # If stats array is incomplete, return zeros for safety
        return {
            "minutes_played": 0.0,
            "field_goals_made": 0,
            "field_goals_attempted": 0,
            "field_goal_percentage": 0.0,
            "three_pointers_made": 0,
            "three_pointers_attempted": 0,
            "three_point_percentage": 0.0,
            "free_throws_made": 0,
            "free_throws_attempted": 0,
            "free_throw_percentage": 0.0,
            "offensive_rebounds": 0,
            "defensive_rebounds": 0,
            "rebounds": 0.0,
            "assists": 0.0,
            "steals": 0.0,
            "blocks": 0.0,
            "turnovers": 0,
            "personal_fouls": 0,
            "plus_minus": 0,
            "points": 0.0,
        }

    # Parse shooting statistics
    fg_made, fg_attempted, fg_percentage = _parse_shooting(stats[1])
    threept_made, threept_attempted, threept_percentage = _parse_shooting(stats[2])
    ft_made, ft_attempted, ft_percentage = _parse_shooting(stats[3])

    return {
        "minutes_played": _to_float(stats[0]),
        "field_goals_made": fg_made,
        "field_goals_attempted": fg_attempted,
        "field_goal_percentage": fg_percentage,
        "three_pointers_made": threept_made,
        "three_pointers_attempted": threept_attempted,
        "three_point_percentage": threept_percentage,
        "free_throws_made": ft_made,
        "free_throws_attempted": ft_attempted,
        "free_throw_percentage": ft_percentage,
        "offensive_rebounds": _to_int(stats[4]),
        "defensive_rebounds": _to_int(stats[5]),
        "rebounds": _to_float(stats[6]),
        "assists": _to_float(stats[7]),
        "steals": _to_float(stats[8]),
        "blocks": _to_float(stats[9]),
        "turnovers": _to_int(stats[10]),
        "personal_fouls": _to_int(stats[11]),
        "plus_minus": _to_int(stats[12]),
        "points": _to_float(stats[13]),
    }


async def standalone_ingest(test_date: dt.date):
    """Standalone ingestion using direct SQL to avoid ORM issues."""

    date_iso = test_date.strftime("%Y-%m-%d")
    game_datetime = dt.datetime.combine(test_date, dt.time())

    print(f"Starting comprehensive stats ingestion for {date_iso}")

    # Fetch schedule
    try:
        year = test_date.strftime("%Y")
        month = test_date.strftime("%m")
        day = test_date.strftime("%d")
        games = await wnba_client.fetch_schedule(year, month, day)
    except Exception as e:
        print(f"Failed to fetch schedule: {e}")
        return

    if not games:
        print(f"No games found for {date_iso}")
        return

    conn = sqlite3.connect('prod.db')
    cursor = conn.cursor()

    processed_games = 0

    try:
        for game in games:
            game_id = str(game.get("id", ""))
            if not game_id:
                continue

            print(f"Processing game {game_id}")

            # Fetch box score
            try:
                box = await wnba_client.fetch_box_score(game_id)
            except Exception as e:
                print(f"Failed to fetch box score for {game_id}: {e}")
                continue

            # Extract game information
            header = box.get("header", {})
            competition = header.get("competitions", [{}])[0] if header.get("competitions") else {}
            competitors = competition.get("competitors", [])

            home_team_id = None
            away_team_id = None
            home_score = 0
            away_score = 0

            for competitor in competitors:
                if competitor.get("homeAway") == "home":
                    home_team_id = competitor.get("team", {}).get("id")
                    home_score = int(competitor.get("score", 0))
                elif competitor.get("homeAway") == "away":
                    away_team_id = competitor.get("team", {}).get("id")
                    away_score = int(competitor.get("score", 0))

            # Insert/update game record
            cursor.execute(
                """
                INSERT OR REPLACE INTO game
                (id, date, home_team_id, away_team_id, home_score, away_score, status, venue, attendance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    game_id,
                    game_datetime,
                    int(home_team_id) if home_team_id else None,
                    int(away_team_id) if away_team_id else None,
                    home_score,
                    away_score,
                    competition.get("status", {}).get("type", {}).get("name", "scheduled"),
                    competition.get("venue", {}).get("fullName"),
                    competition.get("attendance"),
                ),
            )

            # Process player stats
            players_blocks = box.get("players", [])
            stats_processed = 0

            for team_idx, team_block in enumerate(players_blocks):
                team_info = competitors[team_idx] if team_idx < len(competitors) else {}
                current_team_id = (
                    int(team_info.get("team", {}).get("id")) if team_info.get("team", {}).get("id") else None
                )
                is_home_team = team_info.get("homeAway") == "home"
                opponent_team_id = away_team_id if is_home_team else home_team_id

                statistics = team_block.get("statistics", [])
                for stat_block in statistics:
                    athletes = stat_block.get("athletes", [])
                    for athlete_block in athletes:
                        athlete = athlete_block.get("athlete")
                        if not athlete:
                            continue

                        player_id = int(athlete["id"])

                        # Upsert player
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO player (id, full_name, position)
                            VALUES (?, ?, ?)
                        """,
                            (player_id, athlete["displayName"], athlete.get("position", {}).get("abbreviation")),
                        )

                        # Handle DNP
                        did_not_play = athlete_block.get("didNotPlay", False)
                        is_starter = athlete_block.get("starter", False)

                        if did_not_play:
                            # Insert DNP record
                            cursor.execute(
                                """
                                INSERT OR REPLACE INTO stat_line
                                (player_id, game_id, game_date, did_not_play, team_id, opponent_id, is_home_game, is_starter,
                                 points, rebounds, assists, steals, blocks, minutes_played,
                                 field_goals_made, field_goals_attempted, field_goal_percentage,
                                 three_pointers_made, three_pointers_attempted, three_point_percentage,
                                 free_throws_made, free_throws_attempted, free_throw_percentage,
                                 offensive_rebounds, defensive_rebounds, turnovers, personal_fouls, plus_minus)
                                VALUES (?, ?, ?, 1, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                            """,
                                (
                                    player_id,
                                    game_id,
                                    game_datetime,
                                    current_team_id,
                                    opponent_team_id,
                                    is_home_team,
                                    is_starter,
                                ),
                            )
                            stats_processed += 1
                            continue

                        stats_arr = athlete_block.get("stats", [])
                        if not stats_arr:
                            continue

                        # Parse comprehensive stats
                        stat_vals = _parse_comprehensive_stats(stats_arr)

                        # Insert comprehensive stat line
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO stat_line
                            (player_id, game_id, game_date, team_id, opponent_id, is_home_game, is_starter, did_not_play,
                             points, rebounds, assists, steals, blocks, minutes_played,
                             field_goals_made, field_goals_attempted, field_goal_percentage,
                             three_pointers_made, three_pointers_attempted, three_point_percentage,
                             free_throws_made, free_throws_attempted, free_throw_percentage,
                             offensive_rebounds, defensive_rebounds, turnovers, personal_fouls, plus_minus)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                player_id,
                                game_id,
                                game_datetime,
                                current_team_id,
                                opponent_team_id,
                                is_home_team,
                                is_starter,
                                stat_vals["points"],
                                stat_vals["rebounds"],
                                stat_vals["assists"],
                                stat_vals["steals"],
                                stat_vals["blocks"],
                                stat_vals["minutes_played"],
                                stat_vals["field_goals_made"],
                                stat_vals["field_goals_attempted"],
                                stat_vals["field_goal_percentage"],
                                stat_vals["three_pointers_made"],
                                stat_vals["three_pointers_attempted"],
                                stat_vals["three_point_percentage"],
                                stat_vals["free_throws_made"],
                                stat_vals["free_throws_attempted"],
                                stat_vals["free_throw_percentage"],
                                stat_vals["offensive_rebounds"],
                                stat_vals["defensive_rebounds"],
                                stat_vals["turnovers"],
                                stat_vals["personal_fouls"],
                                stat_vals["plus_minus"],
                            ),
                        )
                        stats_processed += 1

            conn.commit()
            print(f"  Processed {stats_processed} stat lines for game {game_id}")
            processed_games += 1

        print(f"\n✅ Successfully processed {processed_games} games with comprehensive statistics")

        # Show sample results
        cursor.execute(
            """
            SELECT p.full_name, s.points, s.rebounds, s.assists,
                   s.field_goals_made, s.field_goals_attempted, s.field_goal_percentage,
                   s.three_pointers_made, s.three_pointers_attempted, s.did_not_play, s.is_starter
            FROM stat_line s
            JOIN player p ON p.id = s.player_id
            WHERE s.game_id IS NOT NULL
            LIMIT 5
        """
        )
        results = cursor.fetchall()

        if results:
            print("\nSample comprehensive statistics:")
            for row in results:
                name, pts, reb, ast, fgm, fga, fgp, tpm, tpa, dnp, starter = row
                print(
                    f"  {name}: {pts}pts, {reb}reb, {ast}ast, FG: {fgm}/{fga} ({fgp:.1f}%), "
                    f"3PT: {tpm}/{tpa}, DNP: {bool(dnp)}, Starter: {bool(starter)}"
                )

    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()
        await wnba_client.close()


if __name__ == "__main__":
    # Test with multiple dates to find games
    test_dates = [
        dt.date(2024, 6, 15),  # Early season 2024
        dt.date(2024, 7, 20),  # Mid-season 2024
        dt.date(2024, 8, 15),  # Late season 2024
        dt.date(2023, 7, 15),  # 2023 season
        dt.date(2023, 8, 15),  # 2023 season
    ]

    async def test_multiple_dates():
        for test_date in test_dates:
            print(f"\n{'='*60}")
            await standalone_ingest(test_date)

            # Check if we got data
            conn = sqlite3.connect('prod.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM game")
            game_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM stat_line WHERE game_id IS NOT NULL")
            stat_count = cursor.fetchone()[0]
            conn.close()

            print(f"Database state: {game_count} games, {stat_count} comprehensive stat lines")

            if game_count > 0:
                print("✅ Found games! Stopping search.")
                break
        else:
            print("❌ No games found for any test dates. May need to check API or try different dates.")

    asyncio.run(test_multiple_dates())
