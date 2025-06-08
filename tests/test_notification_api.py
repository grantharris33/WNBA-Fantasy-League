"""Tests for notification API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models import League, Player, Team, User
from app.services.notification import NotificationService, NotificationType


@pytest.fixture
def sample_user(db):
    """Create a sample user for testing."""
    user = User(email="test@example.com", hashed_password="hashed_password")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def sample_league(db):
    """Create a sample league for testing."""
    league = League(name="Test League", invite_code="TEST123", max_teams=8)
    db.add(league)
    db.flush()
    return league


@pytest.fixture
def sample_team(db, sample_user, sample_league):
    """Create a sample team for testing."""
    team = Team(name="Test Team", owner_id=sample_user.id, league_id=sample_league.id)
    db.add(team)
    db.flush()
    return team


@pytest.fixture
def sample_player(db):
    """Create a sample player for testing."""
    player = Player(id=1001, full_name="Test Player", position="G", team_abbr="TST")
    db.add(player)
    db.flush()
    return player


@pytest.fixture
def auth_headers(sample_user):
    """Create authentication headers for a sample user."""
    token = create_access_token(data={"sub": str(sample_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestNotificationAPI:
    """Test cases for notification API endpoints."""

    def test_get_notifications_unauthorized(self, client: TestClient):
        """Test getting notifications without authentication."""
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 401

    def test_get_notifications_empty(self, client: TestClient, auth_headers):
        """Test getting notifications when user has none."""
        response = client.get("/api/v1/notifications/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == 0
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_get_notifications_with_data(self, client: TestClient, auth_headers, db, sample_user):
        """Test getting notifications when user has some."""
        # Create notifications directly in database
        service = NotificationService(db)
        service.create_notification(
            user_id=sample_user.id,
            title="Test Notification 1",
            message="First message",
            notification_type=NotificationType.INFO,
        )
        service.create_notification(
            user_id=sample_user.id,
            title="Test Notification 2",
            message="Second message",
            notification_type=NotificationType.SUCCESS,
        )

        response = client.get("/api/v1/notifications/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert len(data["notifications"]) == 2
        assert data["total"] == 2

        # Should be ordered by created_at DESC
        assert data["notifications"][0]["title"] == "Test Notification 2"
        assert data["notifications"][1]["title"] == "Test Notification 1"

    def test_get_notifications_with_pagination(self, client: TestClient, auth_headers, db, sample_user):
        """Test notification pagination parameters."""
        # Create multiple notifications
        service = NotificationService(db)
        for i in range(5):
            service.create_notification(user_id=sample_user.id, title=f"Notification {i}", message=f"Message {i}")

        # Test limit
        response = client.get("/api/v1/notifications/?limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 3
        assert data["limit"] == 3

        # Test offset
        response = client.get("/api/v1/notifications/?limit=2&offset=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 2
        assert data["offset"] == 2

    def test_get_notifications_unread_only(self, client: TestClient, auth_headers, db, sample_user):
        """Test filtering for unread notifications only."""
        service = NotificationService(db)

        # Create notifications and mark one as read
        notification1 = service.create_notification(
            user_id=sample_user.id, title="Unread Notification", message="Unread message"
        )
        notification2 = service.create_notification(
            user_id=sample_user.id, title="Read Notification", message="Read message"
        )

        # Mark second notification as read
        service.mark_as_read(notification2.id, sample_user.id)

        # Get unread only
        response = client.get("/api/v1/notifications/?unread_only=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["id"] == notification1.id
        assert data["notifications"][0]["is_read"] is False

    def test_get_unread_count(self, client: TestClient, auth_headers, db, sample_user):
        """Test getting unread notification count."""
        # Initially should be 0
        response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

        # Create notifications
        service = NotificationService(db)
        for i in range(3):
            service.create_notification(user_id=sample_user.id, title=f"Notification {i}", message=f"Message {i}")

        response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_mark_notification_as_read(self, client: TestClient, auth_headers, db, sample_user):
        """Test marking a notification as read."""
        service = NotificationService(db)
        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        assert notification.is_read is False

        # Mark as read
        response = client.put(f"/api/v1/notifications/{notification.id}/read", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "marked as read" in data["message"]

        # Verify it's marked as read
        db.refresh(notification)
        assert notification.is_read is True

    def test_mark_notification_as_read_not_found(self, client: TestClient, auth_headers):
        """Test marking nonexistent notification as read."""
        response = client.put("/api/v1/notifications/999999/read", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Notification not found"

    def test_mark_notification_as_read_wrong_user(self, client: TestClient, db, sample_user):
        """Test marking notification as read with wrong user."""
        # Create notification for sample_user
        service = NotificationService(db)
        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        # Create another user and get their auth headers
        from app.core.security import create_access_token
        from app.models import User

        other_user = User(email="other@test.com", hashed_password="hashed")
        db.add(other_user)
        db.commit()

        other_token = create_access_token(data={"sub": str(other_user.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to mark notification as read with other user
        response = client.put(f"/api/v1/notifications/{notification.id}/read", headers=other_headers)
        assert response.status_code == 404  # Should not find notification belonging to other user

    def test_mark_all_as_read(self, client: TestClient, auth_headers, db, sample_user):
        """Test marking all notifications as read."""
        # Create multiple notifications
        service = NotificationService(db)
        notifications = []
        for i in range(3):
            notification = service.create_notification(
                user_id=sample_user.id, title=f"Notification {i}", message=f"Message {i}"
            )
            notifications.append(notification)

        # All should be unread initially
        for notification in notifications:
            assert notification.is_read is False

        # Mark all as read
        response = client.put("/api/v1/notifications/read-all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "3 notifications" in data["message"]

        # Verify all are marked as read
        for notification in notifications:
            db.refresh(notification)
            assert notification.is_read is True

    def test_delete_notification(self, client: TestClient, auth_headers, db, sample_user):
        """Test deleting a notification."""
        service = NotificationService(db)
        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        notification_id = notification.id

        # Delete notification
        response = client.delete(f"/api/v1/notifications/{notification_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"]

        # Verify it's deleted
        from app.models import Notification

        deleted_notification = db.query(Notification).filter(Notification.id == notification_id).first()
        assert deleted_notification is None

    def test_delete_notification_not_found(self, client: TestClient, auth_headers):
        """Test deleting nonexistent notification."""
        response = client.delete("/api/v1/notifications/999999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Notification not found"

    def test_delete_notification_wrong_user(self, client: TestClient, db, sample_user):
        """Test deleting notification with wrong user."""
        # Create notification for sample_user
        service = NotificationService(db)
        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        # Create another user and get their auth headers
        from app.core.security import create_access_token
        from app.models import User

        other_user = User(email="other@test.com", hashed_password="hashed")
        db.add(other_user)
        db.commit()

        other_token = create_access_token(data={"sub": str(other_user.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to delete notification with other user
        response = client.delete(f"/api/v1/notifications/{notification.id}", headers=other_headers)
        assert response.status_code == 404  # Should not find notification belonging to other user

    def test_notification_response_format(
        self, client: TestClient, auth_headers, db, sample_user, sample_league, sample_team, sample_player
    ):
        """Test that notification response has correct format."""
        service = NotificationService(db)
        notification = service.create_notification(
            user_id=sample_user.id,
            title="Test Notification",
            message="Test message",
            notification_type=NotificationType.DRAFT_PICK,
            league_id=sample_league.id,
            team_id=sample_team.id,
            player_id=sample_player.id,
        )

        response = client.get("/api/v1/notifications/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert len(data["notifications"]) == 1
        notification_data = data["notifications"][0]

        # Check all required fields are present
        required_fields = ["id", "title", "message", "type", "is_read", "created_at"]
        for field in required_fields:
            assert field in notification_data

        # Check optional fields
        assert notification_data["league_id"] == sample_league.id
        assert notification_data["team_id"] == sample_team.id
        assert notification_data["player_id"] == sample_player.id
        assert notification_data["read_at"] is None  # Should be None for unread notification

        # Check values
        assert notification_data["id"] == notification.id
        assert notification_data["title"] == "Test Notification"
        assert notification_data["message"] == "Test message"
        assert notification_data["type"] == "draft_pick"
        assert notification_data["is_read"] is False
