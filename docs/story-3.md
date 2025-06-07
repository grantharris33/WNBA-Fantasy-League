# Story 3: Implement Waiver Wire System

**Priority**: P1 - Essential Feature
**Dependencies**: Story 1 (Integration fixes)

## Overview
Currently, players can only add/drop free agents immediately. A waiver wire system is needed to ensure fair access to dropped players and prevent instant pickup abuse.

## Acceptance Criteria
1. Dropped players enter waiver period (configurable per league)
2. Teams can submit waiver claims with priority order
3. Waiver processing runs at scheduled time (e.g., 3 AM daily)
4. Waiver priority determined by league settings (reverse standings, continual rolling, etc.)
5. UI shows waiver status and claim interface
6. Notifications sent for successful/failed claims

## Technical Tasks

### Backend Implementation

#### 1. Database Schema Updates
```sql
-- Add waiver fields to players
ALTER TABLE players ADD COLUMN waiver_expires_at TIMESTAMP;

-- Create waiver_claims table
CREATE TABLE waiver_claims (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    drop_player_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (drop_player_id) REFERENCES players(id)
);

-- Add waiver settings to leagues
ALTER TABLE leagues ADD COLUMN waiver_period_days INTEGER DEFAULT 2;
ALTER TABLE leagues ADD COLUMN waiver_type VARCHAR(20) DEFAULT 'reverse_standings';
```

#### 2. Create Waiver Service
```python
# app/services/waiver.py
- [ ] Create WaiverService class
- [ ] Implement submit_claim method
- [ ] Implement cancel_claim method
- [ ] Implement get_team_claims method
- [ ] Implement process_waivers method (for scheduled job)
- [ ] Add waiver priority calculation logic
- [ ] Handle roster size validation
```

#### 3. Create Waiver API Endpoints
```python
# app/api/waiver.py
- [ ] GET /api/v1/leagues/{league_id}/waivers - List players on waivers
- [ ] GET /api/v1/teams/{team_id}/waiver-claims - List team's claims
- [ ] POST /api/v1/teams/{team_id}/waiver-claims - Submit claim
- [ ] DELETE /api/v1/waiver-claims/{claim_id} - Cancel claim
- [ ] GET /api/v1/teams/{team_id}/waiver-priority - Get priority
```

#### 4. Create Waiver Processing Job
```python
# app/jobs/waiver_processing.py
- [ ] Create process_daily_waivers function
- [ ] Sort claims by priority
- [ ] Process claims in order
- [ ] Update rosters
- [ ] Send notifications
- [ ] Add to scheduler (3 AM daily)
```

#### 5. Update Roster Service
```python
# app/services/roster.py
- [ ] Update drop_player to set waiver_expires_at
- [ ] Update add_player to check waiver status
- [ ] Add validation for waiver claims
```

### Frontend Implementation

#### 1. Create Waiver Components
```typescript
// frontend/src/components/waiver/
- [ ] WaiverWire.tsx - Main waiver wire page
- [ ] WaiverPlayerList.tsx - List of players on waivers
- [ ] WaiverClaimModal.tsx - Submit claim interface
- [ ] MyWaiverClaims.tsx - View/manage claims
- [ ] WaiverCountdown.tsx - Time until processing
```

#### 2. Update Free Agents View
- [ ] Show waiver status for players
- [ ] Different UI for waiver vs free agent players
- [ ] Add "Claim" button for waiver players
- [ ] Show waiver expiration time

#### 3. Add Waiver Types and API Integration
```typescript
// frontend/src/types/waiver.ts
- [ ] Define WaiverClaim interface
- [ ] Define WaiverPlayer interface
- [ ] Add waiver API functions
- [ ] Add waiver status to Player type
```

## Waiver Priority Systems
```typescript
enum WaiverType {
  REVERSE_STANDINGS = "reverse_standings", // Worst team gets #1
  CONTINUAL_ROLLING = "continual_rolling", // Move to end after claim
  FAAB = "faab"                           // Free agent auction budget
}
```

## Testing Requirements
- [ ] Unit tests for waiver service logic
- [ ] Tests for priority calculation
- [ ] Tests for claim processing
- [ ] API endpoint tests
- [ ] Frontend component tests
- [ ] Integration tests for full waiver flow

## Documentation Updates
- [ ] Document waiver rules and priority systems
- [ ] API documentation for waiver endpoints
- [ ] User guide for submitting waiver claims
- [ ] Commissioner guide for waiver settings

## UI/UX Considerations
- Clear indication of waiver vs free agent status
- Countdown timer until waiver processing
- Priority order display
- Claim confirmation with drop player selection
- Success/failure notifications

## Performance Considerations
- Index on waiver_expires_at for efficient queries
- Batch processing for multiple claims
- Efficient priority calculation
- Cache waiver wire page data

## Definition of Done
- Players enter waivers when dropped
- Teams can submit and manage claims
- Waiver processing runs automatically
- Priority system works correctly
- UI clearly shows waiver status
- All tests pass