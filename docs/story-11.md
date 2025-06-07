# Story 11: Complete Settings Page Implementation

**Priority**: P2 - Important  
**Effort**: 2 days  
**Dependencies**: Story 1 (Integration fixes)

## Overview
The Settings page exists but doesn't actually save settings. Theme changes don't persist, notification preferences aren't respected, and timezone settings have no effect. This creates a poor user experience.

## Acceptance Criteria
1. All settings are saved to the backend
2. Settings persist across sessions
3. Theme changes apply immediately and persist
4. Notification preferences are respected
5. Timezone affects all date/time displays
6. Privacy settings have actual effects

## Technical Tasks

### Backend Implementation (8 hours)

#### 1. Update User Preferences Model (2 hours)
```python
# app/models/user_profile.py
# Verify/update UserPreferences model to include:
- [ ] theme (light/dark/system)
- [ ] timezone
- [ ] notification_email (boolean)
- [ ] notification_push (boolean)
- [ ] notification_trade_offers (boolean)
- [ ] notification_draft_reminders (boolean)
- [ ] notification_game_starts (boolean)
- [ ] notification_weekly_summary (boolean)
- [ ] privacy_show_email (boolean)
- [ ] privacy_show_real_name (boolean)
- [ ] language (future)
```

#### 2. Update Preferences Service (3 hours)
```python
# app/services/user_preferences.py
- [ ] get_user_preferences(user_id)
- [ ] update_user_preferences(user_id, preferences)
- [ ] get_default_preferences()
- [ ] validate_timezone(timezone)
- [ ] apply_privacy_settings(user_data, viewer_id)
```

#### 3. Update API Endpoints (3 hours)
```python
# app/api/profile.py
- [ ] Ensure GET /api/v1/profile/preferences returns all settings
- [ ] Ensure PUT /api/v1/profile/preferences saves all settings
- [ ] Add validation for timezone format
- [ ] Add validation for theme values
```

### Frontend Implementation (12 hours)

#### 1. Fix Settings State Management (4 hours)
```typescript
// frontend/src/pages/SettingsPage.tsx
- [ ] Load actual preferences from API on mount
- [ ] Save preferences to backend on change
- [ ] Add loading states during save
- [ ] Show success/error messages
- [ ] Implement optimistic updates
```

#### 2. Implement Theme Persistence (3 hours)
```typescript
// frontend/src/contexts/ThemeContext.tsx
- [ ] Load theme preference from backend
- [ ] Save theme changes to backend
- [ ] Apply theme immediately
- [ ] Persist theme in localStorage for quick loading
- [ ] Handle system theme preference
```

#### 3. Implement Timezone Support (3 hours)
```typescript
// frontend/src/utils/datetime.ts
- [ ] Create timezone-aware date formatting
- [ ] Apply user timezone to all dates
- [ ] Show timezone in date displays
- [ ] Handle timezone in form inputs

// frontend/src/hooks/useUserTimezone.ts
- [ ] Get user's timezone preference
- [ ] Provide timezone formatting functions
```

#### 4. Update Settings UI (2 hours)
```typescript
// frontend/src/pages/SettingsPage.tsx
- [ ] Add saving indicators
- [ ] Add success messages
- [ ] Improve form validation
- [ ] Add reset to defaults option
- [ ] Group related settings
```

## Settings Categories

### 1. Appearance
```typescript
interface AppearanceSettings {
  theme: 'light' | 'dark' | 'system';
  compactView: boolean; // future
  colorblindMode: boolean; // future
}
```

### 2. Notifications
```typescript
interface NotificationSettings {
  emailNotifications: boolean;
  pushNotifications: boolean; // future
  tradeOffers: boolean;
  draftReminders: boolean;
  gameStarts: boolean;
  weeklySummary: boolean;
  leagueAnnouncements: boolean;
}
```

### 3. Privacy
```typescript
interface PrivacySettings {
  showEmail: boolean;
  showRealName: boolean;
  publicProfile: boolean; // future
  shareStatistics: boolean; // future
}
```

### 4. Regional
```typescript
interface RegionalSettings {
  timezone: string; // IANA timezone
  dateFormat: 'MM/DD/YYYY' | 'DD/MM/YYYY';
  timeFormat: '12h' | '24h';
  language: string; // future
}
```

## UI Improvements

### Settings Layout
```
Settings
├── Appearance
│   ├── Theme: [Light] [Dark] [System]
│   └── Compact View: [ ] Enable
├── Notifications
│   ├── Email Notifications: [✓] Enable
│   ├── Trade Offers: [✓]
│   ├── Draft Reminders: [✓]
│   └── Game Starts: [ ]
├── Privacy
│   ├── Show Email: [ ] Allow
│   └── Show Real Name: [✓] Allow
└── Regional
    ├── Timezone: [America/New_York ▼]
    └── Time Format: [12 hour ▼]
```

### Save Behavior
- Auto-save on change with debounce
- Show saving indicator
- Show success message
- Optimistic updates
- Revert on error

## Testing Requirements
- [ ] Test all settings save correctly
- [ ] Test theme persistence
- [ ] Test timezone application
- [ ] Test notification preferences
- [ ] Test privacy settings effects
- [ ] Test error handling
- [ ] Test loading states

## Integration Points
- [ ] Notification service respects preferences
- [ ] All date displays use timezone
- [ ] Theme applies to all components
- [ ] Privacy settings filter API responses

## Database Migration
```sql
-- Ensure all preference fields exist
ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS theme VARCHAR(10) DEFAULT 'light';
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC';
-- etc...
```

## Definition of Done
- All settings save to backend
- Settings persist across sessions
- Theme changes apply immediately
- Timezone affects all dates
- Privacy settings work correctly
- No console errors
- Success/error messages display
- All tests pass