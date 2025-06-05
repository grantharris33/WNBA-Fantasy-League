#!/usr/bin/env python
"""MVP seed script using real WNBA data from RapidAPI.

Creates demo data with:
- Real WNBA teams and players
- Recent game data and stats
- Demo users and fantasy leagues

Run with:
    poetry run python scripts/seed_mvp_real_data.py [--force]
"""
from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

from sqlalchemy import text

from app import models
from app.core.database import DB_PATH, SessionLocal, init_db
from app.core.security import hash_password
from app.external_apis.rapidapi_client import wnba_client
from app.services.wnba import WNBAService


def create_demo_users(db) -> list[models.User]:
    """Create demo users."""
    users_data = [
        # Admin user
        {"email": "me@grantharris.tech", "password": "Thisisapassword1", "is_admin": True},
        # Regular demo users
        {"email": "demo@example.com", "password": "demo123", "is_admin": False},
        {"email": "alice@example.com", "password": "alice123", "is_admin": False},
        {"email": "bob@example.com", "password": "bob123", "is_admin": False},
        {"email": "charlie@example.com", "password": "charlie123", "is_admin": False},
    ]
    
    users = []
    for data in users_data:
        # Check if user already exists
        existing = db.query(models.User).filter_by(email=data["email"]).first()
        if existing:
            users.append(existing)
        else:
            user = models.User(
                email=data["email"],
                hashed_password=hash_password(data["password"]),
                is_admin=data["is_admin"]
            )
            db.add(user)
            users.append(user)
    
    db.flush()
    return users


def create_demo_leagues(db, users) -> list[models.League]:
    """Create demo fantasy leagues."""
    leagues = []
    
    # Active league
    league1 = models.League(
        name="MVP Demo League 2025",
        invite_code="MVP-DEMO",
        commissioner=users[0],  # Admin
        max_teams=6,
        draft_date=datetime.now(timezone.utc) + timedelta(hours=2),
        settings={
            "draft_type": "snake",
            "scoring_type": "h2h",
            "min_teams": 4,
            "draft_rounds": 10,
            "seconds_per_pick": 90,
            "season_year": 2025
        }
    )
    db.add(league1)
    leagues.append(league1)
    
    # Another league
    league2 = models.League(
        name="Test League 2024",
        invite_code="TEST-2024",
        commissioner=users[1],  # demo user
        max_teams=4,
        draft_date=datetime.now(timezone.utc) - timedelta(days=30),
        settings={
            "draft_type": "snake",
            "scoring_type": "roto",
            "min_teams": 3,
            "draft_rounds": 8,
            "seconds_per_pick": 60,
            "season_year": 2024
        }
    )
    db.add(league2)
    leagues.append(league2)
    
    db.flush()
    return leagues


def create_teams(db, leagues, users) -> list[models.Team]:
    """Create fantasy teams."""
    teams = []
    team_names = ["Warriors", "Dynasty", "All-Stars", "Champions", "Legends"]
    
    # Teams for league 1
    for i, (user, team_name) in enumerate(zip(users[:5], team_names)):
        team = models.Team(
            name=team_name,
            owner=user,
            league=leagues[0]
        )
        db.add(team)
        teams.append(team)
    
    # Teams for league 2
    for user, team_name in zip(users[1:4], ["Team Alpha", "Team Beta", "Team Gamma"]):
        team = models.Team(
            name=team_name,
            owner=user,
            league=leagues[1]
        )
        db.add(team)
        teams.append(team)
    
    db.flush()
    return teams


async def fetch_and_store_wnba_data(db, year: int) -> Dict[str, Any]:
    """Fetch real WNBA data from RapidAPI."""
    print(f"Fetching WNBA data for {year}...")
    
    # Check if API key is configured
    api_key = os.getenv("RAPIDAPI_KEY") or os.getenv("WNBA_API_KEY")
    if not api_key:
        print("⚠️  No RapidAPI key found. Skipping real data import.")
        print("   Set RAPIDAPI_KEY in your .env file to enable real WNBA data.")
        return {"teams": 0, "players": 0, "games": 0}
    
    wnba_service = WNBAService(db)
    stats = {"teams": 0, "players": 0, "games": 0}
    
    try:
        # Fetch and store teams
        print("  Fetching teams...")
        teams_data = await wnba_client.fetch_all_teams()
        if teams_data:
            for team_data in teams_data:
                if isinstance(team_data, dict):
                    existing = db.query(models.WNBATeam).filter_by(id=team_data.get("id")).first()
                    if not existing:
                        team = models.WNBATeam(
                            id=team_data.get("id"),
                            name=team_data.get("name", "Unknown"),
                            abbreviation=team_data.get("abbreviation", "UNK"),
                            city=team_data.get("city", ""),
                            logo_url=team_data.get("logo", "")
                        )
                        db.add(team)
                        stats["teams"] += 1
        
        # Fetch standings to get current teams
        print(f"  Fetching {year} standings...")
        standings_data = await wnba_client.fetch_standings(str(year))
        
        # Process each team's roster
        team_ids = []
        if isinstance(standings_data, dict):
            for conf_data in standings_data.values():
                if isinstance(conf_data, list):
                    for team_info in conf_data:
                        if isinstance(team_info, dict) and "teamId" in team_info:
                            team_ids.append(str(team_info["teamId"]))
        
        # Fetch rosters for each team
        print(f"  Fetching rosters for {len(team_ids)} teams...")
        for team_id in team_ids[:12]:  # Limit to 12 teams for MVP
            try:
                roster_data = await wnba_client.fetch_team_roster(team_id)
                if roster_data and isinstance(roster_data, dict):
                    for player_data in roster_data.get("roster", []):
                        if isinstance(player_data, dict):
                            player_id = player_data.get("playerId")
                            if player_id:
                                existing = db.query(models.Player).filter_by(id=player_id).first()
                                if not existing:
                                    player = models.Player(
                                        id=player_id,
                                        full_name=player_data.get("longName", "Unknown"),
                                        first_name=player_data.get("firstName", ""),
                                        last_name=player_data.get("lastName", ""),
                                        position=player_data.get("pos", ""),
                                        jersey_number=player_data.get("jersey", ""),
                                        height=player_data.get("height"),
                                        weight=player_data.get("weight"),
                                        birth_date=None,  # Would need to parse from API
                                        college=player_data.get("college", ""),
                                        years_pro=player_data.get("exp", 0),
                                        status="active",
                                        headshot_url=player_data.get("headshot", ""),
                                        team_abbr=player_data.get("team", "")
                                    )
                                    db.add(player)
                                    stats["players"] += 1
            except Exception as e:
                print(f"    Error fetching roster for team {team_id}: {e}")
                continue
        
        # Fetch recent games and stats
        print("  Fetching recent games...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)  # Last 2 weeks
        
        current = start_date
        while current <= end_date:
            try:
                schedule = await wnba_client.fetch_schedule(
                    str(current.year),
                    f"{current.month:02d}",
                    f"{current.day:02d}"
                )
                
                for game_info in schedule:
                    if isinstance(game_info, dict):
                        game_id = game_info.get("gameId")
                        if game_id and game_info.get("gameStatus") == "Final":
                            # Store game
                            existing_game = db.query(models.Game).filter_by(id=game_id).first()
                            if not existing_game:
                                game = models.Game(
                                    id=game_id,
                                    date=current,
                                    home_team_id=game_info.get("homeTeam", {}).get("teamId"),
                                    away_team_id=game_info.get("awayTeam", {}).get("teamId"),
                                    home_score=game_info.get("homeTeam", {}).get("score", 0),
                                    away_score=game_info.get("awayTeam", {}).get("score", 0),
                                    status="Final"
                                )
                                db.add(game)
                                stats["games"] += 1
                                
                                # Fetch box score for player stats
                                try:
                                    box_score = await wnba_client.fetch_box_score(game_id)
                                    await wnba_service._process_box_score(game_id, box_score)
                                except Exception as e:
                                    print(f"    Error fetching box score for game {game_id}: {e}")
                
            except Exception as e:
                print(f"    Error fetching schedule for {current.date()}: {e}")
            
            current += timedelta(days=1)
        
        db.commit()
        
    except Exception as e:
        print(f"  Error fetching WNBA data: {e}")
        db.rollback()
    finally:
        await wnba_client.close()
    
    return stats


def assign_players_to_teams(db, teams: List[models.Team]) -> None:
    """Assign some players to fantasy teams for demo purposes."""
    # Get available players
    players = db.query(models.Player).filter_by(status="active").limit(50).all()
    
    if not players:
        print("  No players available to assign to teams")
        return
    
    # Assign players to first 3 teams in league 1
    player_idx = 0
    for team in teams[:3]:
        for i in range(7):  # 7 players per team
            if player_idx >= len(players):
                break
            
            roster_slot = models.RosterSlot(
                team=team,
                player=players[player_idx],
                is_starter=(i < 5)  # First 5 are starters
            )
            db.add(roster_slot)
            player_idx += 1
    
    db.commit()


async def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Seed the database with MVP demo data using real WNBA data.")
    parser.add_argument("--force", action="store_true", help="Force recreation of demo data")
    parser.add_argument("--year", type=int, default=2024, help="Year to fetch WNBA data for")
    args = parser.parse_args()

    print(f"Using database: sqlite:///{DB_PATH}")
    print("Creating MVP demo data with real WNBA data...")

    # Initialize database schema
    init_db()

    # Create session
    db = SessionLocal()

    try:
        # Check for existing data
        user_count = db.query(models.User).count()

        # If data already seeded and not forcing, skip
        if not args.force and user_count > 0:
            print("Demo data already exists. Skipping. (Use --force to recreate)")
            return

        # Clean existing data if force is set
        if args.force and user_count > 0:
            print("Cleaning existing data...")
            # Clear tables in correct order
            db.execute(text("DELETE FROM stat_line"))
            db.execute(text("DELETE FROM game"))
            db.execute(text("DELETE FROM roster_slot"))
            db.execute(text("DELETE FROM team"))
            db.execute(text("DELETE FROM league"))
            db.execute(text("DELETE FROM player"))
            db.execute(text("DELETE FROM wnba_team"))
            db.execute(text("DELETE FROM user"))
            db.commit()

        # Create demo data
        print("1. Creating users...")
        users = create_demo_users(db)
        print(f"   Created {len(users)} users")

        print("2. Creating leagues...")
        leagues = create_demo_leagues(db, users)
        print(f"   Created {len(leagues)} leagues")

        print("3. Creating teams...")
        teams = create_teams(db, leagues, users)
        print(f"   Created {len(teams)} teams")

        print("4. Fetching real WNBA data...")
        stats = await fetch_and_store_wnba_data(db, args.year)
        print(f"   Imported {stats['teams']} teams, {stats['players']} players, {stats['games']} games")

        print("5. Assigning players to fantasy teams...")
        assign_players_to_teams(db, teams)
        print("   Assigned players to demo teams")

        # Commit all changes
        db.commit()

        print("\n✅ MVP demo data created successfully!")
        print("\nDemo Users:")
        print("- Admin: me@grantharris.tech / Thisisapassword1")
        print("- Demo: demo@example.com / demo123")
        print("- Others: alice/bob/charlie@example.com / {name}123")
        print("\nLeagues:")
        print("- MVP Demo League 2025 (6 teams max)")
        print("- Test League 2024 (4 teams max)")
        
        if stats["players"] > 0:
            print(f"\nReal WNBA Data:")
            print(f"- {stats['teams']} teams")
            print(f"- {stats['players']} players") 
            print(f"- {stats['games']} games with stats")
        else:
            print("\n⚠️  No real WNBA data imported (API key not configured)")

    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())