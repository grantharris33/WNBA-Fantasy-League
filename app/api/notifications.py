"""Notification API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas import NotificationListResponse, NotificationResponse, UnreadCountResponse
from app.core.security import decode_access_token
from app.core.ws_manager import manager
from app.models import User
from app.services.notification import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
):
    """Get user notifications with pagination."""
    service = NotificationService(db)
    notifications = service.get_user_notifications(
        user_id=current_user.id, limit=limit, offset=offset, unread_only=unread_only
    )

    return NotificationListResponse(
        notifications=[NotificationResponse.from_orm(n) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    """Get count of unread notifications."""
    service = NotificationService(db)
    count = service.get_unread_count(current_user.id)

    return UnreadCountResponse(count=count)


@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Mark a notification as read."""
    service = NotificationService(db)
    success = service.mark_as_read(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification marked as read"}


@router.put("/read-all")
def mark_all_as_read(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]):
    """Mark all notifications as read."""
    service = NotificationService(db)
    updated_count = service.mark_all_as_read(current_user.id)

    return {"message": f"Marked {updated_count} notifications as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a notification."""
    service = NotificationService(db)
    success = service.delete_notification(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification deleted"}


@router.websocket("/ws")
async def notification_websocket(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time notifications."""
    try:
        # Decode the JWT token to get user info
        payload = decode_access_token(token)
        if payload is None:
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid user")
            return

        user_id = int(user_id)

        # Connect to notification channel
        await manager.connect_notifications(websocket, user_id)

        try:
            # Keep connection alive
            while True:
                # Wait for any message from client (heartbeat)
                data = await websocket.receive_text()
                # Echo back to confirm connection is alive
                await websocket.send_json({"type": "pong", "data": data})

        except WebSocketDisconnect:
            pass

    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Connection error")
    finally:
        # Disconnect from notification channel
        if 'user_id' in locals():
            manager.disconnect_notifications(websocket, user_id)
