import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import hash_password
from app.main import app
from app.models import League, Player, RosterSlot, Team, User


@pytest.fixture
def auth_client(db):
    """
    Create a test client with a mocked authenticated user
    """

    # Replace the dependency with a mock to bypass authentication
    async def mock_get_current_user():
        return User(id=1, email="test@example.com", hashed_password="mock")

    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Set dependency overrides
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    # Create client
    client = TestClient(app)
    yield client

    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def setup_roster_test_data(db: Session):
    # Create a test league
    league = League(name="Test League")
    db.add(league)
    db.flush()

    # Create test user
    hashed_password = hash_password("password123")
    user = User(id=1, email="test@example.com", hashed_password=hashed_password)
    db.add(user)
    db.flush()

    # Create test team
    team = Team(name="Test Team", owner_id=user.id, league_id=league.id)
    db.add(team)
    db.flush()

    # Create test players
    players = []
    for i in range(12):
        position = "G" if i < 4 else "F" if i < 8 else "C"
        player = Player(full_name=f"Player {i+1}", position=position, team_abbr="TST")
        db.add(player)
        players.append(player)
    db.flush()

    # Add 7 players to the team (5 starters, 2 bench)
    roster_slots = [
        RosterSlot(team_id=team.id, player_id=players[0].id, position="G", is_starter=True),
        RosterSlot(team_id=team.id, player_id=players[1].id, position="G", is_starter=True),
        RosterSlot(team_id=team.id, player_id=players[4].id, position="F", is_starter=True),
        RosterSlot(team_id=team.id, player_id=players[5].id, position="F", is_starter=True),
        RosterSlot(team_id=team.id, player_id=players[8].id, position="C", is_starter=True),
        RosterSlot(team_id=team.id, player_id=players[2].id, position="G", is_starter=False),
        RosterSlot(team_id=team.id, player_id=players[6].id, position="F", is_starter=False),
    ]
    db.add_all(roster_slots)
    db.commit()

    return {"league": league, "user": user, "team": team, "players": players}


def test_list_free_agents(auth_client, setup_roster_test_data, db: Session):
    # Arrange
    league_id = setup_roster_test_data["league"].id

    # Act
    response = auth_client.get(f"/api/v1/leagues/{league_id}/free-agents")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5  # 12 players - 7 on roster
    assert len(data["items"]) == 5


def test_add_player(auth_client, setup_roster_test_data, db: Session):
    # Arrange
    team_id = setup_roster_test_data["team"].id
    free_agent_id = setup_roster_test_data["players"][10].id  # A player not on any roster

    # Act
    response = auth_client.post(
        f"/api/v1/teams/{team_id}/roster/add", json={"player_id": free_agent_id, "set_as_starter": False}
    )

    # Assert
    assert response.status_code == 200

    # Verify player is now on the roster
    roster_slot = (
        db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.player_id == free_agent_id).first()
    )
    assert roster_slot is not None
    assert roster_slot.is_starter == 0


def test_add_player_as_starter(auth_client, setup_roster_test_data, db: Session):
    # Arrange
    team_id = setup_roster_test_data["team"].id
    free_agent_id = setup_roster_test_data["players"][10].id  # A player not on any roster

    # Act
    response = auth_client.post(
        f"/api/v1/teams/{team_id}/roster/add", json={"player_id": free_agent_id, "set_as_starter": True}
    )

    # Assert
    assert response.status_code == 200

    # Verify player is now on the roster as a starter
    roster_slot = (
        db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.player_id == free_agent_id).first()
    )
    assert roster_slot is not None
    assert roster_slot.is_starter == 1

    # Verify the moves counter increased
    team = db.query(Team).filter_by(id=team_id).first()
    assert team.moves_this_week == 1


def test_drop_player(auth_client, setup_roster_test_data, db: Session):
    # Arrange
    team_id = setup_roster_test_data["team"].id
    player_to_drop_id = setup_roster_test_data["players"][2].id  # A bench player

    # Act
    response = auth_client.post(f"/api/v1/teams/{team_id}/roster/drop", json={"player_id": player_to_drop_id})

    # Assert
    assert response.status_code == 200

    # Verify player is no longer on the roster
    roster_slot = (
        db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.player_id == player_to_drop_id).first()
    )
    assert roster_slot is None


def test_set_starters(auth_client, setup_roster_test_data, db: Session):
    # Arrange
    team_id = setup_roster_test_data["team"].id
    players = setup_roster_test_data["players"]

    # New starters - replace one starter with a bench player
    new_starters = [
        players[0].id,  # Existing starter
        players[1].id,  # Existing starter
        players[4].id,  # Existing starter
        players[5].id,  # Existing starter
        players[2].id,  # Bench player -> Starter
    ]

    # Act
    response = auth_client.put(f"/api/v1/teams/{team_id}/roster/starters", json={"starter_player_ids": new_starters})

    # Assert
    assert response.status_code == 200

    # Verify the new starter is set
    roster_slot = (
        db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.player_id == players[2].id).first()
    )
    assert roster_slot is not None
    assert roster_slot.is_starter == 1

    # Verify the old starter is now on the bench
    roster_slot = (
        db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.player_id == players[8].id).first()
    )
    assert roster_slot is not None
    assert roster_slot.is_starter == 0

    # Verify the moves counter increased
    team = db.query(Team).filter_by(id=team_id).first()
    assert team.moves_this_week == 1


def test_set_starters_invalid_positions(auth_client, setup_roster_test_data):
    # Arrange
    team_id = setup_roster_test_data["team"].id
    players = setup_roster_test_data["players"]

    # Invalid lineup - only 1 guard
    invalid_starters = [
        players[0].id,  # G
        players[4].id,  # F
        players[5].id,  # F
        players[6].id,  # F
        players[8].id,  # C
    ]

    # Act
    response = auth_client.put(
        f"/api/v1/teams/{team_id}/roster/starters", json={"starter_player_ids": invalid_starters}
    )

    # Assert
    assert response.status_code == 400
    assert "must include at least 2 players with Guard" in response.json()["detail"]


def test_set_starters_move_limit_reached(auth_client, setup_roster_test_data, db: Session):
    # Arrange
    team = setup_roster_test_data["team"]
    players = setup_roster_test_data["players"]

    # Set the team's moves_this_week to the limit
    team.moves_this_week = 3
    db.commit()

    # Try to make a change to the starters
    new_starters = [players[0].id, players[1].id, players[4].id, players[5].id, players[2].id]  # New starter

    # Act
    response = auth_client.put(f"/api/v1/teams/{team.id}/roster/starters", json={"starter_player_ids": new_starters})

    # Assert
    assert response.status_code == 400
    assert "Not enough moves left for the week" in response.json()["detail"]
