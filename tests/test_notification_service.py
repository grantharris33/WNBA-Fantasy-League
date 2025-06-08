"""Tests for notification service."""

from datetime import datetime

import pytest

from app.models import League, Notification, Player, Team, User
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


class TestNotificationService:
    """Test cases for NotificationService."""

    def test_create_notification(self, db, sample_user):
        """Test creating a basic notification."""
        service = NotificationService(db)

        notification = service.create_notification(
            user_id=sample_user.id,
            title="Test Notification",
            message="This is a test message",
            notification_type=NotificationType.INFO,
        )

        assert notification.id is not None
        assert notification.user_id == sample_user.id
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.type == "info"
        assert notification.is_read is False
        assert notification.created_at is not None

    def test_create_notification_with_references(self, db, sample_user, sample_league, sample_team, sample_player):
        """Test creating a notification with entity references."""
        service = NotificationService(db)

        notification = service.create_notification(
            user_id=sample_user.id,
            title="Draft Pick",
            message="Player drafted",
            notification_type=NotificationType.DRAFT_PICK,
            league_id=sample_league.id,
            team_id=sample_team.id,
            player_id=sample_player.id,
        )

        assert notification.league_id == sample_league.id
        assert notification.team_id == sample_team.id
        assert notification.player_id == sample_player.id

    def test_get_user_notifications(self, db, sample_user):
        """Test retrieving user notifications."""
        service = NotificationService(db)

        # Create multiple notifications
        service.create_notification(user_id=sample_user.id, title="First Notification", message="First message")
        service.create_notification(user_id=sample_user.id, title="Second Notification", message="Second message")

        notifications = service.get_user_notifications(sample_user.id)

        assert len(notifications) == 2
        # Should be ordered by created_at DESC (most recent first)
        assert notifications[0].title == "Second Notification"
        assert notifications[1].title == "First Notification"

    def test_get_user_notifications_with_pagination(self, db, sample_user):
        """Test notification pagination."""
        service = NotificationService(db)

        # Create 5 notifications
        for i in range(5):
            service.create_notification(user_id=sample_user.id, title=f"Notification {i}", message=f"Message {i}")

        # Test limit
        notifications = service.get_user_notifications(sample_user.id, limit=3)
        assert len(notifications) == 3

        # Test offset
        notifications = service.get_user_notifications(sample_user.id, limit=2, offset=2)
        assert len(notifications) == 2

    def test_get_user_notifications_unread_only(self, db, sample_user):
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
        unread_notifications = service.get_user_notifications(sample_user.id, unread_only=True)
        assert len(unread_notifications) == 1
        assert unread_notifications[0].id == notification1.id

    def test_get_unread_count(self, db, sample_user):
        """Test getting unread notification count."""
        service = NotificationService(db)

        # Initially should be 0
        assert service.get_unread_count(sample_user.id) == 0

        # Create 3 notifications
        for i in range(3):
            service.create_notification(user_id=sample_user.id, title=f"Notification {i}", message=f"Message {i}")

        assert service.get_unread_count(sample_user.id) == 3

        # Mark one as read
        notifications = service.get_user_notifications(sample_user.id)
        service.mark_as_read(notifications[0].id, sample_user.id)

        assert service.get_unread_count(sample_user.id) == 2

    def test_mark_as_read(self, db, sample_user):
        """Test marking a notification as read."""
        service = NotificationService(db)

        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        assert notification.is_read is False
        assert notification.read_at is None

        # Mark as read
        success = service.mark_as_read(notification.id, sample_user.id)
        assert success is True

        # Refresh and check
        db.refresh(notification)
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_mark_as_read_wrong_user(self, db, sample_user):
        """Test marking notification as read with wrong user ID."""
        service = NotificationService(db)

        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        # Try to mark as read with wrong user ID
        success = service.mark_as_read(notification.id, sample_user.id + 999)
        assert success is False

    def test_mark_as_read_nonexistent_notification(self, db, sample_user):
        """Test marking nonexistent notification as read."""
        service = NotificationService(db)

        success = service.mark_as_read(999999, sample_user.id)
        assert success is False

    def test_mark_all_as_read(self, db, sample_user):
        """Test marking all notifications as read."""
        service = NotificationService(db)

        # Create 3 notifications
        for i in range(3):
            service.create_notification(user_id=sample_user.id, title=f"Notification {i}", message=f"Message {i}")

        assert service.get_unread_count(sample_user.id) == 3

        # Mark all as read
        updated_count = service.mark_all_as_read(sample_user.id)
        assert updated_count == 3
        assert service.get_unread_count(sample_user.id) == 0

    def test_delete_notification(self, db, sample_user):
        """Test deleting a notification."""
        service = NotificationService(db)

        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        notification_id = notification.id

        # Delete notification
        success = service.delete_notification(notification_id, sample_user.id)
        assert success is True

        # Verify it's deleted
        deleted_notification = db.query(Notification).filter(Notification.id == notification_id).first()
        assert deleted_notification is None

    def test_delete_notification_wrong_user(self, db, sample_user):
        """Test deleting notification with wrong user ID."""
        service = NotificationService(db)

        notification = service.create_notification(
            user_id=sample_user.id, title="Test Notification", message="Test message"
        )

        # Try to delete with wrong user ID
        success = service.delete_notification(notification.id, sample_user.id + 999)
        assert success is False

    def test_create_bulk_notifications(self, db):
        """Test creating bulk notifications for multiple users."""
        service = NotificationService(db)

        # Create multiple users
        user1 = User(email="user1@test.com", hashed_password="hashed")
        user2 = User(email="user2@test.com", hashed_password="hashed")
        user3 = User(email="user3@test.com", hashed_password="hashed")
        db.add_all([user1, user2, user3])
        db.commit()

        user_ids = [user1.id, user2.id, user3.id]

        notifications = service.create_bulk_notifications(
            user_ids=user_ids,
            title="Bulk Notification",
            message="This is a bulk message",
            notification_type=NotificationType.LEAGUE_INVITE,
        )

        assert len(notifications) == 3

        # Verify each user got a notification
        for i, user_id in enumerate(user_ids):
            assert notifications[i].user_id == user_id
            assert notifications[i].title == "Bulk Notification"
            assert notifications[i].message == "This is a bulk message"
            assert notifications[i].type == "league_invite"

    def test_notify_draft_pick(self, db, sample_user, sample_league, sample_team, sample_player):
        """Test draft pick notification convenience method."""
        service = NotificationService(db)

        notification = service.notify_draft_pick(
            user_id=sample_user.id,
            player_name=sample_player.full_name,
            team_name=sample_team.name,
            league_id=sample_league.id,
            team_id=sample_team.id,
            player_id=sample_player.id,
        )

        assert notification.title == "Draft Pick Made"
        assert sample_player.full_name in notification.message
        assert sample_team.name in notification.message
        assert notification.type == "draft_pick"
        assert notification.league_id == sample_league.id
        assert notification.team_id == sample_team.id
        assert notification.player_id == sample_player.id

    def test_notify_draft_start(self, db, sample_league):
        """Test draft start notification convenience method."""
        service = NotificationService(db)

        # Create multiple users
        user1 = User(email="user1@test.com", hashed_password="hashed")
        user2 = User(email="user2@test.com", hashed_password="hashed")
        db.add_all([user1, user2])
        db.commit()

        user_ids = [user1.id, user2.id]

        notifications = service.notify_draft_start(
            user_ids=user_ids, league_name=sample_league.name, league_id=sample_league.id
        )

        assert len(notifications) == 2
        for notification in notifications:
            assert notification.title == "Draft Started"
            assert sample_league.name in notification.message
            assert notification.type == "draft_start"
            assert notification.league_id == sample_league.id

    def test_notify_roster_move_add(self, db, sample_user, sample_league, sample_team, sample_player):
        """Test roster move notification for adding a player."""
        service = NotificationService(db)

        notification = service.notify_roster_move(
            user_id=sample_user.id,
            action="added",
            player_name=sample_player.full_name,
            team_name=sample_team.name,
            league_id=sample_league.id,
            team_id=sample_team.id,
            player_id=sample_player.id,
        )

        assert notification.title == "Player Added"
        assert sample_player.full_name in notification.message
        assert sample_team.name in notification.message
        assert "added" in notification.message
        assert notification.type == "roster_add"

    def test_notify_roster_move_drop(self, db, sample_user, sample_league, sample_team, sample_player):
        """Test roster move notification for dropping a player."""
        service = NotificationService(db)

        notification = service.notify_roster_move(
            user_id=sample_user.id,
            action="dropped",
            player_name=sample_player.full_name,
            team_name=sample_team.name,
            league_id=sample_league.id,
            team_id=sample_team.id,
            player_id=sample_player.id,
        )

        assert notification.title == "Player Dropped"
        assert sample_player.full_name in notification.message
        assert sample_team.name in notification.message
        assert "dropped" in notification.message
        assert notification.type == "roster_drop"

    def test_notify_game_start(self, db):
        """Test game start notification convenience method."""
        service = NotificationService(db)

        # Create multiple users
        user1 = User(email="user1@test.com", hashed_password="hashed")
        user2 = User(email="user2@test.com", hashed_password="hashed")
        db.add_all([user1, user2])
        db.commit()

        user_ids = [user1.id, user2.id]

        notifications = service.notify_game_start(user_ids=user_ids, game_description="Lakers vs Aces")

        assert len(notifications) == 2
        for notification in notifications:
            assert notification.title == "Game Started"
            assert "Lakers vs Aces" in notification.message
            assert notification.type == "game_start"
