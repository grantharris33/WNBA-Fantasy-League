import pytest
from datetime import datetime
from freezegun import freeze_time
from sqlalchemy.orm import Session

from app.models import Player, RosterSlot, Team, User, League
from app.services.roster import RosterService


@pytest.fixture
def setup_roster_test(db: Session):
    # Create a test league
    league = League(name="Test League")
    db.add(league)
    db.flush()

    # Create test users
    user1 = User(email="user1@example.com", hashed_password="hashed_password")
    db.add(user1)
    db.flush()

    # Create test teams
    team1 = Team(name="Team 1", owner_id=user1.id, league_id=league.id)
    db.add(team1)
    db.flush()

    # Create test players with positions
    players = [
        Player(full_name="Guard 1", position="G", team_abbr="TST"),
        Player(full_name="Guard 2", position="G", team_abbr="TST"),
        Player(full_name="Forward 1", position="F", team_abbr="TST"),
        Player(full_name="Forward 2", position="F", team_abbr="TST"),
        Player(full_name="Center 1", position="C", team_abbr="TST"),
        Player(full_name="Forward-Center 1", position="F-C", team_abbr="TST"),
        Player(full_name="Guard-Forward 1", position="G-F", team_abbr="TST"),
        Player(full_name="Bench 1", position="G", team_abbr="TST"),
        Player(full_name="Bench 2", position="F", team_abbr="TST"),
        Player(full_name="Bench 3", position="C", team_abbr="TST"),
        Player(full_name="Free Agent 1", position="G", team_abbr="TST"),
        Player(full_name="Free Agent 2", position="F", team_abbr="TST"),
    ]
    db.add_all(players)
    db.flush()

    # Add 7 players to team1's roster (5 starters, 2 bench)
    roster_slots = [
        RosterSlot(team_id=team1.id, player_id=players[0].id, position="G", is_starter=True),
        RosterSlot(team_id=team1.id, player_id=players[1].id, position="G", is_starter=True),
        RosterSlot(team_id=team1.id, player_id=players[2].id, position="F", is_starter=True),
        RosterSlot(team_id=team1.id, player_id=players[3].id, position="F", is_starter=True),
        RosterSlot(team_id=team1.id, player_id=players[4].id, position="C", is_starter=True),
        RosterSlot(team_id=team1.id, player_id=players[7].id, position="G", is_starter=False),
        RosterSlot(team_id=team1.id, player_id=players[8].id, position="F", is_starter=False),
    ]
    db.add_all(roster_slots)
    db.commit()

    return {
        "league": league,
        "user": user1,
        "team": team1,
        "players": players,
    }


def test_get_free_agents(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    league_id = setup_roster_test["league"].id

    # Act
    free_agents = service.get_free_agents(league_id)

    # Assert
    assert len(free_agents) == 5  # 12 players total - 7 on roster
    assert any(p.full_name == "Free Agent 1" for p in free_agents)
    assert any(p.full_name == "Free Agent 2" for p in free_agents)


def test_add_player_to_team(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]
    players = setup_roster_test["players"]
    free_agent = players[10]  # Free Agent 1

    # Act
    roster_slot = service.add_player_to_team(team.id, free_agent.id)

    # Assert
    assert roster_slot is not None
    assert roster_slot.team_id == team.id
    assert roster_slot.player_id == free_agent.id
    assert roster_slot.is_starter == False

    # Verify player is now on the roster
    team_players = db.query(RosterSlot).filter(RosterSlot.team_id == team.id).all()
    assert len(team_players) == 8  # 7 original + 1 new

    # The move counter should not increment since the player is not set as a starter
    team_db = db.query(Team).filter_by(id=team.id).first()
    assert team_db.moves_this_week == 0


def test_add_player_as_starter_increments_move_counter(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]
    players = setup_roster_test["players"]
    free_agent = players[10]  # Free Agent 1

    # Act
    roster_slot = service.add_player_to_team(team.id, free_agent.id, set_as_starter=True)

    # Assert
    assert roster_slot.is_starter == True

    # The move counter should increment since the player is set as a starter
    team_db = db.query(Team).filter_by(id=team.id).first()
    assert team_db.moves_this_week == 1


def test_drop_player_from_team(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]
    players = setup_roster_test["players"]
    player_to_drop = players[7]  # Bench 1

    # Act
    service.drop_player_from_team(team.id, player_to_drop.id)

    # Assert
    # Verify player is no longer on the roster
    team_players = db.query(RosterSlot).filter(RosterSlot.team_id == team.id).all()
    assert len(team_players) == 6  # 7 original - 1 dropped

    roster_slot = db.query(RosterSlot).filter(
        RosterSlot.team_id == team.id,
        RosterSlot.player_id == player_to_drop.id
    ).first()
    assert roster_slot is None


def test_set_starters_valid_lineup(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]
    players = setup_roster_test["players"]

    # Change one starter to a bench player
    new_starters = [
        players[0].id,  # Guard 1
        players[1].id,  # Guard 2
        players[2].id,  # Forward 1
        players[8].id,  # Bench 2 (F) - This is a new starter
        players[4].id,  # Center 1
    ]

    # Act
    starters = service.set_starters(team.id, new_starters)

    # Assert
    assert len(starters) == 5
    starter_ids = [s.player_id for s in starters]
    assert players[8].id in starter_ids  # Bench 2 is now a starter
    assert players[3].id not in starter_ids  # Forward 2 is no longer a starter

    # Verify the moves counter increased by 1
    team_db = db.query(Team).filter_by(id=team.id).first()
    assert team_db.moves_this_week == 1


def test_set_starters_invalid_positions(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]
    players = setup_roster_test["players"]

    # First add all these players to the team to make sure they're on the roster
    for player_id in [players[2].id, players[3].id, players[5].id]:
        # Make sure this player is on the team's roster if not already
        if not db.query(RosterSlot).filter(
            RosterSlot.team_id == team.id,
            RosterSlot.player_id == player_id
        ).first():
            db.add(RosterSlot(
                team_id=team.id,
                player_id=player_id,
                position=next(p.position for p in players if p.id == player_id),
                is_starter=False
            ))
    db.commit()

    # Invalid lineup - only 1 guard
    invalid_starters = [
        players[0].id,  # Guard 1
        players[2].id,  # Forward 1
        players[3].id,  # Forward 2
        players[4].id,  # Center 1
        players[5].id,  # Forward-Center 1
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Starting lineup must include at least 2 players with Guard"):
        service.set_starters(team.id, invalid_starters)


def test_set_starters_move_limit_reached(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]
    players = setup_roster_test["players"]

    # Set the team's moves_this_week to the limit
    team.moves_this_week = 3
    db.commit()

    # Try to make a change to the starters
    new_starters = [
        players[0].id,  # Guard 1
        players[1].id,  # Guard 2
        players[2].id,  # Forward 1
        players[7].id,  # Bench 1 (G) - New starter
        players[4].id,  # Center 1
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Not enough moves left for the week"):
        service.set_starters(team.id, new_starters)


def test_reset_weekly_moves(db: Session, setup_roster_test):
    # Arrange
    service = RosterService(db)
    team = setup_roster_test["team"]

    # Set some moves
    team.moves_this_week = 2
    db.commit()

    # Act
    with freeze_time("2023-06-05 05:00:00"):  # Monday at reset time
        service.reset_weekly_moves()

    # Assert
    team_db = db.query(Team).filter_by(id=team.id).first()
    assert team_db.moves_this_week == 0