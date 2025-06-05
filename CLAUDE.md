# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-featured WNBA Fantasy League application with a FastAPI backend and React frontend. The system supports real-time drafts, automated statistics ingestion, scoring calculations, and comprehensive league management.

## Development Commands

### Backend (Python/FastAPI)
```bash
# Always use poetry run for Python commands
make dev                    # Start development server with auto-reload
make test                   # Run pytest suite
make lint                   # Run ruff, isort, black checks
make format                 # Auto-format code with black and isort

# Database operations
poetry run alembic upgrade head                    # Apply migrations
poetry run alembic revision --autogenerate -m ""   # Create new migration
poetry run python scripts/seed_demo.py             # Seed demo data

# CLI admin commands
poetry run python -m app.cli.main                  # Access CLI interface
```

### Frontend (React/TypeScript)
```bash
# Always cd frontend before running npm commands
cd frontend
npm run dev                 # Start Vite dev server (localhost:5173)
npm run build              # Production build
npm run lint               # ESLint checking
```

## Architecture

### Backend Structure
- **`app/api/`**: FastAPI routers organized by domain (auth, draft, leagues, etc.)
- **`app/services/`**: Business logic layer - always implement logic here before API endpoints
- **`app/models/`**: SQLAlchemy models with comprehensive relationships
- **`app/jobs/`**: Scheduled background tasks using APScheduler
- **`app/core/`**: Core utilities (database, config, security, WebSocket manager)

### Frontend Structure
- **`frontend/src/components/`**: Organized by feature (dashboard, draft, roster)
- **`frontend/src/pages/`**: Route-based page components
- **`frontend/src/contexts/`**: React Context for global state (AuthContext)
- **`frontend/src/types/`**: TypeScript definitions - keep these updated

### Key Data Models
- **User/League/Team**: Core hierarchy for fantasy leagues
- **Player/WNBATeam**: WNBA reference data with comprehensive statistics
- **RosterSlot/WeeklyLineup**: Fantasy team management with starter tracking
- **DraftState/DraftPick**: Live draft system with WebSocket real-time updates
- **StatLine/TeamScore**: Game statistics and fantasy point calculations

## Development Patterns

### API Development
1. Implement business logic in `app/services/` first
2. Create API endpoints in appropriate router files
3. Add comprehensive error handling and validation
4. Update OpenAPI schemas in router definitions

### Database Changes
1. Modify models in `app/models/`
2. Generate migration: `poetry run alembic revision --autogenerate -m "description"`
3. Review and edit migration file if needed
4. Apply: `poetry run alembic upgrade head`

### Frontend Development
1. Use TypeScript strictly - no `any` types
2. Follow component organization by feature domain
3. Use React Context sparingly - prefer component state
4. Import types from `frontend/src/types/index.ts`

### Testing
- Backend: Comprehensive pytest suite in `/tests/` - always run tests after changes
- Frontend: Jest + Testing Library configured but minimal coverage
- Use `make test` to run backend tests
- Test fixtures handle database setup/teardown

## Scheduled Jobs

The application runs several automated jobs:
- **3:00 UTC**: Nightly stats ingestion from RapidAPI
- **3:30 UTC**: Fantasy score calculation after stats ingestion
- **Monday 5:00 UTC**: Weekly roster move reset
- **Monday 5:59 UTC**: Weekly bonus calculation

Jobs are defined in `app/jobs/` and scheduled in `app/core/scheduler.py`.

## Real-time Features

### Draft System
- WebSocket-powered live drafts with timer functionality
- Snake draft format with automatic turn progression
- Auto-pick system when timer expires
- Real-time updates to all connected clients

### Implementation Notes
- WebSocket manager in `app/core/ws_manager.py`
- Draft logic in `app/services/draft.py`
- Frontend WebSocket hook: `frontend/src/hooks/useDraftWebSocket.ts`

## External Integrations

### RapidAPI (WNBA Statistics)
- Client in `app/external_apis/rapidapi_client.py`
- Endpoints for games, stats, teams, standings
- Rate limiting and error handling implemented
- Ingestion jobs in `app/jobs/` directory

## Environment Configuration

Backend requires:
- `DATABASE_URL`: SQLite/PostgreSQL connection
- `SECRET_KEY`: JWT signing key
- `RAPIDAPI_KEY`: WNBA statistics API access
- `INGEST_HOUR_UTC`: When to run nightly stats (default: 3)

Frontend requires:
- `VITE_API_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL for real-time features

## Common Development Workflows

### Adding New API Endpoints
1. Implement service logic in `app/services/`
2. Add endpoint to appropriate router in `app/api/`
3. Update frontend TypeScript types
4. Add tests in `/tests/`

### Database Model Changes
1. Update model in `app/models/`
2. Generate and review migration
3. Update related services and API endpoints
4. Add/update tests

### Adding Frontend Components
1. Create component in appropriate `components/` subdirectory
2. Add TypeScript types to `types/` if needed
3. Import and use in parent components or pages
4. Follow existing patterns for styling (Tailwind CSS)