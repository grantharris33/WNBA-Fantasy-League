#!/usr/bin/env python3

from app.core.database import SessionLocal, init_db
from app.models import Player, WNBATeam


def check_data():
    init_db()
    db = SessionLocal()

    try:
        # Check WNBA teams
        teams_count = db.query(WNBATeam).count()
        print(f"WNBA Teams in database: {teams_count}")

        if teams_count > 0:
            team = db.query(WNBATeam).first()
            print(f"Sample team: {team.display_name} ({team.abbreviation})")

        # Check specific player
        player = db.query(Player).filter(Player.id == 2999101).first()
        if player:
            print(f"\nPlayer: {player.full_name}")
            print(f"Team abbr: {player.team_abbr}")
            print(f"WNBA team ID: {player.wnba_team_id}")
            print(f"Height: {player.height}")
            print(f"Weight: {player.weight}")
            print(f"College: {player.college}")
            print(f"Jersey: {player.jersey_number}")
            print(f"Position: {player.position}")
            print(f"Status: {player.status}")
        else:
            print("\nPlayer 2999101 not found")

        # Check a few players for team data
        players_with_teams = db.query(Player).filter(Player.team_abbr.isnot(None)).limit(5).all()
        print(f"\nPlayers with team_abbr: {len(players_with_teams)}")
        for p in players_with_teams:
            print(f"  {p.full_name}: {p.team_abbr}")

    finally:
        db.close()


if __name__ == "__main__":
    check_data()
