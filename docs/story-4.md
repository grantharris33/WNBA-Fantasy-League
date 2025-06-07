# Story 4: Implement Trading System

**Priority**: P1 - Essential Feature
**Effort**: 5-6 days
**Dependencies**: Story 1 (Integration fixes), Story 2 (Notifications)

## Overview
Implement a complete trading system allowing teams to propose, negotiate, and execute player trades with proper validation and league approval mechanisms.

## Acceptance Criteria
1. Teams can propose trades with multiple players on each side
2. Trade proposals can be accepted, rejected, or countered
3. Commissioner can veto trades (optional per league)
4. League can vote on trades (optional per league)
5. Trade deadline enforcement
6. Trade history and analytics
7. Notifications for all trade events

## Technical Tasks

### Backend Implementation (24 hours)

#### 1. Database Schema (2 hours)
```sql
-- Create trades table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    proposing_team_id INTEGER NOT NULL,
    receiving_team_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    proposed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,
    veto_votes INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (proposing_team_id) REFERENCES teams(id),
    FOREIGN KEY (receiving_team_id) REFERENCES teams(id)
);

-- Create trade_players table
CREATE TABLE trade_players (
    id INTEGER PRIMARY KEY,
    trade_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    from_team_id INTEGER NOT NULL,
    to_team_id INTEGER NOT NULL,
    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (from_team_id) REFERENCES teams(id),
    FOREIGN KEY (to_team_id) REFERENCES teams(id)
);

-- Create trade_votes table (for league voting)
CREATE TABLE trade_votes (
    id INTEGER PRIMARY KEY,
    trade_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    vote BOOLEAN NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE(trade_id, team_id)
);

-- Add trade settings to leagues
ALTER TABLE leagues ADD COLUMN trade_deadline DATE;
ALTER TABLE leagues ADD COLUMN trade_review_period_hours INTEGER DEFAULT 48;
ALTER TABLE leagues ADD COLUMN trade_approval_type VARCHAR(20) DEFAULT 'none';
ALTER TABLE leagues ADD COLUMN trade_veto_threshold INTEGER DEFAULT 4;
```

#### 2. Create Trade Service (10 hours)
```python
# app/services/trade.py
class TradeService:
    - [ ] propose_trade(proposing_team_id, receiving_team_id, give_players, receive_players)
    - [ ] accept_trade(trade_id, team_id)
    - [ ] reject_trade(trade_id, team_id)
    - [ ] counter_trade(trade_id, team_id, new_give_players, new_receive_players)
    - [ ] cancel_trade(trade_id, team_id)
    - [ ] veto_trade(trade_id, user_id) # Commissioner only
    - [ ] vote_on_trade(trade_id, team_id, approve: bool)
    - [ ] process_trade(trade_id) # Execute the trade
    - [ ] validate_trade(trade) # Check roster limits, positions, etc.
    - [ ] get_trade_impact(trade_id) # Analytics on trade fairness
    - [ ] check_trade_deadline(league_id)
```

#### 3. Create Trade API Endpoints (6 hours)
```python
# app/api/trades.py
- [ ] GET /api/v1/leagues/{league_id}/trades - List league trades
- [ ] GET /api/v1/teams/{team_id}/trades - List team trades
- [ ] GET /api/v1/trades/{trade_id} - Get trade details
- [ ] POST /api/v1/trades - Propose new trade
- [ ] PUT /api/v1/trades/{trade_id}/accept - Accept trade
- [ ] PUT /api/v1/trades/{trade_id}/reject - Reject trade
- [ ] POST /api/v1/trades/{trade_id}/counter - Counter trade
- [ ] DELETE /api/v1/trades/{trade_id} - Cancel trade
- [ ] PUT /api/v1/trades/{trade_id}/veto - Commissioner veto
- [ ] POST /api/v1/trades/{trade_id}/vote - Vote on trade
- [ ] GET /api/v1/trades/{trade_id}/analysis - Trade fairness analysis
```

#### 4. Create Trade Processing Job (3 hours)
```python
# app/jobs/trade_processing.py
- [ ] check_expired_trades() - Cancel expired trades
- [ ] check_trade_approvals() - Process approved trades
- [ ] check_trade_deadline() - Disable trading after deadline
```

#### 5. Add Trade Validation (3 hours)
```python
# Validation rules:
- [ ] Both teams must have roster space
- [ ] Cannot exceed position limits
- [ ] Cannot trade injured reserve players (optional)
- [ ] Must be before trade deadline
- [ ] Cannot trade with eliminated teams (playoffs)
- [ ] Validate trade fairness (optional warning)
```

### Frontend Implementation (20 hours)

#### 1. Create Trade Components (12 hours)
```typescript
// frontend/src/components/trades/
- [ ] TradeCenter.tsx - Main trade interface
- [ ] ProposeTradeModal.tsx - Create new trade proposal
- [ ] TradeProposalCard.tsx - Display trade details
- [ ] TradeHistory.tsx - Past trades list
- [ ] TradeAnalysis.tsx - Trade fairness metrics
- [ ] MyTrades.tsx - Active trades for team
- [ ] TradePlayerSelector.tsx - Select players for trade
```

#### 2. Create Trade Pages (4 hours)
```typescript
// frontend/src/pages/
- [ ] TradeCenterPage.tsx - Browse and propose trades
- [ ] TradeDetailPage.tsx - View specific trade
```

#### 3. Add Trade State Management (4 hours)
```typescript
// frontend/src/hooks/useTrades.ts
- [ ] Fetch and cache trades
- [ ] Optimistic updates
- [ ] Real-time trade notifications

// frontend/src/types/trade.ts
- [ ] Trade interfaces
- [ ] TradeStatus enum
- [ ] TradePlayer type
```

## Trade Flow Diagrams

### Basic Trade Flow
```
Team A proposes → Team B reviews → Accept/Reject/Counter
                                    ↓
                              Trade Executes
```

### League Approval Flow
```
Team A proposes → Team B accepts → League Review Period
                                    ↓
                              Votes/Veto Check
                                    ↓
                              Trade Executes
```

## Testing Requirements
- [ ] Unit tests for trade validation logic
- [ ] Integration tests for trade execution
- [ ] Test all trade status transitions
- [ ] Test roster limit enforcement
- [ ] Test trade deadline enforcement
- [ ] API endpoint tests
- [ ] Frontend component tests

## Documentation Updates
- [ ] Trade system user guide
- [ ] API documentation
- [ ] Commissioner guide for trade settings
- [ ] Trade strategy guide

## Performance Considerations
- Efficient queries for trade history
- Caching for trade analysis
- Real-time updates via WebSocket
- Pagination for trade lists

## Future Enhancements (Post-MVP)
- Three-team trades
- Draft pick trading (for keeper leagues)
- Trade finder/suggestion engine
- Advanced analytics and projections
- Trade impact on playoff chances

## Definition of Done
- Full trade lifecycle works end-to-end
- All validation rules enforced
- Notifications sent for all trade events
- Trade history properly maintained
- UI intuitive and responsive
- All tests pass
- Documentation complete