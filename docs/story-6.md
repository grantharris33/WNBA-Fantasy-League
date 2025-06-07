# Story 6: Complete Live Game Tracking System

**Priority**: P1 - Essential Feature
**Dependencies**: Story 1 (Integration fixes)

## Overview
The backend has WebSocket support for live game tracking but the frontend implementation is minimal. Users need real-time updates during games to track their fantasy scores and player performance.

## Acceptance Criteria
1. Live scoreboard shows all games in progress
2. Real-time fantasy point updates for user's team
3. Live player statistics during games
4. WebSocket connection with automatic reconnection
5. Visual indicators for scoring plays
6. Mobile-optimized live tracking experience

## Technical Tasks

### Frontend Implementation

#### 1. Complete Live Game Components
```typescript
// frontend/src/components/games/
- [ ] LiveScoreboard.tsx - Shows all live games
- [ ] LiveGameCard.tsx - Individual game with real-time score
- [ ] LivePlayerStats.tsx - Real-time player statistics
- [ ] LiveFantasyScore.tsx - Team's live fantasy points
- [ ] LivePlayFeed.tsx - Recent plays affecting fantasy score
- [ ] GameClock.tsx - Game time and quarter display
```

#### 2. Create Live Game Pages
```typescript
// frontend/src/pages/
- [ ] LiveScoreboardPage.tsx - All live games dashboard
- [ ] LiveGameDetailPage.tsx - Single game live tracking
- [ ] LiveFantasyPage.tsx - User's fantasy team live scoring
```

#### 3. Implement WebSocket Management
```typescript
// frontend/src/hooks/useLiveGames.ts
- [ ] WebSocket connection management
- [ ] Auto-reconnection with exponential backoff
- [ ] Message queue for offline handling
- [ ] Connection status indicator

// frontend/src/hooks/useLiveFantasyScore.ts
- [ ] Subscribe to team's live score updates
- [ ] Calculate point changes
- [ ] Track scoring plays
```

#### 4. Add Real-time State Management
```typescript
// frontend/src/contexts/LiveGameContext.tsx
- [ ] Manage live game state
- [ ] Handle WebSocket messages
- [ ] Merge real-time updates with cached data
- [ ] Optimistic UI updates
```

### WebSocket Protocol Implementation

#### 1. Define Message Types (2 hours)
```typescript
interface LiveGameMessage {
  type: 'game_update' | 'player_stats' | 'fantasy_points' | 'play_by_play';
  gameId: number;
  data: any;
  timestamp: string;
}
```

#### 2. Implement Message Handlers
```typescript
// frontend/src/lib/websocket.ts
- [ ] Handle game score updates
- [ ] Handle player stat updates
- [ ] Handle fantasy point calculations
- [ ] Handle play-by-play events
- [ ] Error handling and recovery
```

### UI/UX Implementation

#### 1. Live Indicators
- [ ] Pulsing dot for live games
- [ ] Score change animations
- [ ] Player scoring notifications
- [ ] Quarter/time updates

#### 2. Mobile Optimization
- [ ] Compact live game cards
- [ ] Swipeable game details
- [ ] Efficient data usage
- [ ] Battery-conscious updates

## Visual Design Mockups

### Live Scoreboard Layout
```
┌─────────────────────────────────────┐
│ Live Games (3)          Auto-refresh │
├─────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐     │
│ │ LA  85  Q3  │ │ NY  72  Q3  │     │
│ │ CHI 79  7:23│ │ DAL 68  5:14│     │
│ └─────────────┘ └─────────────┘     │
│                                      │
│ ┌─────────────────────────────┐     │
│ │ SEA 44  HALF                │     │
│ │ MIN 51                      │     │
│ └─────────────────────────────┘     │
└─────────────────────────────────────┘
```

### Live Fantasy Tracker
```
┌─────────────────────────────────────┐
│ My Team: 127.5 pts (+12.5)    LIVE  │
├─────────────────────────────────────┤
│ Starting Lineup                      │
│ ┌─────────────────────────────┐     │
│ │ A. Wilson  G  │ 24.5 (+3.5) │ •   │
│ │ S. Diggins F  │ 18.0 (+2.0) │ •   │
│ │ B. Stewart F  │ 31.5 (+7.0) │ ••• │
│ └─────────────────────────────┘     │
│                                      │
│ Recent Scoring Plays                 │
│ • Stewart - 3PT made (+3.0)         │
│ • Wilson - Assist (+1.5)            │
└─────────────────────────────────────┘
```

## Performance Optimization
- [ ] Throttle updates to prevent UI janking
- [ ] Batch WebSocket messages
- [ ] Use React.memo for player cards
- [ ] Implement virtual scrolling for long lists
- [ ] Progressive data loading

## Error Handling
- [ ] Connection lost banner with retry
- [ ] Graceful degradation to polling
- [ ] Queue updates when offline
- [ ] Clear error messages
- [ ] Fallback to cached data

## Testing Requirements
- [ ] WebSocket connection tests
- [ ] Message handling tests
- [ ] Reconnection logic tests
- [ ] Component rendering tests
- [ ] Performance tests under load

## Backend Verification
- [ ] Verify WebSocket endpoints work correctly
- [ ] Test message format compatibility
- [ ] Ensure proper authentication
- [ ] Check rate limiting
- [ ] Validate data accuracy

## Documentation Updates
- [ ] WebSocket protocol documentation
- [ ] Live tracking user guide
- [ ] Troubleshooting connection issues
- [ ] Mobile app usage guide

## Accessibility
- [ ] Screen reader announcements for score changes
- [ ] Keyboard navigation for live games
- [ ] High contrast mode support
- [ ] Reduced motion options

## Future Enhancements (Post-MVP)
- Push notifications for scoring plays
- Live game audio commentary
- Picture-in-picture game tracking
- Multi-game view
- Historical play-by-play

## Definition of Done
- Live games show real-time scores
- Fantasy points update immediately
- WebSocket connection is stable
- Works on mobile devices
- No performance degradation
- All tests pass
- Documentation complete