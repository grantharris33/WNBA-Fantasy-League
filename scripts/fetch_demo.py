#!/usr/bin/env python3
"""PoC script for FANTASY-1 — fetches WNBA box-scores via RapidAPI.

Usage:
    python scripts/fetch_demo.py 2025-05-04
If no date argument is provided the script defaults to yesterday (UTC).

Requires:
    export RAPIDAPI_KEY="xxxx"
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from typing import Any, Dict, List

import requests

BASE_URL = "https://wnba-api.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", "demo-key-please-set"),
    "X-RapidAPI-Host": "wnba-api.p.rapidapi.com",
}


def fetch_schedule(date_iso: str) -> List[Dict[str, Any]]:
    """Call /wnbaschedule using year / month / day query params."""
    date_obj = dt.datetime.strptime(date_iso, "%Y-%m-%d").date()
    params = {
        "year": date_obj.strftime("%Y"),
        "month": date_obj.strftime("%m"),
        "day": date_obj.strftime("%d"),
    }

    url = f"{BASE_URL}/wnbaschedule"
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    data = resp.json()

    date_key = date_obj.strftime("%Y%m%d")
    return data.get(date_key, [])


def fetch_boxscore(game_id: str) -> Dict[str, Any]:
    # Use the /wnbabox endpoint with gameId query parameter
    url = f"{BASE_URL}/wnbabox"
    resp = requests.get(url, headers=HEADERS, params={"gameId": game_id})
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = (dt.datetime.utcnow() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Fetching games for {date_str} …")
    games = fetch_schedule(date_str)
    if not games:
        print("No games found for that date.")
        sys.exit(0)

    game = games[0]
    game_id = game["id"]
    print(f"Found game {game_id} – {game['teams'][0]['displayName']} vs {game['teams'][1]['displayName']}")

    print("Fetching box-score …")
    boxscore = fetch_boxscore(game_id)


    for team in boxscore.get("players", []):
        for stat_block in team.get("statistics", []):
            for player in stat_block.get("athletes", []):
                name = player["athlete"]["displayName"]
                stats_array = player.get("stats", [])
                # The points are last element (see sample)
                pts = stats_array[-1] if stats_array else "—"
                print(f"{name:25}  PTS: {pts}")


if __name__ == "__main__":
    main()