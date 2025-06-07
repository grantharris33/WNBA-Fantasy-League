# CLAUDE.md - LLM Developer Guide

This file provides comprehensive guidance for LLM instances working on the WNBA Fantasy League codebase. Follow these instructions to maintain code quality, architectural patterns, and project consistency.

## Project Overview

This is a production-ready WNBA Fantasy League application built with modern web technologies. The system provides:

- **Full Fantasy League Management**: User registration, league creation, team management
- **Real-time Draft System**: WebSocket-powered live drafts with timer and auto-pick functionality
- **Automated Data Pipeline**: Nightly ingestion of WNBA statistics from RapidAPI
- **Comprehensive Scoring**: Fantasy point calculations with bonuses and historical tracking
- **Admin Dashboard**: Complete system monitoring, data quality checks, and manual controls
- **Live Game Tracking**: Real-time game updates and fantasy score calculations
- **Analytics Engine**: Player performance analytics, projections, and trend analysis

### Technology Stack
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy ORM, APScheduler, WebSockets
- **Frontend**: React 18 + TypeScript, Vite, TailwindCSS, React Context
- **Database**: SQLite (development), PostgreSQL (production)
- **External APIs**: RapidAPI (WNBA statistics)
- **DevOps**: Docker, Traefik, Cloudflare, Hetzner VPS deployment

## Development Commands & Workflow

### Backend (Python/FastAPI)
```bash
# ALWAYS use poetry run for Python commands
make dev                    # Start development server with auto-reload
make test                   # Run comprehensive pytest suite
make lint                   # Run ruff, isort, black checks
make format                 # Auto-format code with black and isort

# Database operations
poetry run alembic upgrade head                    # Apply migrations
poetry run alembic revision --autogenerate -m ""   # Create new migration
poetry run python scripts/seed_demo.py             # Seed demo data
poetry run python scripts/seed_mvp.py --force      # Seed MVP data
poetry run python scripts/seed_mvp_real_data.py    # Seed with real WNBA data

# CLI admin commands
poetry run python -m app.cli.main                  # Access CLI interface
poetry run python -m app.cli.admin                 # Admin-specific commands

# Manual job execution
poetry run python -c "from app.jobs.ingest import ingest_stat_lines; import asyncio; asyncio.run(ingest_stat_lines())"
poetry run python -c "from app.jobs.score_engine import update_weekly_team_scores; update_weekly_team_scores()"
```

### Frontend (React/TypeScript)
```bash
# ALWAYS cd frontend before running npm commands
cd frontend
npm run dev                 # Start Vite dev server (localhost:5173)
npm run build              # Production build with type checking
npm run lint               # ESLint checking with TypeScript rules
npm run preview            # Preview production build
```

### Quick Start Commands
```bash
# Full development setup
make dev &                  # Start backend
cd frontend && npm run dev  # Start frontend (new terminal)

# MVP Docker setup
./start-mvp.sh             # Complete MVP environment

# Production deployment
./scripts/deploy.sh production
```

## Development Principles

- Always run the full pytest suite and linters/formatters before pushing a commit

## Architecture & Code Organization

### Backend Structure (Layered Architecture)
- **`app/api/`**: FastAPI routers organized by domain
  - `auth.py`: Authentication endpoints
  - `admin.py`: Admin-only operations
  - `analytics.py`: Player analytics and projections
  - `draft.py`: Live draft management
  - `endpoints_v1.py`: Core league/team/roster endpoints
  - `live_games.py`: Real-time game tracking
  - `wnba.py`: WNBA data endpoints
  - `deps.py`: Dependency injection (get_current_user, get_db)
  - `schemas.py`: Pydantic request/response models

- **`app/services/`**: Business logic layer (CRITICAL: Always implement logic here first)
  - `admin.py`: Admin operations and audit logging
  - `analytics.py`: Player performance analytics
  - `draft.py`: Draft state management and validation
  - `league.py`: League management operations
  - `lineup.py`: Lineup and starter management
  - `roster.py`: Roster operations and move validation
  - `scoring.py`: Fantasy point calculations
  - `team.py`: Team management
  - `wnba.py`: WNBA data processing

- **`app/models/`**: SQLAlchemy ORM models with comprehensive relationships
  - Models defined in `__init__.py` with proper relationships
  - Analytics models in `analytics.py`
  - User profile models in `user_profile.py`

- **`app/jobs/`**: Scheduled background tasks using APScheduler
  - `ingest.py`: Nightly WNBA data ingestion
  - `score_engine.py`: Fantasy score calculations
  - `bonus_calc.py`: Weekly bonus calculations
  - `draft_clock.py`: Draft timer management
  - `live_game_updates.py`: Real-time game tracking
  - `analytics_job.py`: Player analytics calculations

- **`app/core/`**: Core utilities and configuration
  - `config.py`: Environment configuration
  - `database.py`: Database session management
  - `security.py`: Authentication and password handling
  - `ws_manager.py`: WebSocket connection management
  - `scheduler.py`: APScheduler configuration
  - `middleware.py`: Request/response middleware

- **`app/external_apis/`**: External service clients
  - `rapidapi_client.py`: RapidAPI WNBA data client

### Frontend Structure (Component-Based Architecture)
- **`frontend/src/components/`**: Organized by feature domain
  - `common/`: Reusable UI components (LoadingSpinner, ErrorMessage, etc.)
  - `dashboard/`: Dashboard-specific components (StandingsTable, LeagueTeamCard, etc.)
  - `draft/`: Draft room components (PlayerList, DraftTimer, etc.)
  - `roster/`: Roster management components
  - `games/`: Live game tracking components
  - `layout/`: Layout components (NavBar, DashboardLayout, etc.)

- **`frontend/src/pages/`**: Route-based page components
  - Each page corresponds to a major application route
  - Keep pages thin - delegate to components

- **`frontend/src/contexts/`**: React Context for global state
  - `AuthContext.tsx`: User authentication state
  - `ThemeContext.tsx`: UI theme management

- **`frontend/src/types/`**: TypeScript definitions
  - Mirror backend Pydantic schemas
  - Keep synchronized with API changes

- **`frontend/src/hooks/`**: Custom React hooks
  - `useDraftWebSocket.ts`: Draft real-time updates

- **`frontend/src/services/`**: API client services
  - `adminApi.ts`: Admin-specific API calls

### Key Data Models & Relationships
- **Core Hierarchy**: User → League → Team → RosterSlot → Player
- **Draft System**: DraftState → DraftPick (with WebSocket updates)
- **Scoring System**: StatLine → TeamScore → WeeklyLineup
- **Analytics**: AdvancedPlayerStats, PlayerTrends, ProjectedStats
- **Admin & Audit**: TransactionLog, IngestLog, AdminMove
- **Real-time**: LiveGameData, LiveFantasyScore

## Development Patterns & Best Practices

### CRITICAL: Service-First Development Pattern
1. **ALWAYS implement business logic in `app/services/` FIRST**
2. Services handle all business rules, validation, and database operations
3. API endpoints are thin wrappers that call service methods
4. Services are testable and reusable across different contexts

### API Development Workflow
1. **Service Layer**: Implement business logic in appropriate service class
2. **API Endpoint**: Create thin endpoint that calls service method
3. **Schemas**: Define Pydantic models for request/response in `schemas.py`
4. **Error Handling**: Use HTTPException in API layer, custom exceptions in services
5. **OpenAPI Documentation**: Add clear descriptions and examples
6. **Testing**: Write comprehensive tests for both service and endpoint

### Database Development Pattern
1. **Model Changes**: Modify SQLAlchemy models in `app/models/`
2. **Migration Generation**: `poetry run alembic revision --autogenerate -m "description"`
3. **Migration Review**: Always review generated migration before applying
4. **Migration Apply**: `poetry run alembic upgrade head`
5. **Service Updates**: Update related service methods
6. **Test Updates**: Ensure tests cover new model behavior

### Frontend Development Standards
1. **TypeScript Strict Mode**: No `any` types, strict null checks enabled
2. **Component Organization**: Group by feature domain, not by type
3. **State Management**: Use React Context for global state, local state for component-specific
4. **API Integration**: Use typed API client with proper error handling
5. **Performance**: Use React.memo, useMemo, useCallback where appropriate
6. **Styling**: TailwindCSS utility classes, consistent design system

### Testing Requirements
- **Backend**: Comprehensive pytest suite with >90% coverage target
  - Test both success and failure paths
  - Use fixtures for database setup/teardown
  - Mock external API calls
  - Test authentication and authorization
- **Frontend**: Jest + React Testing Library (expanding coverage)
  - Test component rendering and user interactions
  - Mock API calls with MSW
  - Test error states and loading states

### Code Quality Standards
- **Backend**: Must pass ruff, black, isort, mypy checks
- **Frontend**: Must pass ESLint, TypeScript compiler checks
- **Git**: Use conventional commits, feature branches
- **Documentation**: Update relevant docs with significant changes

## Scheduled Jobs & Background Tasks

The application runs comprehensive automated jobs via APScheduler:

### Daily Jobs
- **3:00 UTC**: Nightly stats ingestion from RapidAPI (`ingest_stat_lines`)
- **3:30 UTC**: Fantasy score calculation after stats ingestion (`update_weekly_team_scores`)
- **4:00 UTC**: Analytics calculation (`calculate_analytics`)
- **2:00 UTC Tuesday**: Player profile updates (`update_player_profiles`)

### Weekly Jobs
- **Monday 5:00 UTC**: Weekly roster move reset (`reset_weekly_moves`)
- **Monday 5:59 UTC**: Weekly bonus calculation (`calculate_weekly_bonuses`)

### Real-time Jobs
- **Every second**: Draft clock management (`check_draft_clocks`)
- **Every 30 seconds**: Live game updates (when games are active)

### Job Implementation Details
- **Location**: Jobs defined in `app/jobs/` directory
- **Scheduling**: Configured in `app/core/scheduler.py`
- **Error Handling**: All jobs log errors to `ingest_log` table
- **Manual Execution**: Jobs can be triggered via CLI or admin dashboard
- **Monitoring**: Job status visible in admin dashboard

### Adding New Jobs
1. Create job function in appropriate `app/jobs/` file
2. Add scheduling configuration in `app/core/scheduler.py`
3. Include error handling and logging
4. Add manual trigger option in admin interface
5. Write tests for job functionality

## Real-time Features & WebSocket Architecture

### Draft System (Production-Ready)
- **WebSocket-powered live drafts** with configurable timer (default 60s)
- **Snake draft format** with automatic turn progression
- **Auto-pick system** when timer expires with position-based logic
- **Real-time updates** to all connected clients
- **Commissioner controls**: pause/resume/revert picks
- **Player queue system** for planning future picks
- **Position validation** enforced during picks

### Live Game Tracking
- **Real-time game updates** during WNBA games
- **Live fantasy scoring** with immediate point updates
- **WebSocket broadcasts** for score changes
- **Efficient caching** to minimize API calls
- **Admin controls** to start/stop live tracking

### Implementation Architecture
- **WebSocket Manager**: `app/core/ws_manager.py`
  - Connection pooling by league/game
  - Automatic cleanup of stale connections
  - Broadcasting to specific groups
- **Draft Logic**: `app/services/draft.py`
  - State validation and transitions
  - Auto-pick algorithms
  - Turn progression logic
- **Live Game Logic**: `app/services/live_games.py`
  - Real-time score calculations
  - Cache management
  - Update frequency control
- **Frontend Integration**:
  - `frontend/src/hooks/useDraftWebSocket.ts`: Draft real-time updates
  - Automatic reconnection on connection loss
  - Type-safe message handling

## External Integrations & Data Pipeline

### RapidAPI (WNBA Statistics)
- **Client**: `app/external_apis/rapidapi_client.py`
- **Endpoints**: Games, box scores, standings, teams, news, injuries
- **Rate Limiting**: Automatic throttling and retry logic
- **Error Handling**: Comprehensive exception handling with logging
- **Data Validation**: Pydantic models for API responses
- **Caching**: Intelligent caching to minimize API calls

### Data Ingestion Pipeline
1. **Schedule Fetch**: Get previous day's games
2. **Box Score Retrieval**: Fetch detailed player statistics
3. **Data Parsing**: Parse API responses into database models
4. **Data Validation**: Ensure data quality and consistency
5. **Database Updates**: Upsert players and statistics
6. **Error Logging**: Log all ingestion events and errors
7. **Analytics Trigger**: Trigger analytics recalculation

### Supported API Endpoints
- `fetch_schedule(year, month, day)`: Game schedules
- `fetch_box_score(game_id)`: Player statistics
- `fetch_game_summary(game_id)`: Game summaries
- `fetch_game_playbyplay(game_id)`: Play-by-play data
- `fetch_wnba_news(limit)`: League news
- `fetch_league_injuries()`: Injury reports

### Rate Limiting & Quotas
- **Basic Plan**: 500 requests/month
- **Pro Plan**: 10,000 requests/month
- **Typical Usage**: ~7 requests/day during season
- **Monitoring**: Track usage in admin dashboard

## Environment Configuration & Deployment

### Backend Environment Variables
**Required:**
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT signing key (use strong random string)
- `RAPIDAPI_KEY`: WNBA statistics API access key

**Optional with Defaults:**
- `INGEST_HOUR_UTC`: Nightly stats ingestion hour (default: 3)
- `DRAFT_TIMER_SECONDS`: Draft pick timer duration (default: 60)
- `ACCESS_TOKEN_EXPIRE_SECONDS`: JWT token expiration (default: 3600)
- `MAX_ROSTER_SIZE`: Maximum players per roster (default: 15)
- `MIN_STARTER_COUNT`: Minimum starters required (default: 5)
- `WEEKLY_MOVE_LIMIT`: Weekly roster moves allowed (default: 3)

**Production Additional:**
- `CORS_ORIGINS`: Allowed CORS origins
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ADMIN_EMAIL`: Default admin user email
- `ADMIN_PASSWORD`: Default admin user password

### Frontend Environment Variables
- `VITE_API_URL`: Backend API URL (e.g., https://api.example.com)
- `VITE_WS_URL`: WebSocket URL (e.g., wss://api.example.com)

### Environment Files
- `.env`: Local development
- `.env.production`: Production deployment
- `.env.mvp`: MVP demonstration
- `env.example`: Template with all variables

### Deployment Configurations
- **Development**: SQLite, localhost URLs
- **MVP**: Docker Compose with SQLite
- **Production**: PostgreSQL, Traefik, Cloudflare SSL

## Common Development Workflows

### Adding New API Endpoints (Complete Process)
1. **Service Layer**: Implement business logic in `app/services/`
   - Handle all validation and business rules
   - Include proper error handling
   - Add comprehensive docstrings
2. **API Endpoint**: Add endpoint to appropriate router in `app/api/`
   - Keep endpoint thin - just call service method
   - Add proper OpenAPI documentation
   - Include response examples
3. **Schemas**: Define Pydantic models in `app/api/schemas.py`
   - Mirror service method parameters and return types
   - Include validation rules and examples
4. **Frontend Types**: Update TypeScript definitions in `frontend/src/types/`
   - Mirror backend schemas exactly
   - Use consistent naming conventions
5. **Tests**: Add comprehensive tests in `/tests/`
   - Test both service layer and API endpoint
   - Include success and failure scenarios
   - Test authentication and authorization
6. **Documentation**: Update API documentation if needed

### Database Model Changes (Production-Safe Process)
1. **Model Updates**: Modify models in `app/models/__init__.py`
   - Follow existing naming conventions
   - Include proper relationships and constraints
   - Add indexes for performance
2. **Migration Generation**: `poetry run alembic revision --autogenerate -m "description"`
   - Use descriptive migration names
   - Review generated SQL carefully
3. **Migration Review**: Check generated migration file
   - Ensure data safety (no data loss)
   - Add manual data migration if needed
   - Test on copy of production data
4. **Service Updates**: Update related service methods
   - Handle new fields appropriately
   - Maintain backward compatibility
5. **API Updates**: Update endpoints if needed
   - Add new fields to schemas
   - Maintain API versioning
6. **Frontend Updates**: Update TypeScript types and components
7. **Testing**: Comprehensive testing of changes
   - Test migration rollback
   - Test with existing data

### Adding Frontend Components (Best Practices)
1. **Component Planning**: Determine component scope and reusability
   - Single responsibility principle
   - Identify shared vs feature-specific components
2. **Location**: Place in appropriate `components/` subdirectory
   - `common/` for reusable components
   - Feature directories for specific components
3. **TypeScript Types**: Add interfaces to `types/` if needed
   - Props interfaces
   - State interfaces
   - API response types
4. **Implementation**: Follow established patterns
   - Use functional components with hooks
   - Implement proper error boundaries
   - Include loading and error states
5. **Styling**: Use TailwindCSS utility classes
   - Follow design system patterns
   - Ensure responsive design
6. **Testing**: Write component tests
   - Test rendering with different props
   - Test user interactions
   - Test error states

### Adding Scheduled Jobs
1. **Job Function**: Create in appropriate `app/jobs/` file
   - Include comprehensive error handling
   - Add progress logging
   - Make idempotent if possible
2. **Scheduling**: Add to `app/core/scheduler.py`
   - Use appropriate cron expressions
   - Consider timezone implications
3. **Manual Trigger**: Add admin interface option
   - Allow manual job execution
   - Show job status and logs
4. **Monitoring**: Add job status tracking
   - Log job start/completion
   - Track execution time
   - Alert on failures
5. **Testing**: Test job execution
   - Mock external dependencies
   - Test error scenarios
   - Verify idempotency

### Performance Optimization Workflow
1. **Identify Bottlenecks**: Use profiling tools
   - Database query analysis
   - API response time monitoring
   - Frontend bundle analysis
2. **Database Optimization**:
   - Add appropriate indexes
   - Optimize N+1 queries
   - Use database query analysis
3. **API Optimization**:
   - Implement response caching
   - Add pagination for large datasets
   - Optimize serialization
4. **Frontend Optimization**:
   - Code splitting
   - Lazy loading
   - Memoization of expensive operations

## Error Handling & Logging Standards

### Backend Error Handling
- **Service Layer**: Raise specific Python exceptions (ValueError, PermissionError, etc.)
- **API Layer**: Convert to HTTPException with appropriate status codes
- **Database Errors**: Handle constraint violations, connection errors
- **External API Errors**: Implement retry logic with exponential backoff
- **Logging**: Use structured logging with appropriate levels

### Frontend Error Handling
- **API Errors**: Use error boundaries and proper error states
- **Network Errors**: Handle offline scenarios gracefully
- **Validation Errors**: Show user-friendly error messages
- **Loading States**: Always show appropriate loading indicators

### Status Code Standards
- **200**: Success
- **201**: Created
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (business logic violation)
- **422**: Unprocessable Entity (validation errors)
- **500**: Internal Server Error

## Security Best Practices

### Authentication & Authorization
- **JWT Tokens**: Secure token generation and validation
- **Password Hashing**: bcrypt with appropriate cost factor
- **Session Management**: Proper token expiration and refresh
- **Role-Based Access**: Admin vs regular user permissions
- **API Security**: Rate limiting and input validation

### Data Protection
- **Environment Variables**: Never commit secrets to code
- **Database Security**: Use parameterized queries, avoid SQL injection
- **CORS Configuration**: Restrict origins in production
- **Input Validation**: Validate all user inputs
- **Output Sanitization**: Prevent XSS attacks

### Production Security Checklist
- [ ] Secure environment variable storage
- [ ] HTTPS enforcement
- [ ] Database connection encryption
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Input validation comprehensive

## Testing Strategy & Requirements

### Backend Testing (Comprehensive Coverage Required)
- **Unit Tests**: Test individual service methods
- **Integration Tests**: Test API endpoints end-to-end
- **Database Tests**: Test model relationships and constraints
- **Authentication Tests**: Test security and permissions
- **External API Tests**: Mock external services
- **Performance Tests**: Test under load

### Test Organization
```
tests/
├── test_auth.py              # Authentication tests
├── test_admin_api.py         # Admin endpoint tests
├── test_analytics.py         # Analytics service tests
├── test_draft.py             # Draft system tests
├── test_league_endpoints.py  # League management tests
├── test_roster_service.py    # Roster operations tests
├── test_scoring_service.py   # Scoring calculations tests
└── conftest.py              # Shared fixtures
```

### Test Fixtures & Utilities
- Use `conftest.py` for shared fixtures
- Database setup/teardown per test
- Mock external API calls
- Create realistic test data
- Test both success and failure paths

### Frontend Testing (Expanding Coverage)
- **Component Tests**: React Testing Library
- **Hook Tests**: Custom hook testing
- **Integration Tests**: Full user workflows
- **E2E Tests**: Cypress (planned)

## Code Quality & Standards

### Backend Code Quality
- **Linting**: ruff (flake8 replacement)
- **Formatting**: black (line length 88)
- **Import Sorting**: isort
- **Type Checking**: mypy (strict mode)
- **Documentation**: Google-style docstrings

### Frontend Code Quality
- **Linting**: ESLint with TypeScript rules
- **Formatting**: Prettier (via ESLint)
- **Type Checking**: TypeScript strict mode
- **Bundle Analysis**: webpack-bundle-analyzer

### Git Workflow
- **Branch Naming**: `feature/description`, `fix/description`, `refactor/description`
- **Commit Messages**: Conventional commits format
- **Pull Requests**: Require review and passing tests
- **Branch Protection**: Protect main branch

## Performance Optimization Guidelines

### Backend Performance
- **Database**: Proper indexing, query optimization
- **Caching**: Redis for session storage and API caching
- **API**: Response compression, pagination
- **Background Jobs**: Efficient scheduling and execution
- **Memory Management**: Proper connection pooling

### Frontend Performance
- **Bundle Optimization**: Code splitting, tree shaking
- **Component Optimization**: React.memo, useMemo, useCallback
- **API Optimization**: Request deduplication, caching
- **Image Optimization**: Proper sizing and formats
- **Loading Strategies**: Lazy loading, progressive enhancement

### Monitoring & Metrics
- **Application Metrics**: Response times, error rates
- **Database Metrics**: Query performance, connection usage
- **External API Metrics**: Rate limit usage, error rates
- **User Metrics**: Page load times, user interactions

## Troubleshooting Common Issues

### Development Issues
1. **Database Connection Errors**
   - Check DATABASE_URL environment variable
   - Ensure database migrations are applied
   - Verify database file permissions (SQLite)

2. **Authentication Failures**
   - Verify SECRET_KEY is set and consistent
   - Check token expiration settings
   - Ensure proper CORS configuration

3. **External API Issues**
   - Verify RAPIDAPI_KEY is valid and has quota
   - Check network connectivity
   - Review rate limiting configuration

4. **WebSocket Connection Issues**
   - Verify WebSocket URL configuration
   - Check for proxy/firewall blocking WebSocket connections
   - Ensure proper error handling and reconnection

### Production Issues
1. **Performance Problems**
   - Review database query performance
   - Check memory and CPU usage
   - Analyze API response times
   - Review caching effectiveness

2. **Data Quality Issues**
   - Use admin dashboard data quality checks
   - Review ingest logs for errors
   - Verify external API data consistency

3. **Deployment Issues**
   - Check environment variable configuration
   - Verify Docker container health
   - Review application logs
   - Ensure database migrations are applied

## Documentation Maintenance

### When to Update Documentation
- **API Changes**: Update WNBA_API_ENDPOINTS.md
- **Architecture Changes**: Update Architecture.md
- **Deployment Changes**: Update DEPLOYMENT.md
- **Style Changes**: Update Style-Guide.md
- **New Features**: Update README.md and relevant docs

### Documentation Standards
- **Clear Examples**: Provide code examples and usage scenarios
- **Up-to-Date**: Keep documentation synchronized with code
- **Complete Coverage**: Document all public APIs and major features
- **User-Focused**: Write for both developers and end users

## Important Project Files Reference

### Core Configuration Files
- `pyproject.toml`: Python dependencies and project metadata
- `alembic.ini`: Database migration configuration
- `Makefile`: Common development commands
- `docker-compose.yml`: Production deployment
- `docker-compose.mvp.yml`: MVP demonstration

### Key Scripts
- `scripts/seed_demo.py`: Development data seeding
- `scripts/seed_mvp.py`: MVP data seeding
- `scripts/deploy.sh`: Production deployment
- `scripts/backup.sh`: Database backup
- `start-mvp.sh`: Quick MVP startup

### Essential Documentation
- `CLAUDE.md`: This comprehensive developer guide
- `README.md`: Project overview and quick start
- `docs/Architecture.md`: Detailed system architecture
- `docs/Style-Guide.md`: Coding standards and conventions
- `docs/DEPLOYMENT.md`: Production deployment guide
- `WNBA_API_ENDPOINTS.md`: Complete API documentation

## Current Tasks & Known Issues

### High Priority Tasks
- **Player Analytics Frontend**: Complete frontend integration for analytics dashboard
- **Trade System**: Implement player trading between teams
- **Enhanced UI/UX**: Improve responsive design and user experience
- **Email Notifications**: Add notification system for draft events and game updates
- **Mobile App**: Consider React Native implementation

### Known Issues & Limitations
- **Database Performance**: Some complex queries need optimization
- **Bundle Size**: Frontend bundle could be further optimized
- **Error Handling**: Some edge cases need better error messages
- **Documentation**: Some API endpoints need better examples

### Technical Debt
- **Test Coverage**: Expand frontend test coverage
- **Type Safety**: Add stricter TypeScript configurations
- **Performance**: Implement comprehensive caching strategy
- **Monitoring**: Add production monitoring and alerting

Remember: Always prioritize code quality, comprehensive testing, and clear documentation. When in doubt, follow established patterns in the codebase and refer to this guide.