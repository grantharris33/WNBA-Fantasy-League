# Story 5: Complete Player Analytics Frontend

**Priority**: P1 - Essential Feature
**Dependencies**: Story 1 (Integration fixes)

## Overview
The backend has comprehensive player analytics endpoints but no frontend implementation. Users need to see player trends, projections, and advanced statistics to make informed roster decisions.

## Acceptance Criteria
1. Player detail pages show advanced analytics
2. Trend charts display performance over time
3. Matchup history against teams is visible
4. Projections are displayed for upcoming games
5. Consistency scores and floor/ceiling metrics shown
6. Mobile-responsive analytics display

## Technical Tasks

### Frontend Implementation

#### 1. Create Analytics Components
```typescript
// frontend/src/components/analytics/
- [ ] PlayerAnalyticsCard.tsx - Overview of key metrics
- [ ] PerformanceTrendChart.tsx - Line chart of recent games
- [ ] MatchupHistoryTable.tsx - Performance vs each team
- [ ] ProjectionCard.tsx - Upcoming game projections
- [ ] ConsistencyMetrics.tsx - Floor/ceiling/consistency display
- [ ] AdvancedStatsTable.tsx - PER, usage rate, etc.
- [ ] PlayerComparison.tsx - Compare multiple players
```

#### 2. Update Player Detail Page
```typescript
// frontend/src/pages/PlayerDetailPage.tsx
- [ ] Add analytics tab/section
- [ ] Integrate all analytics components
- [ ] Add loading states
- [ ] Handle error states
- [ ] Add data refresh capability
```

#### 3. Create Analytics Hooks
```typescript
// frontend/src/hooks/usePlayerAnalytics.ts
- [ ] Fetch player analytics data
- [ ] Cache management
- [ ] Polling for live updates

// frontend/src/hooks/usePlayerTrends.ts
- [ ] Fetch trend data
- [ ] Data transformation for charts
```

#### 4. Add Analytics to Player Lists
```typescript
// Update player list components to show:
- [ ] Trending indicators (↑↓)
- [ ] Last 5 games average
- [ ] Consistency rating
- [ ] Projection for next game
- [ ] Quick stats popup on hover
```

### Data Visualization

#### 1. Install and Configure Chart Library
```bash
npm install recharts
```
- [ ] Configure chart theme to match app design
- [ ] Create reusable chart components
- [ ] Add responsive containers

#### 2. Implement Charts (6 hours)
- [ ] Performance trend line chart
- [ ] Stats radar chart
- [ ] Consistency box plot
- [ ] Matchup heat map
- [ ] Rolling average chart

### API Integration Updates

#### 1. Add Analytics API Functions
```typescript
// frontend/src/lib/api.ts
- [ ] getPlayerAnalytics(playerId)
- [ ] getPlayerTrends(playerId, games?)
- [ ] getPlayerProjections(playerIds[])
- [ ] getMatchupHistory(playerId)
```

#### 2. Add TypeScript Types
```typescript
// frontend/src/types/analytics.ts
interface PlayerAnalytics {
  playerId: number;
  consistency_score: number;
  ceiling: number;
  floor: number;
  trend: 'up' | 'down' | 'stable';
  per: number;
  true_shooting_pct: number;
  usage_rate: number;
  // ... etc
}
```

## UI/UX Considerations

### Desktop Layout
```
Player Detail Page
├── Basic Info Header
├── Nav Tabs [Overview | Stats | Analytics | Game Log]
└── Analytics Tab
    ├── Quick Metrics Cards (4 cards in grid)
    ├── Performance Trend Chart
    ├── Advanced Stats Table
    └── Matchup History
```

### Mobile Layout
- Stack components vertically
- Swipeable chart views
- Collapsible sections
- Simplified tables

### Visual Design
- Use team colors for player charts
- Green/red indicators for positive/negative trends
- Tooltips for metric explanations
- Loading skeletons for better UX

## Testing Requirements
- [ ] Component unit tests
- [ ] Chart rendering tests
- [ ] API integration tests
- [ ] Responsive design tests
- [ ] Performance tests with large datasets

## Documentation Updates
- [ ] Add analytics guide to help section
- [ ] Document all metrics and calculations
- [ ] Create tooltips for each analytic
- [ ] Add examples of how to use analytics

## Performance Optimization
- [ ] Implement data caching strategy
- [ ] Lazy load charts
- [ ] Virtualize long lists
- [ ] Optimize chart rendering
- [ ] Use React.memo for expensive components

## Accessibility
- [ ] Chart data available in table format
- [ ] Proper ARIA labels
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] High contrast mode support

## Future Enhancements (Post-MVP)
- Player comparison tool
- Custom date ranges
- Export analytics data
- Share analytics cards
- ML-based predictions

## Definition of Done
- All analytics data visible in UI
- Charts render correctly and responsively
- Page performance is acceptable (<3s load)
- Works on mobile devices
- All tests pass
- Documentation updated
- No console errors