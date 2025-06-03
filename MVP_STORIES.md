# WNBA Fantasy League MVP Release - User Stories

## Story 1: Weekly Starter-Only Scoring System

### Overview
Currently, the fantasy scoring system credits teams with points from all players on their roster. We need to implement a weekly lineup system where only designated starters count toward team scores, and past weeks' lineups become locked to preserve scoring integrity.

### Current State Analysis
- The `app/services/scoring.py` file contains `update_weekly_team_scores()` which currently uses all `RosterSlot` records
- The `RosterSlot` model already has an `is_starter` boolean field
- There's a weekly moves system with `Team.moves_this_week` counter
- The frontend (`frontend/src/components/roster/RosterView.tsx`) already displays starters vs bench

### Technical Requirements

#### Backend Changes
1. **Create Weekly Lineup History Model**
   ```python
   class WeeklyLineup(Base):
       __tablename__ = "weekly_lineup"
       __table_args__ = (UniqueConstraint("team_id", "week_id", "player_id"),)

       id: int = Column(Integer, primary_key=True)
       team_id: int = Column(Integer, ForeignKey("team.id"))
       player_id: int = Column(Integer, ForeignKey("player.id"))
       week_id: int = Column(Integer)
       is_starter: bool = Column(Boolean)
       locked_at: datetime = Column(DateTime)
   ```

2. **Modify Scoring Service**
   - Update `update_weekly_team_scores()` in `app/services/scoring.py` to only count starters from `WeeklyLineup` table
   - Create function to lock lineups every Monday at 12:01 AM
   - Modify the scoring logic to use historical lineup data instead of current roster state

3. **Create Lineup Service**
   ```python
   class LineupService:
       def lock_weekly_lineups(self, week_id: int)
       def can_modify_lineup(self, team_id: int, week_id: int) -> bool
       def set_weekly_starters(self, team_id: int, week_id: int, starter_ids: List[int])
       def get_weekly_lineup(self, team_id: int, week_id: int)
   ```

4. **API Endpoints**
   - `POST /api/v1/teams/{team_id}/lineups/{week_id}/starters` - Set starters for specific week
   - `GET /api/v1/teams/{team_id}/lineups/{week_id}` - Get lineup for specific week
   - `GET /api/v1/teams/{team_id}/lineups/history` - Get all historical lineups

5. **Weekly Job**
   - Create scheduled job to automatically lock lineups every Monday
   - Copy current starter status to `WeeklyLineup` table when locking

#### Frontend Changes
1. **Weekly Lineup Interface**
   - Modify `RosterView.tsx` to show current week vs historical weeks
   - Add week selector dropdown
   - Show lock status for each week
   - Disable starter changes for locked weeks

2. **Lineup History View**
   - Create `LineupHistory.tsx` component
   - Show lineup for each week with lock timestamps
   - Display scoring breakdown by week

### Acceptance Criteria
- [ ] Users can set starters for the current and future weeks only
- [ ] Lineups automatically lock every Monday at 12:01 AM
- [ ] Scoring only counts points from players who were starters during that specific week
- [ ] Users can view their historical lineups but cannot modify them
- [ ] Current week lineup changes still count against the 3-move weekly limit

---

## Story 2: Admin Roster Management and Score Recalculation

### Overview
Admins need the ability to modify any team's roster for previous weeks and trigger score recalculation. This is essential for mid-season adjustments due to injuries or data corrections.

### Current State Analysis
- `User` model has `is_admin` field
- Current roster management is in `app/services/roster.py`
- Scoring recalculation exists in `app/services/scoring.py`

### Technical Requirements

#### Backend Changes
1. **Admin Service**
   ```python
   class AdminService:
       def modify_historical_lineup(self, team_id: int, week_id: int, changes: Dict)
       def recalculate_team_week_score(self, team_id: int, week_id: int)
       def override_weekly_moves(self, team_id: int, additional_moves: int)
       def get_admin_audit_log(self, team_id: int = None)
   ```

2. **Enhanced Transaction Logging**
   - Extend `TransactionLog` model to include admin actions
   - Log all admin roster modifications with justification field
   - Track before/after states for audit trails

3. **Admin API Endpoints**
   - `PUT /api/v1/admin/teams/{team_id}/lineups/{week_id}` - Modify historical lineup
   - `POST /api/v1/admin/teams/{team_id}/weeks/{week_id}/recalculate` - Recalculate scores
   - `POST /api/v1/admin/teams/{team_id}/moves/grant` - Grant additional weekly moves
   - `GET /api/v1/admin/audit-log` - Get admin action history

4. **Permission Middleware**
   - Create `require_admin` dependency for admin endpoints
   - Validate admin status in JWT token

#### Frontend Changes
1. **Admin Dashboard**
   - Create `AdminDashboard.tsx` component
   - Team roster management interface
   - Week-by-week lineup editor
   - Score recalculation buttons

2. **Admin Controls in Roster View**
   - Add admin-only controls to existing roster components
   - "Edit Historical Lineup" buttons for admins
   - "Recalculate Scores" action buttons

3. **Audit Log Viewer**
   - Create `AuditLog.tsx` component
   - Display all admin actions with timestamps
   - Filter by team, admin user, and date range

### Acceptance Criteria
- [ ] Only users with `is_admin=True` can access admin endpoints
- [ ] Admins can modify any team's lineup for any week
- [ ] Score recalculation automatically updates `TeamScore` table
- [ ] All admin actions are logged with user ID and timestamp
- [ ] Admins can grant additional weekly moves to any team
- [ ] Frontend shows clear indication when viewing admin-modified data

---

## Story 3: Enhanced Admin Capabilities for Weekly Move Overrides

### Overview
Admins need the ability to set team rosters even when users have exhausted their 3 weekly moves, providing flexibility for exceptional circumstances.

### Current State Analysis
- Weekly moves logic exists in `app/services/roster.py` in `set_starters()` method
- Current validation prevents setting starters when `moves_this_week >= 3`

### Technical Requirements

#### Backend Changes
1. **Extend RosterService**
   ```python
   def set_starters_admin_override(
       self,
       team_id: int,
       starter_player_ids: List[int],
       admin_user_id: int,
       bypass_move_limit: bool = True
   )
   ```

2. **Admin Move Bank System**
   ```python
   class AdminMoveGrant(Base):
       __tablename__ = "admin_move_grant"

       id: int = Column(Integer, primary_key=True)
       team_id: int = Column(Integer, ForeignKey("team.id"))
       admin_user_id: int = Column(Integer, ForeignKey("user.id"))
       moves_granted: int = Column(Integer)
       reason: str = Column(String)
       granted_at: datetime = Column(DateTime)
       week_id: int = Column(Integer)
   ```

3. **Enhanced Move Validation**
   - Modify move validation to check for admin grants
   - Calculate total available moves (3 + admin grants - used moves)
   - Log admin override usage separately from normal moves

4. **API Endpoints**
   - `POST /api/v1/admin/teams/{team_id}/moves/grant` - Grant emergency moves
   - `POST /api/v1/admin/teams/{team_id}/roster/force-set` - Force set roster bypassing limits
   - `GET /api/v1/admin/teams/{team_id}/moves/history` - View move grant history

#### Frontend Changes
1. **Admin Move Management**
   - Add "Grant Emergency Moves" modal in admin dashboard
   - Reason field for move grants
   - Display remaining moves including admin grants

2. **Enhanced Roster Management**
   - Show admin-granted moves separately from weekly moves
   - "Force Set Roster" button for admins
   - Warning messages when using admin overrides

### Acceptance Criteria
- [ ] Admins can grant additional moves to any team with reason tracking
- [ ] Admin-granted moves are tracked separately from normal weekly moves
- [ ] Users can see total available moves (normal + admin granted)
- [ ] All admin move grants are logged for audit purposes
- [ ] Frontend clearly indicates when admin overrides are being used

---

## Story 4: Production Deployment Setup with Hetzner VPS

### Overview
Create a comprehensive deployment setup for a Hetzner VPS running Ubuntu 24.04 with Docker containers, Portainer for management, and Traefik for reverse proxy with Cloudflare DNS.

### Technical Requirements

#### Infrastructure Setup
1. **Docker Compose Configuration**
   ```yaml
   # docker-compose.prod.yml
   services:
     app:
       build: .
       environment:
         - DATABASE_URL=sqlite:///data/prod.db
         - FRONTEND_URL=https://fantasy.yourdomain.com

     frontend:
       build: ./frontend

     traefik:
       image: traefik:v2.10

     portainer:
       image: portainer/portainer-ce:latest
   ```

2. **Traefik Configuration**
   - SSL certificate management with Let's Encrypt
   - Cloudflare DNS integration for domain management
   - Route configuration for app and frontend services

3. **Database Setup Script**
   ```bash
   #!/bin/bash
   # setup-prod-db.sh
   # Creates production SQLite database with initial data
   ```

4. **User Seeding Script**
   ```python
   # Create 4 users: 1 admin, 3 regular users
   # Generate sample leagues and teams for testing
   ```

#### Deployment Files Structure
```
ops/
├── docker/
│   ├── Dockerfile.app
│   ├── Dockerfile.frontend
│   └── docker-compose.prod.yml
├── traefik/
│   ├── traefik.yml
│   └── dynamic/
├── scripts/
│   ├── setup-prod-db.sh
│   ├── seed-users.py
│   ├── deploy.sh
│   └── backup-db.sh
├── cloudflare/
│   └── dns-config.json
└── README.md
```

#### Setup Documentation
1. **Complete Setup Guide**
   - Hetzner VPS provisioning steps
   - Ubuntu 24.04 configuration
   - Docker and Docker Compose installation
   - Cloudflare DNS setup
   - SSL certificate configuration
   - Environment variable configuration

2. **Maintenance Scripts**
   - Database backup automation
   - Log rotation setup
   - Health check monitoring
   - Update deployment scripts

### Acceptance Criteria
- [ ] Complete Docker containerization of app and frontend
- [ ] Traefik reverse proxy with SSL termination
- [ ] Portainer for container management
- [ ] Automated database setup with seeded data
- [ ] Cloudflare DNS integration
- [ ] Comprehensive setup documentation
- [ ] Backup and maintenance scripts

---

## Story 5: 2025 Season Data Backfill

### Overview
Create a comprehensive data backfill system that ingests all WNBA 2025 season data including games, player stats, team information, and standings to date.

### Current State Analysis
- Ingestion system exists in `app/ingest/` directory
- Models exist for games, players, stats, and standings
- `IngestionRun` and `IngestionQueue` models track ingestion progress

### Technical Requirements

#### Backend Changes
1. **Enhanced Backfill Service**
   ```python
   class SeasonBackfillService:
       def backfill_full_season(self, season: int = 2025)
       def backfill_date_range(self, start_date: date, end_date: date)
       def verify_data_completeness(self, season: int)
       def generate_backfill_report(self)
   ```

2. **Data Validation and Cleanup**
   - Verify all games have complete stat lines
   - Check for missing player data
   - Validate team standings consistency
   - Flag incomplete or suspicious data

3. **CLI Commands**
   ```bash
   poetry run python -m app.cli backfill-season --year=2025
   poetry run python -m app.cli verify-season-data --year=2025
   poetry run python -m app.cli generate-sample-leagues
   ```

4. **Progress Tracking**
   - Enhanced `IngestionRun` logging
   - Real-time progress updates
   - Error reporting and retry mechanisms
   - Data completeness metrics

#### Data Sources Integration
1. **Multiple API Sources**
   - Primary WNBA API integration
   - Backup data sources for redundancy
   - ESPN API for additional player data
   - Official WNBA standings

2. **Data Enrichment**
   - Player biographical information
   - Team logo and color data
   - Venue information
   - Historical matchup data

#### Seeding and Sample Data
1. **Production Database Initialization**
   ```python
   # seed_production_data.py
   def create_admin_user()
   def create_sample_users()
   def create_sample_leagues()
   def assign_sample_rosters()
   ```

2. **Fantasy League Setup**
   - Create sample leagues with different configurations
   - Assign realistic rosters to teams
   - Generate historical lineup data
   - Calculate retrospective scores

### Acceptance Criteria
- [ ] Complete 2025 season data ingestion (games, stats, standings)
- [ ] All player biographical data populated
- [ ] Sample leagues created with realistic rosters
- [ ] Historical score calculation for all completed weeks
- [ ] Data validation and completeness verification
- [ ] CLI tools for ongoing data management
- [ ] Comprehensive backfill logging and error handling

---

## Story 6: Frontend Integration of All Backend Features

### Overview
Implement comprehensive frontend components to display and interact with all the new backend data and functionality.

### Current State Analysis
- React frontend in `frontend/src/`
- Existing components for roster management, draft, and dashboard
- TypeScript types defined in `frontend/src/types/`

### Technical Requirements

#### Component Development
1. **Enhanced Dashboard**
   ```typescript
   // components/dashboard/EnhancedDashboard.tsx
   // - Weekly lineup status
   // - Historical performance charts
   // - League standings with complete data
   ```

2. **Weekly Lineup Management**
   ```typescript
   // components/roster/WeeklyLineupManager.tsx
   // - Week selector with lock status
   // - Starter/bench assignment for current week
   // - Historical lineup viewer
   ```

3. **Admin Interface**
   ```typescript
   // components/admin/AdminPanel.tsx
   // - Team roster management across all weeks
   // - Score recalculation controls
   // - Move grant interface
   // - Audit log viewer
   ```

4. **Data Visualization**
   ```typescript
   // components/analytics/PerformanceCharts.tsx
   // - Player performance trends
   // - Team scoring history
   // - League-wide statistics
   ```

#### API Integration
1. **Enhanced API Service**
   ```typescript
   // services/api.ts
   // Add endpoints for:
   // - Weekly lineup management
   // - Admin functions
   // - Historical data retrieval
   // - Analytics endpoints
   ```

2. **Real-time Updates**
   - WebSocket integration for live scoring
   - Auto-refresh for current week lineups
   - Push notifications for important events

3. **Error Handling and Loading States**
   - Comprehensive error boundaries
   - Loading skeletons for all data fetching
   - Retry mechanisms for failed requests

#### User Experience Enhancements
1. **Navigation Improvements**
   - Add admin menu for admin users
   - Week-based navigation for historical data
   - Quick access to current week lineup

2. **Mobile Responsiveness**
   - Optimize all new components for mobile
   - Touch-friendly admin controls
   - Responsive data tables

3. **Performance Optimization**
   - Lazy loading for historical data
   - Memoization of expensive calculations
   - Efficient state management

### Acceptance Criteria
- [ ] All backend features accessible through frontend
- [ ] Admin interface for roster and scoring management
- [ ] Weekly lineup management with lock indicators
- [ ] Historical data visualization and charts
- [ ] Mobile-responsive design for all new features
- [ ] Real-time updates and notifications
- [ ] Comprehensive error handling and loading states

---

## Story 7: Enhanced Analytics and Reporting System

### Overview
Implement comprehensive analytics for player performance, team trends, and league-wide statistics to provide deeper insights for fantasy managers.

### Technical Requirements

#### Backend Analytics Engine
1. **Advanced Analytics Service**
   ```python
   class AdvancedAnalyticsService:
       def calculate_player_trends(self, player_id: int, weeks: int = 4)
       def generate_matchup_analysis(self, team1_id: int, team2_id: int)
       def calculate_league_averages(self, week_id: int)
       def predict_player_performance(self, player_id: int)
   ```

2. **Performance Metrics**
   - Player consistency ratings
   - Ceiling/floor calculations
   - Matchup-based projections
   - Usage rate trending

3. **Team Analytics**
   - Roster construction analysis
   - Starting lineup optimization suggestions
   - Weekly performance variance
   - Season-long trends

#### Data Models
1. **Player Analytics**
   ```python
   class PlayerAnalytics(Base):
       __tablename__ = "player_analytics"

       player_id: int
       week_id: int
       consistency_score: float
       usage_rate: float
       matchup_difficulty: float
       projected_points: float
   ```

2. **League Analytics**
   - Weekly league averages
   - Position scarcity metrics
   - Waiver wire values

#### API Endpoints
- `GET /api/v1/analytics/players/{player_id}/trends`
- `GET /api/v1/analytics/teams/{team_id}/optimization`
- `GET /api/v1/analytics/league/weekly-summary`
- `GET /api/v1/analytics/matchups/{team1_id}/vs/{team2_id}`

### Acceptance Criteria
- [ ] Player performance trend analysis
- [ ] Team optimization recommendations
- [ ] League-wide statistical summaries
- [ ] Matchup analysis and projections
- [ ] Historical performance comparisons

---

## Story 8: Notification and Communication System

### Overview
Implement a notification system to keep users informed about lineup deadlines, scoring updates, and important league events.

### Technical Requirements

#### Notification Service
1. **Backend Notification Engine**
   ```python
   class NotificationService:
       def send_lineup_deadline_reminder(self, team_id: int)
       def notify_score_update(self, team_id: int, week_id: int)
       def send_admin_action_notification(self, team_id: int, action: str)
   ```

2. **Notification Types**
   - Lineup deadline reminders (24h, 2h before lock)
   - Weekly score calculations complete
   - Admin roster modifications
   - League announcements

3. **Delivery Channels**
   - In-app notifications
   - Email notifications (optional)
   - Push notifications (future enhancement)

#### Frontend Integration
1. **Notification Center**
   ```typescript
   // components/notifications/NotificationCenter.tsx
   // - Unread notification badge
   // - Notification history
   // - Preference settings
   ```

2. **Real-time Updates**
   - WebSocket-based notification delivery
   - Toast notifications for immediate alerts
   - Badge counters for unread notifications

### Acceptance Criteria
- [ ] Automated lineup deadline reminders
- [ ] Score update notifications
- [ ] Admin action notifications
- [ ] In-app notification center
- [ ] Email notification support

---

## Implementation Priority and Dependencies

### Phase 1 (Core MVP Features)
1. Story 1: Weekly Starter-Only Scoring System
2. Story 2: Admin Roster Management and Score Recalculation

### Phase 2 (Enhanced Features)
3. Story 3: Enhanced Admin Capabilities for Weekly Move Overrides
4. Story 6: Frontend Integration of All Backend Features

### Phase 3 (Deployment and Data)
5. Story 4: Production Deployment Setup with Hetzner VPS
6. Story 5: 2025 Season Data Backfill

### Phase 4 (Advanced Features)
7. Story 7: Enhanced Analytics and Reporting System
8. Story 8: Notification and Communication System

### Technical Notes for Implementation Teams

#### Database Migration Strategy
- All new models should include Alembic migrations
- Existing data preservation during schema changes
- Rollback procedures for each migration

#### Testing Requirements
- Unit tests for all new service classes
- Integration tests for API endpoints
- Frontend component testing with React Testing Library
- End-to-end testing for critical user flows

#### Security Considerations
- Admin endpoint authentication and authorization
- Input validation for all admin functions
- Audit logging for sensitive operations
- Rate limiting for admin actions

#### Performance Considerations
- Database indexing for new queries
- Caching strategies for analytics data
- Lazy loading for historical data
- Background job optimization

Each story includes complete context about the current system state, technical requirements, and acceptance criteria to ensure successful implementation by development teams.