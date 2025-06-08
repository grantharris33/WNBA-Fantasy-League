"""Notification service for managing user notifications."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.ws_manager import manager
from app.models import Notification, User


class NotificationType(str, Enum):
    """Enumeration of notification types."""

    DRAFT_PICK = "draft_pick"
    DRAFT_START = "draft_start"
    DRAFT_COMPLETE = "draft_complete"
    ROSTER_ADD = "roster_add"
    ROSTER_DROP = "roster_drop"
    TRADE_OFFER = "trade_offer"
    TRADE_ACCEPTED = "trade_accepted"
    TRADE_REJECTED = "trade_rejected"
    LEAGUE_INVITE = "league_invite"
    GAME_START = "game_start"
    WEEKLY_SUMMARY = "weekly_summary"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationService:
    """Service for managing user notifications."""

    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type.value,
            league_id=league_id,
            team_id=team_id,
            player_id=player_id,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # Send real-time notification via WebSocket
        try:
            import asyncio

            notification_data = {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.type,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "league_id": notification.league_id,
                "team_id": notification.team_id,
                "player_id": notification.player_id,
            }

            # Try to send the notification via WebSocket if there's an event loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(manager.send_notification_to_user(user_id, notification_data))
            except RuntimeError:
                # No event loop running - this is normal in synchronous contexts
                pass
        except Exception as e:
            print(f"Failed to send real-time notification: {e}")

        return notification

    def get_user_notifications(
        self, user_id: int, limit: int = 50, offset: int = 0, unread_only: bool = False
    ) -> list[Notification]:
        """Get notifications for a user with pagination."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read.is_(False))

        query = query.order_by(desc(Notification.created_at))

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        return query.all()

    def get_unread_count(self, user_id: int) -> int:
        """Get the count of unread notifications for a user."""
        return (
            self.db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id)
            .filter(Notification.is_read.is_(False))
            .scalar()
        )

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .filter(Notification.user_id == user_id)
            .first()
        )

        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()

        return True

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user. Returns count of updated notifications."""
        updated_count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .filter(Notification.is_read.is_(False))
            .update({"is_read": True, "read_at": datetime.utcnow()}, synchronize_session=False)
        )

        self.db.commit()
        return updated_count

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .filter(Notification.user_id == user_id)
            .first()
        )

        if not notification:
            return False

        self.db.delete(notification)
        self.db.commit()

        return True

    def create_bulk_notifications(
        self,
        user_ids: list[int],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ) -> list[Notification]:
        """Create the same notification for multiple users."""
        notifications = []

        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type.value,
                league_id=league_id,
                team_id=team_id,
                player_id=player_id,
            )
            notifications.append(notification)

        self.db.add_all(notifications)
        self.db.commit()

        for notification in notifications:
            self.db.refresh(notification)

        return notifications

    # Convenience methods for specific notification types

    def notify_draft_pick(
        self, user_id: int, player_name: str, team_name: str, league_id: int, team_id: int, player_id: int
    ) -> Notification:
        """Create a draft pick notification."""
        return self.create_notification(
            user_id=user_id,
            title="Draft Pick Made",
            message=f"{team_name} drafted {player_name}",
            notification_type=NotificationType.DRAFT_PICK,
            league_id=league_id,
            team_id=team_id,
            player_id=player_id,
        )

    def notify_draft_start(self, user_ids: list[int], league_name: str, league_id: int) -> list[Notification]:
        """Notify all league members that draft has started."""
        return self.create_bulk_notifications(
            user_ids=user_ids,
            title="Draft Started",
            message=f"The draft for {league_name} has begun!",
            notification_type=NotificationType.DRAFT_START,
            league_id=league_id,
        )

    def notify_roster_move(
        self,
        user_id: int,
        action: str,  # "added" or "dropped"
        player_name: str,
        team_name: str,
        league_id: int,
        team_id: int,
        player_id: int,
    ) -> Notification:
        """Create a roster move notification."""
        notification_type = NotificationType.ROSTER_ADD if action == "added" else NotificationType.ROSTER_DROP

        return self.create_notification(
            user_id=user_id,
            title=f"Player {action.title()}",
            message=f"{team_name} {action} {player_name}",
            notification_type=notification_type,
            league_id=league_id,
            team_id=team_id,
            player_id=player_id,
        )

    def notify_game_start(
        self, user_ids: list[int], game_description: str, league_id: Optional[int] = None
    ) -> list[Notification]:
        """Notify users about a game starting."""
        return self.create_bulk_notifications(
            user_ids=user_ids,
            title="Game Started",
            message=f"Game started: {game_description}",
            notification_type=NotificationType.GAME_START,
            league_id=league_id,
        )
