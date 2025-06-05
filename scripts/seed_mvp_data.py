#!/usr/bin/env python
"""Enhanced seed script for MVP demo.

Creates a more realistic demo environment with:
- Multiple users with different roles
- Active and completed leagues
- Real WNBA players with stats
- Draft history
- Game scores and team performance

Run with:
    poetry run python scripts/seed_mvp_data.py [--force]
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text

from app import models
from app.core.database import DB_PATH, SessionLocal, init_db
from app.core.security import hash_password


def create_demo_users(db) -> list[models.User]:
    """Create demo users with different personas."""
    users_data = [
        # Admin user
        {"email": "me@grantharris.tech", "password": "Thisisapassword1", "is_admin": True},
        # Regular demo users
        {"email": "demo@example.com", "password": "demo123", "is_admin": False},
        {"email": "alice@example.com", "password": "alice123", "is_admin": False},
        {"email": "bob@example.com", "password": "bob123", "is_admin": False},
        {"email": "charlie@example.com", "password": "charlie123", "is_admin": False},
        {"email": "diana@example.com", "password": "diana123", "is_admin": False},
        {"email": "eve@example.com", "password": "eve123", "is_admin": False},
        {"email": "frank@example.com", "password": "frank123", "is_admin": False},
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


def create_demo_players(db) -> list[models.Player]:
    """Create real WNBA players with realistic stats."""
    # Top WNBA players with realistic attributes
    players_data = [
        # Guards
        {"full_name": "Sabrina Ionescu", "position": "G", "team_abbr": "NY", "jersey_number": "20"},
        {"full_name": "Jewell Loyd", "position": "G", "team_abbr": "SEA", "jersey_number": "24"},
        {"full_name": "Kelsey Plum", "position": "G", "team_abbr": "LV", "jersey_number": "10"},
        {"full_name": "Diana Taurasi", "position": "G", "team_abbr": "PHX", "jersey_number": "3"},
        {"full_name": "Courtney Williams", "position": "G", "team_abbr": "CHI", "jersey_number": "10"},
        {"full_name": "Arike Ogunbowale", "position": "G", "team_abbr": "DAL", "jersey_number": "24"},
        {"full_name": "Jackie Young", "position": "G", "team_abbr": "LV", "jersey_number": "0"},
        {"full_name": "Skylar Diggins-Smith", "position": "G", "team_abbr": "SEA", "jersey_number": "4"},
        
        # Forwards  
        {"full_name": "A'ja Wilson", "position": "F", "team_abbr": "LV", "jersey_number": "22"},
        {"full_name": "Breanna Stewart", "position": "F", "team_abbr": "NY", "jersey_number": "30"},
        {"full_name": "Nneka Ogwumike", "position": "F", "team_abbr": "SEA", "jersey_number": "30"},
        {"full_name": "Alyssa Thomas", "position": "F", "team_abbr": "CONN", "jersey_number": "25"},
        {"full_name": "Napheesa Collier", "position": "F", "team_abbr": "MIN", "jersey_number": "24"},
        {"full_name": "Candace Parker", "position": "F", "team_abbr": "LV", "jersey_number": "3"},
        {"full_name": "Kahleah Copper", "position": "F", "team_abbr": "CHI", "jersey_number": "2"},
        {"full_name": "DeWanna Bonner", "position": "F", "team_abbr": "CONN", "jersey_number": "24"},
        
        # Centers
        {"full_name": "Brittney Griner", "position": "C", "team_abbr": "PHX", "jersey_number": "42"},
        {"full_name": "Jonquel Jones", "position": "C", "team_abbr": "NY", "jersey_number": "35"},
        {"full_name": "Sylvia Fowles", "position": "C", "team_abbr": "MIN", "jersey_number": "34"},
        {"full_name": "Tina Charles", "position": "C", "team_abbr": "SEA", "jersey_number": "31"},
        
        # Additional players for depth
        {"full_name": "Rhyne Howard", "position": "G", "team_abbr": "ATL", "jersey_number": "10"},
        {"full_name": "Marina Mabrey", "position": "G", "team_abbr": "CONN", "jersey_number": "13"},
        {"full_name": "Allisha Gray", "position": "G", "team_abbr": "ATL", "jersey_number": "15"},
        {"full_name": "Betnijah Laney", "position": "G", "team_abbr": "NY", "jersey_number": "44"},
        {"full_name": "Dearica Hamby", "position": "F", "team_abbr": "LA", "jersey_number": "5"},
        {"full_name": "Satou Sabally", "position": "F", "team_abbr": "DAL", "jersey_number": "0"},
        {"full_name": "Monique Billings", "position": "F", "team_abbr": "ATL", "jersey_number": "25"},
        {"full_name": "Brionna Jones", "position": "C", "team_abbr": "CONN", "jersey_number": "42"},
        {"full_name": "Azura Stevens", "position": "C", "team_abbr": "LA", "jersey_number": "23"},
        {"full_name": "Teaira McCowan", "position": "C", "team_abbr": "DAL", "jersey_number": "7"},
    ]
    
    players = []
    for i, data in enumerate(players_data, start=1):
        # Check if player already exists
        existing = db.query(models.Player).filter_by(full_name=data["full_name"]).first()
        if existing:
            players.append(existing)
        else:
            player = models.Player(
                id=i,
                full_name=data["full_name"],
                position=data["position"],
                team_abbr=data["team_abbr"],
                jersey_number=data["jersey_number"],
                status="active"
            )
            db.add(player)
            players.append(player)
    
    db.flush()
    return players


def create_demo_leagues(db, users) -> list[models.League]:
    """Create demo leagues in different states."""
    leagues = []
    
    # Active league ready for draft
    league1 = models.League(
        name="Championship League 2025",
        invite_code="CHAMP-2025",
        commissioner=users[0],  # Admin user
        max_teams=8,
        draft_date=datetime.now(timezone.utc) + timedelta(hours=2),
        settings={
            "draft_type": "snake",
            "scoring_type": "h2h",
            "min_teams": 4,
            "draft_rounds": 12,
            "seconds_per_pick": 90,
            "season_year": 2025
        }
    )
    db.add(league1)
    leagues.append(league1)
    
    # League currently drafting
    league2 = models.League(
        name="Elite Fantasy League",
        invite_code="ELITE-2025",
        commissioner=users[2],  # Alice
        max_teams=6,
        draft_date=datetime.now(timezone.utc) - timedelta(minutes=30),
        settings={
            "draft_type": "snake",
            "scoring_type": "roto",
            "min_teams": 4,
            "draft_rounds": 10,
            "seconds_per_pick": 60,
            "season_year": 2025
        }
    )
    db.add(league2)
    leagues.append(league2)
    
    # Completed league with history
    league3 = models.League(
        name="Legends League 2024",
        invite_code="LEGEND-2024",
        commissioner=users[3],  # Bob
        max_teams=8,
        draft_date=datetime.now(timezone.utc) - timedelta(days=90),
        settings={
            "draft_type": "auction",
            "scoring_type": "h2h",
            "min_teams": 6,
            "draft_rounds": 12,
            "seconds_per_pick": 120,
            "season_year": 2024
        }
    )
    db.add(league3)
    leagues.append(league3)
    
    db.flush()
    return leagues


def create_teams_and_rosters(db, leagues, users, players):
    """Create teams and assign players to rosters."""
    teams = []
    
    # Championship League teams
    team_names = ["Sky Hoopers", "Court Queens", "Rim Rockers", "Net Ninjas", 
                  "Ball Hawks", "Dunk Dynasty", "Triple Threats", "Fast Breakers"]
    
    for i, (user, team_name) in enumerate(zip(users[:8], team_names)):
        team = models.Team(
            name=team_name,
            owner=user,
            league=leagues[0]
        )
        db.add(team)
        teams.append(team)
    
    # Elite League teams
    elite_names = ["Elite Squad", "Dream Team", "All Stars", "Champions", "Warriors", "Phoenix"]
    for i, (user, team_name) in enumerate(zip(users[2:8], elite_names)):
        team = models.Team(
            name=team_name,
            owner=user,
            league=leagues[1]
        )
        db.add(team)
        teams.append(team)
    
    db.flush()
    
    # Assign players to teams in Elite League (currently drafting)
    # Simulate a partial draft
    draft_teams = [t for t in teams if t.league_id == leagues[1].id]
    available_players = players.copy()
    random.shuffle(available_players)
    
    # Each team gets 3-4 players (partial draft)
    for round_num in range(4):
        for team in draft_teams:
            if available_players:
                player = available_players.pop(0)
                roster_slot = models.RosterSlot(
                    team=team,
                    player=player,
                    is_starter=round_num < 3  # First 2 rounds are starters
                )
                db.add(roster_slot)
    
    # Create draft state for drafting league
    draft_order = []
    # Snake draft order - alternate each round
    for round_num in range(1, 11):  # 10 rounds
        if round_num % 2 == 1:  # Odd rounds
            draft_order.extend([t.id for t in draft_teams])
        else:  # Even rounds - reverse
            draft_order.extend([t.id for t in reversed(draft_teams)])
    
    draft_state = models.DraftState(
        league=leagues[1],
        current_round=5,
        current_pick_index=24,  # 4 rounds * 6 teams = 24 picks done
        status="active",
        pick_order=",".join(map(str, draft_order))
    )
    db.add(draft_state)
    
    db.flush()
    return teams


def create_sample_stats(db, players, teams):
    """Create sample game stats for players."""
    # Create some recent games
    game_dates = [datetime.now(timezone.utc) - timedelta(days=d) for d in range(1, 8)]
    
    # WNBA team abbreviations for games
    wnba_teams = ["NY", "LA", "CHI", "PHX", "SEA", "LV", "CONN", "ATL", "MIN", "DAL", "IND", "WSH"]
    
    for date in game_dates:
        # Create 4-6 games per day
        num_games = random.randint(4, 6)
        for game_num in range(num_games):
            # Pick two teams for the game
            home_team, away_team = random.sample(wnba_teams, 2)
            game_id = f"{date.strftime('%Y%m%d')}-{home_team}-{away_team}"
            
            # Create the game
            game = models.Game(
                id=game_id,
                date=date,
                home_team=home_team,
                away_team=away_team,
                home_score=random.randint(65, 95),
                away_score=random.randint(65, 95),
                status="Final",
                season=date.year
            )
            db.add(game)
            
            # Pick 8-10 random players for this game
            game_players = random.sample(players, k=random.randint(8, 10))
            
            for player in game_players:
                # Generate realistic stats based on position
                if player.position == "G":
                    points = random.randint(8, 25)
                    rebounds = random.randint(2, 6)
                    assists = random.randint(3, 9)
                    steals = random.randint(0, 3)
                    blocks = random.randint(0, 1)
                elif player.position == "F":
                    points = random.randint(10, 22)
                    rebounds = random.randint(5, 10)
                    assists = random.randint(1, 5)
                    steals = random.randint(0, 2)
                    blocks = random.randint(0, 2)
                else:  # Center
                    points = random.randint(8, 18)
                    rebounds = random.randint(6, 12)
                    assists = random.randint(0, 3)
                    steals = random.randint(0, 1)
                    blocks = random.randint(1, 4)
                
                # Calculate other stats
                fgm = points // 2
                fga = fgm + random.randint(2, 6)
                ftm = random.randint(0, 6)
                fta = ftm + random.randint(0, 2)
                three_pm = random.randint(0, min(4, points // 3))
                three_pa = three_pm + random.randint(0, 3)
                
                stat_line = models.StatLine(
                    player_id=player.id,
                    game_id=game_id,
                    game_date=date,
                    minutes_played=random.randint(20, 35),
                    points=points,
                    rebounds=rebounds,
                    assists=assists,
                    steals=steals,
                    blocks=blocks,
                    turnovers=random.randint(0, 4),
                    field_goals_made=fgm,
                    field_goals_attempted=fga,
                    three_pointers_made=three_pm,
                    three_pointers_attempted=three_pa,
                    free_throws_made=ftm,
                    free_throws_attempted=fta,
                    personal_fouls=random.randint(0, 4),
                    is_starter=random.choice([True, True, True, False])  # 75% starters
                )
                db.add(stat_line)
    
    db.flush()


def create_league_settings(db, leagues):
    """Update league settings with scoring and roster configuration."""
    for league in leagues:
        # Update settings with scoring configuration
        league.settings = league.settings or {}
        
        league.settings.update({
            "scoring": {
                "points": 1.0,
                "rebounds": 1.2,
                "assists": 1.5,
                "steals": 3.0,
                "blocks": 3.0,
                "turnovers": -1.0,
                "field_goals_made": 0.5,
                "field_goals_missed": -0.5,
                "free_throws_made": 1.0,
                "free_throws_missed": -0.5,
                "three_pointers_made": 1.0,
                "double_double_bonus": 5.0,
                "triple_double_bonus": 10.0
            },
            "roster": {
                "roster_size": league.settings.get("draft_rounds", 12),
                "starting_lineup": {
                    "G": 2,
                    "F": 2,
                    "C": 1,
                    "UTIL": 2
                },
                "bench_size": league.settings.get("draft_rounds", 12) - 7,
                "ir_slots": 1
            }
        })
    
    db.flush()


def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Seed the database with MVP demo data.")
    parser.add_argument("--force", action="store_true", help="Force recreation of demo data")
    args = parser.parse_args()

    print(f"Using database: sqlite:///{DB_PATH}")
    print("Creating comprehensive MVP demo data...")

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
            # Clear all tables in correct order
            db.execute(text("DELETE FROM stat_line"))
            db.execute(text("DELETE FROM roster_slot"))
            db.execute(text("DELETE FROM draft_pick"))
            db.execute(text("DELETE FROM draft_state"))
            db.execute(text("DELETE FROM team_score"))
            db.execute(text("DELETE FROM team"))
            db.execute(text("DELETE FROM league"))
            db.execute(text("DELETE FROM player"))
            db.execute(text("DELETE FROM user"))
            db.commit()

        # Create demo data
        print("1. Creating users...")
        users = create_demo_users(db)
        print(f"   Created {len(users)} users")

        print("2. Creating WNBA players...")
        players = create_demo_players(db)
        print(f"   Created {len(players)} players")

        print("3. Creating leagues...")
        leagues = create_demo_leagues(db, users)
        print(f"   Created {len(leagues)} leagues")

        print("4. Creating teams and rosters...")
        teams = create_teams_and_rosters(db, leagues, users, players)
        print(f"   Created {len(teams)} teams")

        print("5. Creating sample stats...")
        create_sample_stats(db, players, teams)
        print("   Created game stats for the past week")

        print("6. Configuring league settings...")
        create_league_settings(db, leagues)
        print("   Configured scoring and roster settings")

        # Commit all changes
        db.commit()

        print("\n✅ MVP demo data created successfully!")
        print("\nDemo Users:")
        print("- Admin: me@grantharris.tech / Thisisapassword1")
        print("- Demo User: demo@example.com / demo123")
        print("- Other Users: alice/bob/charlie/diana/eve/frank@example.com / {name}123")
        print("\nLeagues:")
        print("- Championship League 2025: Ready to draft in 2 hours")
        print("- Elite Fantasy League: Currently drafting (round 5)")
        print("- Legends League 2024: Completed season with history")

    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()