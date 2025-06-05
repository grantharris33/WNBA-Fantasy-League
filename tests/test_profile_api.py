"""Tests for user profile API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models import User, UserPreferences, UserProfile

# Import handled by conftest.py


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    from app.core.security import hash_password

    user = User(email="test@example.com", hashed_password=hash_password("testpass123"), is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User, db: Session):
    """Get auth headers for test user."""
    from app.core.security import create_access_token

    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db: Session):
    """Create test client with database override."""
    import os
    os.environ["TESTING"] = "true"  # This prevents scheduler from starting
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestProfileAPI:
    """Test profile API endpoints."""

    def test_get_profile_creates_default(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting profile creates default if not exists."""
        response = client.get("/api/v1/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] is None
        assert data["timezone"] == "UTC"
        assert data["email_verified"] is False

    def test_update_profile(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating profile information."""
        update_data = {
            "display_name": "Test User",
            "bio": "I love WNBA fantasy!",
            "location": "New York, NY",
            "timezone": "America/New_York",
        }
        response = client.put("/api/v1/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Test User"
        assert data["bio"] == "I love WNBA fantasy!"
        assert data["location"] == "New York, NY"
        assert data["timezone"] == "America/New_York"

    def test_get_preferences_creates_default(self, client: TestClient, auth_headers: dict, db: Session):
        """Test getting preferences creates default if not exists."""
        response = client.get("/api/v1/profile/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "light"
        assert data["email_notifications"] is True
        assert data["profile_visibility"] == "public"

    def test_update_preferences(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating user preferences."""
        update_data = {
            "theme": "dark",
            "email_notifications": False,
            "profile_visibility": "private",
            "favorite_team_ids": [1, 2, 3],
        }
        response = client.put("/api/v1/profile/preferences", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["email_notifications"] is False
        assert data["profile_visibility"] == "private"
        assert data["favorite_team_ids"] == [1, 2, 3]

    def test_update_password(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating password."""
        update_data = {"current_password": "testpass123", "new_password": "newpass123"}
        response = client.put("/api/v1/profile/password", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"

    def test_update_password_wrong_current(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating password with wrong current password."""
        update_data = {"current_password": "wrongpass", "new_password": "newpass123"}
        response = client.put("/api/v1/profile/password", json=update_data, headers=auth_headers)
        assert response.status_code == 401
        assert "Invalid current password" in response.json()["detail"]

    def test_update_email(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating email address."""
        update_data = {"new_email": "newemail@example.com", "password": "testpass123"}
        response = client.put("/api/v1/profile/email", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert "Email updated successfully" in response.json()["message"]

    def test_update_email_duplicate(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating to duplicate email."""
        # Create another user
        from app.core.security import hash_password

        other_user = User(email="other@example.com", hashed_password=hash_password("password"))
        db.add(other_user)
        db.commit()

        update_data = {"new_email": "other@example.com", "password": "testpass123"}
        response = client.put("/api/v1/profile/email", json=update_data, headers=auth_headers)
        assert response.status_code == 400
        assert "Email already in use" in response.json()["detail"]

    def test_resend_verification(self, client: TestClient, auth_headers: dict, db: Session):
        """Test resending email verification."""
        response = client.post("/api/v1/profile/resend-verification", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Verification email sent"

    def test_resend_verification_already_verified(self, client: TestClient, auth_headers: dict, db: Session):
        """Test resending verification when already verified."""
        # First get profile to create it
        client.get("/api/v1/profile", headers=auth_headers)

        # Mark as verified
        profile = db.query(UserProfile).filter(UserProfile.user_id == 1).first()
        profile.email_verified = True
        db.commit()

        response = client.post("/api/v1/profile/resend-verification", headers=auth_headers)
        assert response.status_code == 400
        assert "Email already verified" in response.json()["detail"]

    def test_delete_avatar(self, client: TestClient, auth_headers: dict, db: Session):
        """Test deleting avatar."""
        # First set an avatar
        client.get("/api/v1/profile", headers=auth_headers)
        profile = db.query(UserProfile).filter(UserProfile.user_id == 1).first()
        profile.avatar_url = "https://example.com/avatar.jpg"
        db.commit()

        response = client.delete("/api/v1/profile/avatar", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Avatar deleted successfully"

        # Verify avatar was deleted
        db.refresh(profile)
        assert profile.avatar_url is None

    def test_profile_requires_auth(self, client: TestClient):
        """Test that profile endpoints require authentication."""
        endpoints = [
            ("GET", "/api/v1/profile"),
            ("PUT", "/api/v1/profile"),
            ("GET", "/api/v1/profile/preferences"),
            ("PUT", "/api/v1/profile/preferences"),
            ("POST", "/api/v1/profile/avatar"),
            ("DELETE", "/api/v1/profile/avatar"),
            ("PUT", "/api/v1/profile/password"),
            ("PUT", "/api/v1/profile/email"),
            ("POST", "/api/v1/profile/resend-verification"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "POST":
                response = client.post(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code == 401

    def test_theme_preference_validation(self, client: TestClient, auth_headers: dict, db: Session):
        """Test theme preference validation."""
        update_data = {"theme": "invalid_theme"}
        response = client.put("/api/v1/profile/preferences", json=update_data, headers=auth_headers)
        assert response.status_code == 422

    def test_profile_visibility_validation(self, client: TestClient, auth_headers: dict, db: Session):
        """Test profile visibility validation."""
        update_data = {"profile_visibility": "invalid_visibility"}
        response = client.put("/api/v1/profile/preferences", json=update_data, headers=auth_headers)
        assert response.status_code == 422

    def test_accent_color_validation(self, client: TestClient, auth_headers: dict, db: Session):
        """Test accent color validation."""
        # Valid hex color
        update_data = {"accent_color": "#FF5733"}
        response = client.put("/api/v1/profile/preferences", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        # Invalid hex color
        update_data = {"accent_color": "not_a_color"}
        response = client.put("/api/v1/profile/preferences", json=update_data, headers=auth_headers)
        assert response.status_code == 422

    def test_partial_preferences_update(self, client: TestClient, auth_headers: dict, db: Session):
        """Test updating only some preferences."""
        # First set all preferences
        initial_data = {
            "theme": "light",
            "email_notifications": True,
            "show_player_photos": True,
            "profile_visibility": "public",
        }
        client.put("/api/v1/profile/preferences", json=initial_data, headers=auth_headers)

        # Update only theme
        update_data = {"theme": "dark"}
        response = client.put("/api/v1/profile/preferences", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Check that only theme changed
        assert data["theme"] == "dark"
        assert data["email_notifications"] is True
        assert data["show_player_photos"] is True
        assert data["profile_visibility"] == "public"
