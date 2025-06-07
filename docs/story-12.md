# Story 12: Performance Optimization and Caching

**Priority**: P2 - Important
**Dependencies**: Story 1 (Integration fixes)

## Overview
The application has performance issues including N+1 queries, lack of caching, large bundle sizes, and slow API responses. These issues will become critical as user load increases.

## Acceptance Criteria
1. API response times <200ms for list endpoints
2. No N+1 query problems in critical paths
3. Effective caching reduces database load by 50%
4. Frontend bundle <500KB gzipped
5. Lighthouse performance score >90

## Technical Tasks

### Backend Performance
#### 1. Fix N+1 Query Problems
```python
# Identify and fix N+1 queries in:
- [ ] League standings calculation
- [ ] Roster with players listing
- [ ] Team scores with player stats
- [ ] Draft state with picks
- [ ] Weekly lineups with players

# Example fix:
# Before:
teams = db.query(Team).filter_by(league_id=league_id).all()
for team in teams:
    team.players  # N+1 query

# After:
from sqlalchemy.orm import joinedload
teams = db.query(Team)\
    .options(joinedload(Team.roster_slots).joinedload(RosterSlot.player))\
    .filter_by(league_id=league_id).all()
```

#### 2. Implement Caching Layer
```python
# app/services/cache.py improvements
- [ ] Add Redis caching (fallback to in-memory)
- [ ] Cache key strategies
- [ ] Cache invalidation logic
- [ ] Cache warming for hot paths

# Cache these endpoints:
- [ ] GET /api/v1/players (5 min TTL)
- [ ] GET /api/v1/leagues/{id}/standings (1 min TTL)
- [ ] GET /api/v1/wnba/teams (1 hour TTL)
- [ ] GET /api/v1/scores/current (30 sec TTL)
- [ ] GET /api/v1/lookup/* (5 min TTL)
```

#### 3. Database Optimization
```sql
-- Add missing indexes
CREATE INDEX idx_roster_slots_team_player ON roster_slots(team_id, player_id);
CREATE INDEX idx_stat_lines_player_date ON stat_lines(player_id, game_date DESC);
CREATE INDEX idx_team_scores_week ON team_scores(team_id, week DESC);
CREATE INDEX idx_draft_picks_draft_round ON draft_picks(draft_id, round, pick_number);
CREATE INDEX idx_players_active ON players(is_active) WHERE is_active = true;

-- Optimize slow queries
- [ ] Standings calculation query
- [ ] Free agents query
- [ ] Player stats aggregation
```

### Frontend Performance

#### 1. Bundle Optimization
```typescript
// vite.config.ts
- [ ] Enable code splitting by route
- [ ] Configure chunk size limits
- [ ] Optimize dependencies

// Lazy load heavy components
- [ ] Chart libraries (recharts)
- [ ] Draft room components
- [ ] Admin dashboard

// Tree shake unused code
- [ ] Remove unused imports
- [ ] Eliminate dead code
```

#### 2. Component Optimization
```typescript
// Add React performance optimizations
- [ ] Use React.memo for expensive components
- [ ] Implement useMemo for calculations
- [ ] Use useCallback for event handlers
- [ ] Virtualize long lists

// Example:
const PlayerList = React.memo(({ players }) => {
  const sortedPlayers = useMemo(
    () => players.sort((a, b) => b.fantasy_ppg - a.fantasy_ppg),
    [players]
  );
  // ...
});
```

#### 3. API Call Optimization
```typescript
// frontend/src/hooks/useApi.ts
- [ ] Implement request deduplication
- [ ] Add response caching
- [ ] Batch API requests
- [ ] Implement stale-while-revalidate

// Use React Query or SWR
npm install @tanstack/react-query

// Example:
const { data, isLoading } = useQuery({
  queryKey: ['players', leagueId],
  queryFn: () => api.getPlayers(leagueId),
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
});
```

### Infrastructure Optimization

#### 1. Add CDN Support
```nginx
# nginx.conf
- [ ] Configure cache headers for static assets
- [ ] Enable gzip compression
- [ ] Set up CDN for images/assets
```

#### 2. Add Response Compression
```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Performance Metrics

### Target Metrics
```yaml
Backend:
  - List endpoints: <200ms
  - Detail endpoints: <100ms
  - Search endpoints: <500ms
  - Draft operations: <100ms

Frontend:
  - First Contentful Paint: <1.5s
  - Time to Interactive: <3.5s
  - Largest Contentful Paint: <2.5s
  - Cumulative Layout Shift: <0.1

Bundle:
  - Initial JS: <200KB
  - Initial CSS: <50KB
  - Total size: <500KB gzipped
```

### Monitoring
```python
# app/core/monitoring.py
- [ ] Add performance timing middleware
- [ ] Log slow queries
- [ ] Track cache hit rates
- [ ] Monitor memory usage
```

## Caching Strategy

### Cache Levels
1. **Browser Cache**: Static assets (1 year)
2. **CDN Cache**: Images, CSS, JS (1 day)
3. **Application Cache**: API responses (varied TTL)
4. **Database Cache**: Query results (5 minutes)

### Cache Keys
```python
def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate consistent cache keys"""
    parts = [prefix]
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}:{v}")
    return ":".join(parts)

# Examples:
# "players:league:123:free_agents:true"
# "standings:league:456:week:5"
```

## Testing Requirements
- [ ] Load testing with 100 concurrent users
- [ ] Performance regression tests
- [ ] Cache invalidation tests
- [ ] Bundle size monitoring
- [ ] Database query profiling

## Definition of Done
- API response times meet targets
- No N+1 queries in critical paths
- Cache hit rate >50%
- Bundle size <500KB
- Lighthouse score >90
- Load tests pass
- No performance regressions