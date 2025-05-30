#!/usr/bin/env python3
"""
Comprehensive test script for WNBA RapidAPI integration.

This script tests all endpoints with real API calls to verify:
1. API key authentication works
2. All endpoints return expected data structure
3. Rate limiting is handled gracefully
4. Box score data can be parsed correctly
5. Schedule data contains valid game IDs

Usage:
    export RAPIDAPI_KEY="your_key_here"
    python scripts/test_real_api.py

Requirements:
    - RapidAPI subscription to WNBA API: https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/wnba-api
    - API key set in RAPIDAPI_KEY environment variable
    - Basic subscription includes 500 requests/month
    - Endpoints used:
      * /wnbaschedule - Get game schedules
      * /wnbabox - Get box scores with player stats
      * /wnbasummary - Get game summaries
      * /wnbaplay - Get play-by-play data
      * /wnba-news - Get WNBA news
      * /injuries - Get injury reports
"""

import asyncio
import datetime as dt
import os
import sys
from typing import Any, Dict, List

from app.external_apis.rapidapi_client import wnba_client, RapidApiError, RateLimitError, ApiKeyError


class ApiTester:
    """Test suite for WNBA RapidAPI endpoints."""

    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log_pass(self, test_name: str, message: str = ""):
        """Log a successful test."""
        print(f"✅ {test_name}: PASSED" + (f" - {message}" if message else ""))
        self.results["passed"] += 1

    def log_fail(self, test_name: str, error: str):
        """Log a failed test."""
        print(f"❌ {test_name}: FAILED - {error}")
        self.results["failed"] += 1
        self.results["errors"].append(f"{test_name}: {error}")

    async def test_schedule_endpoint(self) -> List[Dict[str, Any]]:
        """Test the schedule endpoint with a recent date."""
        test_name = "Schedule Endpoint"
        try:
            # Test with yesterday's date
            yesterday = (dt.datetime.utcnow() - dt.timedelta(days=1)).date()
            year = yesterday.strftime("%Y")
            month = yesterday.strftime("%m")
            day = yesterday.strftime("%d")

            games = await wnba_client.fetch_schedule(year, month, day)

            if not isinstance(games, list):
                self.log_fail(test_name, f"Expected list, got {type(games)}")
                return []

            if games:
                # Validate first game structure
                game = games[0]
                required_fields = ["id", "date", "teams"]
                missing_fields = [field for field in required_fields if field not in game]

                if missing_fields:
                    self.log_fail(test_name, f"Missing required fields: {missing_fields}")
                    return []

                self.log_pass(test_name, f"Found {len(games)} games for {yesterday}")
            else:
                self.log_pass(test_name, f"No games found for {yesterday} (expected during off-season)")

            return games

        except RateLimitError as e:
            self.log_fail(test_name, f"Rate limit exceeded: {e}")
            return []
        except ApiKeyError as e:
            self.log_fail(test_name, f"API key error: {e}")
            return []
        except Exception as e:
            self.log_fail(test_name, f"Unexpected error: {e}")
            return []

    async def test_box_score_endpoint(self, games: List[Dict[str, Any]]):
        """Test the box score endpoint with a real game ID."""
        test_name = "Box Score Endpoint"

        if not games:
            # Use a known game ID from the sample data
            test_game_id = "401244185"  # From the sample output
            print(f"🔍 No recent games found, testing with sample game ID: {test_game_id}")
        else:
            test_game_id = games[0]["id"]

        try:
            box_score = await wnba_client.fetch_box_score(str(test_game_id))

            if not isinstance(box_score, dict):
                self.log_fail(test_name, f"Expected dict, got {type(box_score)}")
                return

            # Validate box score structure
            if "players" not in box_score:
                self.log_fail(test_name, "Missing 'players' field in box score")
                return

            players_data = box_score["players"]
            if not isinstance(players_data, list):
                self.log_fail(test_name, f"Expected players to be list, got {type(players_data)}")
                return

            # Test stats parsing
            stats_found = 0
            for team_block in players_data:
                statistics = team_block.get("statistics", [])
                for stat_block in statistics:
                    athletes = stat_block.get("athletes", [])
                    for athlete_block in athletes:
                        stats_arr = athlete_block.get("stats", [])
                        if stats_arr and len(stats_arr) >= 14:
                            stats_found += 1
                            # Test that we can parse the stats
                            try:
                                points = float(stats_arr[13])  # PTS should be last
                                rebounds = float(stats_arr[6])  # REB
                                assists = float(stats_arr[7])   # AST
                                steals = float(stats_arr[8])    # STL
                                blocks = float(stats_arr[9])    # BLK
                            except (ValueError, IndexError) as e:
                                self.log_fail(test_name, f"Error parsing stats array: {e}")
                                return

            if stats_found > 0:
                self.log_pass(test_name, f"Successfully parsed {stats_found} player stat lines")
            else:
                self.log_fail(test_name, "No valid player stats found in box score")

        except RateLimitError as e:
            self.log_fail(test_name, f"Rate limit exceeded: {e}")
        except ApiKeyError as e:
            self.log_fail(test_name, f"API key error: {e}")
        except Exception as e:
            self.log_fail(test_name, f"Unexpected error: {e}")

    async def test_game_summary_endpoint(self, games: List[Dict[str, Any]]):
        """Test the game summary endpoint."""
        test_name = "Game Summary Endpoint"

        if not games:
            test_game_id = "401244185"  # Sample game ID
        else:
            test_game_id = games[0]["id"]

        try:
            summary = await wnba_client.fetch_game_summary(str(test_game_id))

            if not isinstance(summary, dict):
                self.log_fail(test_name, f"Expected dict, got {type(summary)}")
                return

            self.log_pass(test_name, "Successfully fetched game summary")

        except RateLimitError as e:
            self.log_fail(test_name, f"Rate limit exceeded: {e}")
        except ApiKeyError as e:
            self.log_fail(test_name, f"API key error: {e}")
        except Exception as e:
            self.log_fail(test_name, f"Unexpected error: {e}")

    async def test_playbyplay_endpoint(self, games: List[Dict[str, Any]]):
        """Test the play-by-play endpoint."""
        test_name = "Play-by-Play Endpoint"

        if not games:
            test_game_id = "401244185"  # Sample game ID
        else:
            test_game_id = games[0]["id"]

        try:
            playbyplay = await wnba_client.fetch_game_playbyplay(str(test_game_id))

            if not isinstance(playbyplay, dict):
                self.log_fail(test_name, f"Expected dict, got {type(playbyplay)}")
                return

            self.log_pass(test_name, "Successfully fetched play-by-play data")

        except RateLimitError as e:
            self.log_fail(test_name, f"Rate limit exceeded: {e}")
        except ApiKeyError as e:
            self.log_fail(test_name, f"API key error: {e}")
        except Exception as e:
            self.log_fail(test_name, f"Unexpected error: {e}")

    async def test_news_endpoint(self):
        """Test the WNBA news endpoint."""
        test_name = "WNBA News Endpoint"

        try:
            news = await wnba_client.fetch_wnba_news(limit=5)

            if not isinstance(news, (dict, list)):
                self.log_fail(test_name, f"Expected dict or list, got {type(news)}")
                return

            self.log_pass(test_name, "Successfully fetched WNBA news")

        except RateLimitError as e:
            self.log_fail(test_name, f"Rate limit exceeded: {e}")
        except ApiKeyError as e:
            self.log_fail(test_name, f"API key error: {e}")
        except Exception as e:
            self.log_fail(test_name, f"Unexpected error: {e}")

    async def test_injuries_endpoint(self):
        """Test the injuries endpoint."""
        test_name = "Injuries Endpoint"

        try:
            injuries = await wnba_client.fetch_league_injuries()

            if not isinstance(injuries, (dict, list)):
                self.log_fail(test_name, f"Expected dict or list, got {type(injuries)}")
                return

            self.log_pass(test_name, "Successfully fetched injury data")

        except RateLimitError as e:
            self.log_fail(test_name, f"Rate limit exceeded: {e}")
        except ApiKeyError as e:
            self.log_fail(test_name, f"API key error: {e}")
        except Exception as e:
            self.log_fail(test_name, f"Unexpected error: {e}")

    async def run_all_tests(self):
        """Run all API endpoint tests."""
        print("🚀 Starting WNBA RapidAPI Integration Tests...")
        print("=" * 60)

        # Check API key
        api_key = os.getenv("RAPIDAPI_KEY") or os.getenv("WNBA_API_KEY")
        if not api_key:
            print("❌ RAPIDAPI_KEY environment variable not set!")
            print("Please set your RapidAPI key: export RAPIDAPI_KEY='your_key_here'")
            return False

        print(f"🔑 API Key configured: {api_key[:8]}...")
        print()

        # Test schedule endpoint first to get real game IDs
        games = await self.test_schedule_endpoint()

        # Test other endpoints
        await self.test_box_score_endpoint(games)
        await self.test_game_summary_endpoint(games)
        await self.test_playbyplay_endpoint(games)
        await self.test_news_endpoint()
        await self.test_injuries_endpoint()

        # Close the client
        await wnba_client.close()

        # Print summary
        print()
        print("=" * 60)
        print("📊 Test Results Summary:")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")

        if self.results["errors"]:
            print("\n🔍 Error Details:")
            for error in self.results["errors"]:
                print(f"   • {error}")

        success_rate = self.results["passed"] / (self.results["passed"] + self.results["failed"]) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")

        if self.results["failed"] == 0:
            print("\n🎉 All tests passed! RapidAPI integration is working correctly.")
            return True
        else:
            print(f"\n⚠️  {self.results['failed']} tests failed. Please check the errors above.")
            return False


async def main():
    """Main function to run the API tests."""
    tester = ApiTester()
    success = await tester.run_all_tests()

    if not success:
        sys.exit(1)

    print("\n📚 API Documentation:")
    print("   • RapidAPI WNBA API: https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/wnba-api")
    print("   • Subscription needed: Basic (500 requests/month) or higher")
    print("   • Endpoints tested: schedule, box scores, summaries, play-by-play, news, injuries")


if __name__ == "__main__":
    asyncio.run(main())