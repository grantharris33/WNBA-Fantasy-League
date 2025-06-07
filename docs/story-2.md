# Story 2: Implement Notification System

**Priority**: P0 - Critical Path
**Dependencies**: Story 1 (Integration fixes)

## Overview
The notification model exists in the backend but there's no service implementation or frontend UI. Users need notifications for draft events, roster moves, game updates, and league activities.

## Acceptance Criteria
1. Backend notification service can create and manage notifications
2. Frontend displays notification badge/count in navigation
3. Notification center shows all user notifications
4. Real-time notifications via WebSocket
5. Email notifications for critical events (optional for MVP)
6. Users can mark notifications as read
7. Notification preferences are respected

## Technical Tasks

### Backend Implementation

#### 1. Create Notification Service
```python
# app/services/notification.py
- [ ] Create NotificationService class
- [ ] Implement create_notification method
- [ ] Implement get_user_notifications with pagination
- [ ] Implement mark_as_read method
- [ ] Implement bulk operations (mark all read, delete)
- [ ] Add notification types enum
```

#### 2. Create Notification API Endpoints
```python
# app/api/notifications.py
- [ ] GET /api/v1/notifications - List user notifications
- [ ] GET /api/v1/notifications/unread-count - Get unread count
- [ ] PUT /api/v1/notifications/{id}/read - Mark as read
- [ ] PUT /api/v1/notifications/read-all - Mark all as read
- [ ] DELETE /api/v1/notifications/{id} - Delete notification
```

#### 3. Add Notification Triggers
- [ ] Draft events: picks made, draft started/completed
- [ ] Roster moves: add/drop, lineup changes
- [ ] Trade offers: proposed, accepted, rejected
- [ ] League events: new member joined, settings changed
- [ ] Game events: games starting, final scores

### Frontend Implementation

#### 1. Create Notification Components
```typescript
// frontend/src/components/notifications/
- [ ] NotificationBadge.tsx - Shows unread count
- [ ] NotificationCenter.tsx - Dropdown/modal with list
- [ ] NotificationItem.tsx - Individual notification display
- [ ] NotificationPreferences.tsx - Settings component
```

#### 2. Add Notification State Management
```typescript
// frontend/src/contexts/NotificationContext.tsx
- [ ] Create notification context
- [ ] WebSocket integration for real-time updates
- [ ] Polling fallback for unread count
- [ ] Cache management
```

#### 3. Integrate Into UI
- [ ] Add notification badge to navbar
- [ ] Create notification center page/modal
- [ ] Add notification preferences to settings
- [ ] Show toast notifications for real-time events

### WebSocket Integration
- [ ] Add notification events to WebSocket protocol
- [ ] Implement real-time notification delivery
- [ ] Handle connection state and reconnection
- [ ] Queue notifications when offline

## Database Schema Updates
```sql
-- Already exists but verify:
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    data JSON,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Add index for performance
CREATE INDEX idx_notifications_user_unread
ON notifications(user_id, is_read, created_at DESC);
```

## Notification Types
```python
class NotificationType(Enum):
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
```

## Testing Requirements
- [ ] Unit tests for notification service
- [ ] API endpoint tests
- [ ] WebSocket notification delivery tests
- [ ] Frontend component tests
- [ ] Integration tests for notification triggers

## Documentation Updates
- [ ] Document notification types and triggers
- [ ] API endpoint documentation
- [ ] WebSocket protocol for notifications
- [ ] User guide for notification settings

## Future Enhancements (Post-MVP)
- Email notifications
- Push notifications
- SMS notifications
- Notification templates
- Rich notifications with actions

## Definition of Done
- Notifications appear in real-time
- Users can view and manage notifications
- Notification preferences are saved and respected
- No performance impact on other features
- All tests pass