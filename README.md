# WNBA Fantasy League
[![CI](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml/badge.svg)](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)

*A production-ready fantasy basketball platform for WNBA enthusiasts with real-time features and comprehensive analytics.*

WNBA Fantasy League is a modern, full-featured web application that enables private groups to create leagues, conduct live drafts, manage rosters, and compete throughout the WNBA season. Built with FastAPI and React, it features real-time updates, automated statistics ingestion, comprehensive scoring systems, and advanced analytics.

---

## 🎯 Feature Overview

### ✅ Core Features (Production Ready)
- **🔐 User Authentication**: Secure JWT-based system with role management
- **🏀 League Management**: Create/join private leagues with invite codes and commissioner controls
- **⚡ Live Draft System**: Real-time snake drafts with WebSocket updates, configurable timers, and auto-pick
- **👥 Roster Management**: Add/drop players with move limits, set starters with position validation
- **📊 Automated Statistics**: Nightly WNBA data ingestion with automatic fantasy scoring
- **🏆 Real-time Standings**: Live league standings with historical tracking
- **📝 Admin Dashboard**: Comprehensive system monitoring, data quality checks, and manual controls
- **📱 Live Game Tracking**: Real-time game updates and fantasy score calculations
- **🔍 Transaction Logging**: Complete audit trail of all league activities

### 🚧 Advanced Features (Backend Complete)
- **📈 Player Analytics**: Performance trends, projections, and matchup analysis
- **🎁 Weekly Bonuses**: Configurable bonus system (double-doubles, triple-doubles, etc.)
- **📋 Historical Lineups**: Track and manage lineups across multiple weeks
- **⚙️ Data Quality Monitoring**: Automated checks and alerts for data consistency

### 🔮 Planned Features
- **🔄 Trade System**: Player trading between teams with approval workflow
- **💬 League Chat**: Real-time communication system for league members
- **📧 Email Notifications**: Automated alerts for draft events and game updates
- **📱 Mobile App**: React Native implementation for mobile access

---

## 🛠 Technology Stack

### Backend (FastAPI)
- **Framework:** FastAPI (Python 3.10+) with async/await support
- **Database:** SQLAlchemy ORM with Alembic migrations
- **Authentication:** JWT tokens with bcrypt password hashing
- **Real-time:** WebSocket connections for live updates
- **Scheduling:** APScheduler for automated background jobs
- **External APIs:** RapidAPI client for WNBA statistics
- **Caching:** In-memory caching with planned Redis integration

### Frontend (React + TypeScript)
- **Framework:** React 18 with hooks and strict TypeScript
- **Build Tool:** Vite with hot module replacement
- **Styling:** Tailwind CSS with responsive design
- **State Management:** React Context with custom hooks
- **Real-time:** WebSocket hooks for live data
- **Routing:** React Router with protected routes

### Infrastructure & DevOps
- **Containerization:** Docker with multi-stage builds
- **Reverse Proxy:** Traefik with automatic SSL (Let's Encrypt)
- **Database:** SQLite (development), PostgreSQL (production)
- **Package Management:** Poetry (backend), npm (frontend)
- **Code Quality:** Ruff, Black, isort (Python), ESLint (TypeScript)
- **Testing:** Pytest with 90%+ coverage, Jest + React Testing Library
- **CI/CD:** GitHub Actions with automated testing and deployment
- **Hosting:** Hetzner VPS with Cloudflare CDN

### External Services
- **WNBA Data:** RapidAPI for real-time statistics and game data
- **SSL Certificates:** Let's Encrypt with Cloudflare DNS validation
- **Monitoring:** Built-in admin dashboard with audit logging

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** with Poetry
- **Node.js 18+** with npm
- **Git** for version control
- **RapidAPI Key** for WNBA data (optional for development)

### Option 1: MVP Docker Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/grantharris33/WNBA-Fantasy-League.git
cd WNBA-Fantasy-League

# Start complete MVP environment
./start-mvp.sh

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Development Setup

#### Backend Setup
```bash
# Install Python dependencies
poetry install

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Initialize database with migrations
poetry run alembic upgrade head

# Seed with demo data (optional)
poetry run python scripts/seed_demo.py

# Start development server with auto-reload
make dev
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

### Development Commands
```bash
# Backend
make test          # Run comprehensive test suite
make lint          # Check code quality
make format        # Auto-format code

# Frontend
cd frontend
npm run build      # Production build
npm run lint       # TypeScript and ESLint checks

# Database
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

---

## 🏀 Getting Started

### Demo Access
Try the live MVP demo with pre-configured data:

**Demo Accounts:**
- Admin: `me@grantharris.tech` / `Thisisapassword1`
- User: `demo@example.com` / `demo123`
- League Invite Codes: `MVP-DEMO`, `TEST-123`

### Development vs Production

| Feature | Development | MVP Docker | Production |
|---------|-------------|------------|-----------|
| Database | SQLite | SQLite | PostgreSQL |
| Real-time | WebSocket | WebSocket | WebSocket + SSL |
| WNBA Data | Mock/Sample | Optional Real API | Real API |
| SSL | No | No | Yes (Traefik + Let's Encrypt) |
| Monitoring | Basic Logs | Basic Logs | Admin Dashboard + Logs |
| Backup | Manual | Manual | Automated Daily |

### Production Deployment

For production deployment on a VPS:

```bash
# Clone and configure
git clone https://github.com/grantharris33/WNBA-Fantasy-League.git
cd WNBA-Fantasy-League

# Configure production environment
cp .env.production .env.production
# Edit with your domain, API keys, and passwords

# Deploy with SSL and monitoring
./scripts/deploy.sh production
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete production setup guide.

## 📊 Key Workflows

### League Creation & Management
1. **Commissioner Setup**: Create league with custom scoring, roster rules, and draft settings
2. **Player Recruitment**: Generate invite codes for private league access
3. **Team Creation**: Players join with invite codes and create their team names
4. **Draft Preparation**: Commissioner configures draft order and timing
5. **Season Management**: Ongoing roster management and standings tracking

### Live Draft Process
1. **Draft Initialization**: Commissioner starts draft with real-time WebSocket connections
2. **Snake Draft Format**: Alternating pick order across multiple rounds
3. **Real-time Updates**: Instant updates to all participants via WebSocket
4. **Timer Management**: Configurable pick timers with auto-pick functionality
5. **Position Validation**: Enforce roster composition rules during draft
6. **Commissioner Controls**: Pause, resume, or revert picks as needed

### Season Management & Scoring
1. **Automated Data Pipeline**: Nightly ingestion of WNBA statistics at 3:00 AM UTC
2. **Fantasy Scoring**: Automatic calculation of fantasy points based on real games
3. **Roster Management**: Players can add/drop free agents (3 moves per week limit)
4. **Lineup Setting**: Set starting lineups with position requirements (5 starters minimum)
5. **Live Tracking**: Real-time game updates and fantasy score calculations
6. **Historical Records**: Complete tracking of lineups, scores, and transactions

### Admin Dashboard Features
1. **System Monitoring**: Real-time status of all system components
2. **Data Quality**: Automated checks and manual data validation tools
3. **User Management**: Admin controls for user accounts and permissions
4. **Manual Operations**: Trigger data ingestion, score recalculation, and other jobs
5. **Audit Logging**: Complete trail of all administrative actions

---

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
```bash
# Required
DATABASE_URL=sqlite:///./prod.db          # Database connection
SECRET_KEY=your-secret-key-here           # JWT signing key
RAPIDAPI_KEY=your-rapidapi-key            # WNBA data API key

# Optional (with defaults)
INGEST_HOUR_UTC=3                         # Data ingestion time
DRAFT_TIMER_SECONDS=60                    # Draft pick timer
MAX_ROSTER_SIZE=15                        # Maximum roster size
WEEKLY_MOVE_LIMIT=3                       # Weekly moves allowed
ACCESS_TOKEN_EXPIRE_SECONDS=3600          # JWT expiration
```

#### Frontend Configuration
```bash
VITE_API_URL=http://localhost:8000        # Backend API URL
VITE_WS_URL=ws://localhost:8000           # WebSocket URL
```

### Automated Scheduling

The application runs comprehensive background jobs:

#### Daily Jobs
- **3:00 AM UTC**: WNBA statistics ingestion from RapidAPI
- **3:30 AM UTC**: Fantasy score calculations and updates
- **4:00 AM UTC**: Player analytics and trend calculations
- **2:00 AM UTC (Tuesday)**: Player profile updates and maintenance

#### Weekly Jobs
- **Monday 5:00 AM UTC**: Reset weekly roster move limits
- **Monday 5:59 AM UTC**: Calculate and award weekly bonuses

#### Real-time Jobs
- **Every second**: Draft timer management and auto-pick triggers
- **Every 30 seconds**: Live game updates during active WNBA games

### Scoring Configuration

Default fantasy scoring system (customizable per league):
```json
{
  "points": 1.0,
  "rebounds": 1.2,
  "assists": 1.5,
  "steals": 3.0,
  "blocks": 3.0,
  "turnovers": -1.0,
  "double_double_bonus": 5.0,
  "triple_double_bonus": 10.0
}
```

---

## 📁 Project Architecture

### Repository Structure
```
WNBA-Fantasy-League/
├── app/                    # FastAPI backend application
│   ├── api/               # API route handlers
│   │   ├── admin.py       # Admin-only operations
│   │   ├── analytics.py   # Player analytics endpoints
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── draft.py       # Live draft management
│   │   ├── live_games.py  # Real-time game tracking
│   │   └── wnba.py        # WNBA data endpoints
│   ├── core/              # Core utilities and configuration
│   │   ├── config.py      # Environment configuration
│   │   ├── database.py    # Database session management
│   │   ├── security.py    # Authentication and security
│   │   ├── ws_manager.py  # WebSocket connection management
│   │   └── scheduler.py   # Background job scheduling
│   ├── models/            # SQLAlchemy ORM models
│   ├── services/          # Business logic layer (service-first architecture)
│   │   ├── admin.py       # Admin operations
│   │   ├── analytics.py   # Player performance analytics
│   │   ├── draft.py       # Draft state and validation
│   │   ├── league.py      # League management
│   │   ├── roster.py      # Roster and lineup management
│   │   └── scoring.py     # Fantasy point calculations
│   ├── jobs/              # Scheduled background tasks
│   │   ├── ingest.py      # WNBA data ingestion
│   │   ├── score_engine.py # Fantasy scoring calculations
│   │   ├── analytics_job.py # Player analytics
│   │   └── draft_clock.py # Draft timer management
│   └── external_apis/     # External service clients
│       └── rapidapi_client.py # WNBA data API client
├── frontend/              # React + TypeScript application
│   ├── src/
│   │   ├── components/    # Feature-organized UI components
│   │   │   ├── common/    # Reusable components
│   │   │   ├── dashboard/ # Dashboard-specific components
│   │   │   ├── draft/     # Draft room components
│   │   │   ├── roster/    # Roster management components
│   │   │   └── layout/    # Layout and navigation
│   │   ├── pages/         # Route-based page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── contexts/      # React Context providers
│   │   ├── types/         # TypeScript type definitions
│   │   └── services/      # API client services
│   └── public/           # Static assets and favicon
├── tests/                # Comprehensive test suite
│   ├── test_auth.py      # Authentication tests
│   ├── test_draft.py     # Draft system tests
│   ├── test_analytics.py # Analytics tests
│   └── conftest.py       # Shared test fixtures
├── scripts/              # Utility and deployment scripts
│   ├── seed_demo.py      # Development data seeding
│   ├── seed_mvp.py       # MVP demonstration data
│   ├── deploy.sh         # Production deployment
│   └── backup.sh         # Database backup
├── docs/                 # Comprehensive documentation
│   ├── Architecture.md   # System architecture details
│   ├── Style-Guide.md    # Coding standards and conventions
│   ├── DEPLOYMENT.md     # Production deployment guide
│   └── rapidapi_integration.md # External API documentation
├── alembic/              # Database migration scripts
├── docker-compose.yml    # Production Docker configuration
├── docker-compose.mvp.yml # MVP demonstration setup
└── Makefile              # Common development commands
```

### Key Design Principles
- **Service-First Architecture**: Business logic implemented in services before API endpoints
- **Feature-Based Organization**: Frontend components organized by domain, not by type
- **Comprehensive Testing**: >90% backend test coverage with realistic fixtures
- **Type Safety**: Strict TypeScript throughout frontend, typed Python in backend
- **Real-time First**: WebSocket support for live updates in draft and games
- **Production Ready**: Docker deployment with SSL, monitoring, and backup systems

---

## 📚 Documentation

### For Developers
- **[CLAUDE.md](CLAUDE.md)**: Comprehensive developer guide for LLM instances
- **[docs/Architecture.md](docs/Architecture.md)**: Detailed system architecture and design patterns
- **[docs/Style-Guide.md](docs/Style-Guide.md)**: Coding standards and best practices
- **[WNBA_API_ENDPOINTS.md](WNBA_API_ENDPOINTS.md)**: Complete API reference documentation

### For Deployment
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Production deployment guide with Docker and SSL
- **[docs/rapidapi_integration.md](docs/rapidapi_integration.md)**: External API configuration
- **[MVP_README.md](MVP_README.md)**: Quick MVP demonstration guide

### For Users
- **[MVP_STORIES.md](MVP_STORIES.md)**: User stories and feature descriptions
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**: Feature implementation status

## 🧪 Testing

### Backend Testing
```bash
make test                    # Run full test suite
make test-coverage          # Run with coverage report
poetry run pytest tests/test_draft.py -v  # Run specific tests
```

### Frontend Testing
```bash
cd frontend
npm run test                # Run Jest tests
npm run test:coverage       # Run with coverage
```

### Test Coverage
- **Backend**: >90% coverage with comprehensive integration tests
- **Frontend**: Expanding coverage with React Testing Library
- **E2E**: Planned Cypress implementation for full user workflows

## 🤝 Contributing

### Development Workflow
1. **Fork and Clone**: Create your own fork of the repository
2. **Feature Branch**: Create a feature branch (`git checkout -b feature/amazing-feature`)
3. **Code Quality**: Ensure all tests pass and code follows style guide
4. **Test Coverage**: Add tests for new functionality
5. **Documentation**: Update relevant documentation
6. **Pull Request**: Submit a PR with clear description of changes

### Code Quality Requirements
- **Backend**: Must pass `make lint` and `make test`
- **Frontend**: Must pass `npm run lint` and TypeScript compilation
- **Documentation**: Update docs for API changes or new features
- **Testing**: Maintain or improve test coverage

## 📊 Performance & Monitoring

### Performance Characteristics
- **API Response Time**: <200ms for most endpoints
- **Real-time Updates**: <100ms WebSocket message delivery
- **Data Ingestion**: Processes full day's WNBA data in <5 minutes
- **Database Queries**: Optimized with proper indexing
- **Frontend Bundle**: <500KB gzipped with code splitting

### Monitoring & Observability
- **Admin Dashboard**: Real-time system status and metrics
- **Audit Logging**: Complete trail of all user actions
- **Error Tracking**: Comprehensive error logging and alerting
- **Performance Metrics**: API response times and database performance
- **External API Monitoring**: RapidAPI usage and rate limiting

## 🛡️ Security

### Security Features
- **Authentication**: JWT tokens with secure password hashing (bcrypt)
- **Authorization**: Role-based access control (admin vs user)
- **Input Validation**: Comprehensive validation on all endpoints
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **XSS Protection**: Input sanitization and CSP headers
- **Rate Limiting**: API rate limiting to prevent abuse
- **HTTPS**: SSL enforcement in production with Traefik

### Security Best Practices
- Environment variables for all secrets
- Regular dependency updates
- Automated security scanning in CI/CD
- Comprehensive audit logging
- Production security hardening

## 📈 Roadmap

### Short Term (Next Release)
- **Enhanced Analytics**: Complete frontend integration for player analytics
- **Trade System**: Player trading between teams with approval workflow
- **Mobile Optimization**: Improved responsive design for mobile devices
- **Performance Optimization**: Database query optimization and caching

### Medium Term
- **Email Notifications**: Automated notifications for draft events and updates
- **Advanced Analytics**: Machine learning-based player projections
- **Social Features**: League chat and communication system
- **Mobile App**: React Native implementation

### Long Term
- **Multi-Sport Support**: Expand beyond WNBA to other sports
- **Advanced Visualization**: Interactive charts and data visualization
- **API Platform**: Public API for third-party integrations
- **Enterprise Features**: Multi-league management and advanced admin tools

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **WNBA**: For providing an exciting league to build fantasy sports around
- **RapidAPI**: For reliable WNBA statistics and data
- **FastAPI**: For an excellent Python web framework
- **React**: For a powerful frontend framework
- **Contributors**: All developers who have contributed to this project

## 📞 Support

- **Documentation**: Start with [CLAUDE.md](CLAUDE.md) for comprehensive guidance
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join discussions for questions and ideas
- **Email**: Contact maintainers for sensitive issues

---

**Built with ❤️ for WNBA fans and fantasy sports enthusiasts**