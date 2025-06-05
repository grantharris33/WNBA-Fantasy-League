#!/usr/bin/env python3
"""
Demonstration of the automatic starter selection when a draft completes.

This script simulates a draft completion and shows how the first 5 players
that meet position requirements (>=2 Guards, >=1 Forward/Center) are
automatically set as starters for each team.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.models import Base, League, Player, RosterSlot, Team, User, DraftState, DraftPick
from app.services.draft import DraftService


def create_test_database():
    """Create an in-memory SQLite database for demonstration."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def setup_demo_data(db):
    """Set up demo league, teams, and players."""
    print("🏀 Setting up demo data...")

    # Create league
    league = League(name="Demo Fantasy League", invite_code="DEMO123")
    db.add(league)
    db.flush()

    # Create users
    users = [
        User(email="user1@demo.com", hashed_password="hash"),
        User(email="user2@demo.com", hashed_password="hash"),
        User(email="user3@demo.com", hashed_password="hash"),
        User(email="user4@demo.com", hashed_password="hash"),
    ]
    db.add_all(users)
    db.flush()

    # Create teams
    teams = [
        Team(name="Thunder Bolts", owner_id=users[0].id, league_id=league.id),
        Team(name="Lightning Strikes", owner_id=users[1].id, league_id=league.id),
        Team(name="Storm Chasers", owner_id=users[2].id, league_id=league.id),
        Team(name="Wind Runners", owner_id=users[3].id, league_id=league.id),
    ]
    db.add_all(teams)
    db.flush()

    # Create diverse player pool with clear position distribution
    players = [
        # Guards (20 total)
        *[Player(full_name=f"Star Guard {i}", position="G", team_abbr="ATL") for i in range(1, 21)],
        # Forwards (10 total)
        *[Player(full_name=f"Power Forward {i}", position="F", team_abbr="LAS") for i in range(1, 11)],
        # Centers (6 total)
        *[Player(full_name=f"Center {i}", position="C", team_abbr="NYL") for i in range(1, 7)],
        # Multi-position players (4 total)
        Player(full_name="Versatile Player 1", position="G-F", team_abbr="SEA"),
        Player(full_name="Versatile Player 2", position="F-C", team_abbr="CHI"),
        Player(full_name="Combo Guard", position="G-F", team_abbr="MIN"),
        Player(full_name="Twin Tower", position="F-C", team_abbr="CON"),
    ]
    db.add_all(players)
    db.flush()

    # Create draft state
    pick_order = ",".join([str(t.id) for t in teams] + [str(t.id) for t in reversed(teams)])
    draft = DraftState(
        league_id=league.id,
        current_round=1,
        current_pick_index=0,
        status="active",
        pick_order=pick_order
    )
    db.add(draft)
    db.flush()

    return league, teams, players, draft


def simulate_draft(db, draft, teams, players):
    """Simulate a complete 10-round draft."""
    print("\n📝 Simulating 10-round draft (4 teams, 40 total picks)...")

    pick_number = 1

    # Draft 10 rounds
    for round_num in range(1, 11):
        print(f"   Round {round_num}:", end=" ")

        for team_index in range(len(teams)):
            # Snake draft: odd rounds forward, even rounds backward
            if round_num % 2 == 1:
                team = teams[team_index]
            else:
                team = teams[len(teams) - 1 - team_index]

            player = players[pick_number - 1]

            # Create draft pick
            pick = DraftPick(
                draft_id=draft.id,
                team_id=team.id,
                player_id=player.id,
                round=round_num,
                pick_number=pick_number,
                is_auto=False
            )

            # Create roster slot (no starters initially)
            roster_slot = RosterSlot(
                team_id=team.id,
                player_id=player.id,
                position=player.position,
                is_starter=False
            )

            db.add(pick)
            db.add(roster_slot)

            print(f"{team.name[:12]} picks {player.full_name} ({player.position})", end=" | ")
            pick_number += 1

        print()  # New line after each round

    # Complete the draft
    draft.status = "completed"
    draft.current_round = 11
    db.commit()

    print(f"\n✅ Draft completed! {pick_number - 1} total picks made.")


def show_rosters_before_auto_starters(db, teams):
    """Show team rosters before auto-starter selection."""
    print("\n📋 Team Rosters BEFORE Auto-Starter Selection:")
    print("=" * 80)

    for team in teams:
        roster_slots = (
            db.query(RosterSlot)
            .join(Player, RosterSlot.player_id == Player.id)
            .filter(RosterSlot.team_id == team.id)
            .order_by(RosterSlot.id)
            .all()
        )

        print(f"\n🏀 {team.name}")
        print("-" * 40)

        for i, slot in enumerate(roster_slots, 1):
            player = db.query(Player).filter(Player.id == slot.player_id).first()
            starter_status = "STARTER" if slot.is_starter else "BENCH"
            print(f"  {i:2d}. {player.full_name:<20} ({player.position:>3}) - {starter_status}")

        # Show position counts
        positions = [
            db.query(Player).filter(Player.id == slot.player_id).first().position
            for slot in roster_slots
        ]
        guard_count = sum(1 for pos in positions if pos and 'G' in pos)
        forward_center_count = sum(1 for pos in positions if pos and ('F' in pos or 'C' in pos))

        print(f"     Position Summary: {guard_count} Guards, {forward_center_count} Forwards/Centers")


def apply_auto_starters(db, league_id):
    """Apply automatic starter selection."""
    print("\n🤖 Applying automatic starter selection...")

    draft_service = DraftService(db)
    draft_service._set_initial_starters_for_all_teams(league_id)

    print("✅ Auto-starter selection completed!")


def show_rosters_after_auto_starters(db, teams):
    """Show team rosters after auto-starter selection."""
    print("\n📋 Team Rosters AFTER Auto-Starter Selection:")
    print("=" * 80)

    for team in teams:
        roster_slots = (
            db.query(RosterSlot)
            .join(Player, RosterSlot.player_id == Player.id)
            .filter(RosterSlot.team_id == team.id)
            .order_by(RosterSlot.id)
            .all()
        )

        print(f"\n🏀 {team.name}")
        print("-" * 40)

        starters = []
        bench = []

        for slot in roster_slots:
            player = db.query(Player).filter(Player.id == slot.player_id).first()
            if slot.is_starter:
                starters.append((player, slot))
            else:
                bench.append((player, slot))

        print("  STARTERS:")
        for i, (player, slot) in enumerate(starters, 1):
            print(f"    {i}. {player.full_name:<20} ({player.position:>3})")

        print("  BENCH:")
        for i, (player, slot) in enumerate(bench, 1):
            print(f"    {i}. {player.full_name:<20} ({player.position:>3})")

        # Validate position requirements
        starter_positions = [player.position for player, _ in starters]
        guard_count = sum(1 for pos in starter_positions if pos and 'G' in pos)
        forward_center_count = sum(1 for pos in starter_positions if pos and ('F' in pos or 'C' in pos))

        valid = guard_count >= 2 and forward_center_count >= 1
        status = "✅ VALID" if valid else "❌ INVALID"
        print(f"     Starter Requirements: {guard_count} Guards (≥2), {forward_center_count} F/C (≥1) - {status}")


def main():
    """Run the demonstration."""
    print("🏀 WNBA Fantasy League: Auto-Starter Selection Demo")
    print("=" * 60)

    # Create database and setup data
    db = create_test_database()
    league, teams, players, draft = setup_demo_data(db)

    # Simulate complete draft
    simulate_draft(db, draft, teams, players)

    # Show rosters before auto-starters
    show_rosters_before_auto_starters(db, teams)

    # Apply auto-starter selection
    apply_auto_starters(db, league.id)

    # Show rosters after auto-starters
    show_rosters_after_auto_starters(db, teams)

    print("\n🎉 Demo completed!")
    print("\nKey Features Demonstrated:")
    print("• Automatic starter selection when draft completes")
    print("• Position requirement validation (≥2 Guards, ≥1 Forward/Center)")
    print("• Prioritization of early draft picks for starter positions")
    print("• Proper handling of multi-position players (G-F, F-C)")
    print("\nWith the new move counting system, teams can now use their 3 weekly")
    print("moves for strategic roster changes instead of just setting up a basic lineup!")


if __name__ == "__main__":
    main()