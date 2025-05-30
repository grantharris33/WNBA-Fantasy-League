import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import hash_password
from app.main import app
from app.models import League, Team, User


@pytest.fixture
def auth_client(db):
    """Create a test client with a mocked authenticated user."""

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
def setup_team_test_data(db: Session):
    """Create test data for team endpoint tests."""
    # Create test users
    hashed_password = hash_password("password123")
    user1 = User(id=1, email="test@example.com", hashed_password=hashed_password)  # Matches mock user in auth_client
    user2 = User(id=2, email="user2@example.com", hashed_password=hashed_password)
    db.add_all([user1, user2])
    db.flush()

    # Create test leagues with invite codes
    league1 = League(name="Test League 1", invite_code="LEAGUE-TEST-0001")
    league2 = League(name="Test League 2", invite_code="LEAGUE-TEST-0002")
    db.add_all([league1, league2])
    db.flush()

    # Create test teams
    team1 = Team(name="Team 1", owner_id=user1.id, league_id=league1.id)
    team2 = Team(name="Team 2", owner_id=user2.id, league_id=league1.id)
    team3 = Team(name="Team 3", owner_id=user1.id, league_id=league2.id)
    db.add_all([team1, team2, team3])
    db.commit()

    return {
        "users": [user1, user2],
        "leagues": [league1, league2],
        "teams": [team1, team2, team3],
    }


def test_create_team_success(auth_client, setup_team_test_data, db: Session):
    """Test successfully creating a team."""
    # User1 (our authenticated user) doesn't have a team in a new league yet
    new_league = League(name="New Test League", invite_code="LEAGUE-TEST-0003")
    db.add(new_league)
    db.commit()

    response = auth_client.post(
        f"/api/v1/leagues/{new_league.id}/teams",
        json={"name": "New Team"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Team"
    assert data["league_id"] == new_league.id
    assert data["owner_id"] == 1  # Our mocked authenticated user
    assert "roster" in data
    assert "season_points" in data


def test_create_team_league_not_found(auth_client):
    """Test creating a team with non-existent league."""
    response = auth_client.post(
        "/api/v1/leagues/9999/teams",  # Non-existent league ID
        json={"name": "New Team"}
    )

    assert response.status_code == 404
    assert "League not found" in response.json()["detail"]


def test_create_team_name_conflicts_skipped(auth_client, setup_team_test_data):
    """Test the order of validation - one team per user per league is checked before name uniqueness."""
    # Create a new league
    league = setup_team_test_data["leagues"][0]

    # Try creating a team with a name that already exists in the league
    existing_name = setup_team_test_data["teams"][0].name

    # The important validation is that a user can't have more than one team per league
    # This check happens before name uniqueness check
    response = auth_client.post(
        f"/api/v1/leagues/{league.id}/teams",
        json={"name": existing_name}
    )

    assert response.status_code == 409
    assert "User already owns a team in this league" in response.json()["detail"]


def test_create_team_one_per_user_per_league(auth_client, setup_team_test_data):
    """Test that a user can only own one team per league."""
    # User1 (our authenticated user) already has a team in league1
    league_id = setup_team_test_data["leagues"][0].id

    response = auth_client.post(
        f"/api/v1/leagues/{league_id}/teams",
        json={"name": "Another Team"}
    )

    assert response.status_code == 409
    assert "User already owns a team in this league" in response.json()["detail"]


def test_list_my_teams(auth_client, setup_team_test_data):
    """Test listing authenticated user's teams."""
    response = auth_client.get("/api/v1/users/me/teams")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # User1 has 2 teams
    team_names = [team["name"] for team in data]
    assert "Team 1" in team_names
    assert "Team 3" in team_names


def test_list_league_teams(auth_client, setup_team_test_data):
    """Test listing all teams in a league."""
    league_id = setup_team_test_data["leagues"][0].id

    response = auth_client.get(f"/api/v1/leagues/{league_id}/teams")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # League1 has 2 teams
    team_names = [team["name"] for team in data]
    assert "Team 1" in team_names
    assert "Team 2" in team_names


def test_list_league_teams_not_found(auth_client):
    """Test listing teams for a non-existent league."""
    response = auth_client.get("/api/v1/leagues/9999/teams")  # Non-existent league ID

    assert response.status_code == 404
    assert "League not found" in response.json()["detail"]


def test_update_team_success(auth_client, setup_team_test_data, db: Session):
    """Test successfully updating a team."""
    team_id = setup_team_test_data["teams"][0].id  # Team1 is owned by User1

    response = auth_client.put(
        f"/api/v1/teams/{team_id}",
        json={"name": "Updated Team Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Team Name"

    # Verify DB was updated
    team = db.query(Team).filter(Team.id == team_id).first()
    assert team.name == "Updated Team Name"


def test_update_team_not_found(auth_client):
    """Test updating a non-existent team."""
    response = auth_client.put(
        "/api/v1/teams/9999",  # Non-existent team ID
        json={"name": "Updated Team Name"}
    )

    assert response.status_code == 404
    assert "Team not found" in response.json()["detail"]


def test_update_team_not_owner(auth_client, setup_team_test_data):
    """Test that only the owner can update a team."""
    team_id = setup_team_test_data["teams"][1].id  # Team2 is owned by User2, not our authenticated User1

    response = auth_client.put(
        f"/api/v1/teams/{team_id}",
        json={"name": "Updated Team Name"}
    )

    assert response.status_code == 403
    assert "Not team owner" in response.json()["detail"]


def test_update_team_duplicate_name(auth_client, setup_team_test_data):
    """Test updating a team with a name that already exists in the league."""
    team_id = setup_team_test_data["teams"][0].id  # Team1 is owned by User1
    existing_name = setup_team_test_data["teams"][1].name  # Name of Team2 in same league

    response = auth_client.put(
        f"/api/v1/teams/{team_id}",
        json={"name": existing_name}
    )

    assert response.status_code == 409
    assert "Team name already exists" in response.json()["detail"]