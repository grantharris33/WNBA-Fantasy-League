"""Integration tests for league management endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import hash_password
from app.main import app
from app.models import User, League


def create_auth_client(db: Session, user_id: int, email: str):
    """Helper function to create an auth client for a specific user."""
    # Check if user already exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Create a real user in the database for the mock to return
        hashed_password = hash_password("password123")
        user = User(id=user_id, email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Replace the dependency with a mock to bypass authentication
    async def mock_get_current_user():
        return user

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
    return client, user


@pytest.fixture
def auth_client(db):
    """Create a test client with a mocked authenticated user."""
    client, user = create_auth_client(db, 1, "test@example.com")
    yield client
    # Clear dependency overrides
    app.dependency_overrides.clear()


class TestLeagueEndpoints:
    """Test league management endpoints."""

    def test_create_league(self, auth_client):
        """Test creating a league."""
        response = auth_client.post(
            "/api/v1/leagues",
            json={
                "name": "Test League",
                "max_teams": 8,
                "settings": {"scoring": "standard"}
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test League"
        assert data["max_teams"] == 8
        assert data["is_active"] is True
        assert data["invite_code"] is not None
        assert data["invite_code"].startswith("LEAGUE-")

    def test_create_league_invalid_max_teams(self, auth_client):
        """Test creating league with invalid max_teams."""
        response = auth_client.post(
            "/api/v1/leagues",
            json={
                "name": "Test League",
                "max_teams": 1,  # Too low
            },
        )

        assert response.status_code == 422  # Pydantic validation error
        assert "max_teams" in response.json()["detail"][0]["loc"]

    def test_join_league(self, db):
        """Test joining a league."""
        # Create league with first user
        client1, user1 = create_auth_client(db, 1, "test1@example.com")
        response = client1.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        invite_code = response.json()["invite_code"]
        app.dependency_overrides.clear()

        # Join league with second user
        client2, user2 = create_auth_client(db, 2, "test2@example.com")
        response = client2.post(
            "/api/v1/leagues/join",
            json={
                "invite_code": invite_code,
                "team_name": "Test Team"
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Team"
        app.dependency_overrides.clear()

    def test_join_league_invalid_code(self, auth_client):
        """Test joining with invalid invite code."""
        response = auth_client.post(
            "/api/v1/leagues/join",
            json={
                "invite_code": "INVALID-CODE",
                "team_name": "Test Team"
            },
        )

        assert response.status_code == 404
        assert "Invalid or expired invite code" in response.json()["detail"]

    def test_get_league_details_commissioner(self, auth_client, db):
        """Test that commissioner sees invite code."""
        # Create league
        response = auth_client.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        league_id = response.json()["id"]
        invite_code = response.json()["invite_code"]

        # Commissioner should see invite code
        response = auth_client.get(f"/api/v1/leagues/{league_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["invite_code"] == invite_code

    def test_get_league_details_member(self, db):
        """Test that member does not see invite code."""
        # Create league with first user
        client1, user1 = create_auth_client(db, 1, "test1@example.com")
        response = client1.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        league_id = response.json()["id"]
        invite_code = response.json()["invite_code"]
        app.dependency_overrides.clear()

        # Join as second user
        client2, user2 = create_auth_client(db, 2, "test2@example.com")
        response = client2.post(
            "/api/v1/leagues/join",
            json={
                "invite_code": invite_code,
                "team_name": "Test Team"
            },
        )
        assert response.status_code == 201

        # Member should not see invite code
        response = client2.get(f"/api/v1/leagues/{league_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["invite_code"] is None
        app.dependency_overrides.clear()

    def test_update_league(self, auth_client):
        """Test updating league settings."""
        # Create league
        response = auth_client.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        league_id = response.json()["id"]

        # Update league
        response = auth_client.put(
            f"/api/v1/leagues/{league_id}",
            json={"name": "Updated League", "max_teams": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated League"
        assert data["max_teams"] == 10

    def test_update_league_non_commissioner(self, db):
        """Test non-commissioner trying to update league."""
        # Create league with first user
        client1, user1 = create_auth_client(db, 1, "test1@example.com")
        response = client1.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        league_id = response.json()["id"]
        app.dependency_overrides.clear()

        # Try to update as non-commissioner with second user
        client2, user2 = create_auth_client(db, 2, "test2@example.com")
        response = client2.put(
            f"/api/v1/leagues/{league_id}",
            json={"name": "Updated League"},
        )

        assert response.status_code == 403
        assert "Only the commissioner can perform this action" in response.json()["detail"]
        app.dependency_overrides.clear()

    def test_delete_league(self, auth_client):
        """Test deleting a league."""
        # Create league
        response = auth_client.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        league_id = response.json()["id"]

        # Delete league
        response = auth_client.delete(f"/api/v1/leagues/{league_id}")
        assert response.status_code == 204

    def test_generate_new_invite_code(self, auth_client):
        """Test generating new invite code."""
        # Create league
        response = auth_client.post(
            "/api/v1/leagues",
            json={"name": "Test League"},
        )
        assert response.status_code == 201
        league_id = response.json()["id"]
        old_code = response.json()["invite_code"]

        # Generate new invite code
        response = auth_client.post(
            f"/api/v1/leagues/{league_id}/invite-code",
        )

        assert response.status_code == 200
        new_code = response.json()["invite_code"]
        assert new_code != old_code
        assert new_code.startswith("LEAGUE-")

    def test_get_my_leagues(self, db):
        """Test getting user's leagues."""
        # Create league as commissioner with first user
        client1, user1 = create_auth_client(db, 1, "test1@example.com")
        response = client1.post(
            "/api/v1/leagues",
            json={"name": "Owned League"},
        )
        assert response.status_code == 201
        invite_code = response.json()["invite_code"]
        app.dependency_overrides.clear()

        # Create another league with second user
        client2, user2 = create_auth_client(db, 2, "test2@example.com")
        response = client2.post(
            "/api/v1/leagues",
            json={"name": "Member League"},
        )
        assert response.status_code == 201
        invite_code2 = response.json()["invite_code"]
        app.dependency_overrides.clear()

        # Join second league as member with first user
        client1, user1 = create_auth_client(db, 1, "test1@example.com")
        response = client1.post(
            "/api/v1/leagues/join",
            json={
                "invite_code": invite_code2,
                "team_name": "Test Team"
            },
        )
        assert response.status_code == 201

        # Get user leagues with first user
        response = client1.get("/api/v1/leagues/mine")
        assert response.status_code == 200
        leagues = response.json()

        assert len(leagues) == 2

        # Check roles
        roles = {league["league"]["name"]: league["role"] for league in leagues}
        assert roles["Owned League"] == "commissioner"
        assert roles["Member League"] == "member"
        app.dependency_overrides.clear()

    def test_unauthorized_access(self):
        """Test that endpoints require authentication."""
        client = TestClient(app)  # No auth override

        response = client.post("/api/v1/leagues", json={"name": "Test League"})
        assert response.status_code == 401

        response = client.get("/api/v1/leagues/mine")
        assert response.status_code == 401