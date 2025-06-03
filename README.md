# WNBA Fantasy League
[![CI](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml/badge.svg)](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml)

*A full-featured fantasy basketball platform for WNBA enthusiasts.*

WNBA Fantasy League is a comprehensive web application that enables private groups to draft WNBA players, manage rosters, track real-time statistics, and compete throughout the season with automated scoring and live standings.

---

## 🎯 Current Features

| Status | Feature | Description |
| ------ | ------- | ----------- |
| ✅ | **User Authentication** | Secure JWT-based authentication system |
| ✅ | **League Management** | Create/join leagues with invite codes, commissioner controls |
| ✅ | **Live Draft System** | Real-time snake draft with WebSocket updates, auto-pick timer |
| ✅ | **Roster Management** | Add/drop players (3 moves/week limit), set starters with position requirements |
| ✅ | **Automated Stats** | Nightly ingestion from RapidAPI with automatic scoring calculations |
| ✅ | **Real-time Standings** | Live league standings with weekly and season totals |
| ✅ | **Transaction Logging** | Complete audit trail of all roster moves and draft picks |
| 🚧 | **Weekly Bonuses** | Backend implemented, frontend integration pending |
| 🚧 | **Player Analytics** | Backend ready, frontend views in development |
| ❌ | **Trade System** | Planned feature for player trades between teams |
| ❌ | **League Chat** | Planned communication system for league members |

---

## 🛠 Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **Database:** SQLAlchemy ORM + Alembic migrations
- **Real-time:** WebSocket support for live draft
- **Scheduling:** APScheduler for automated tasks
- **External API:** RapidAPI for WNBA statistics

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State Management:** React Context + Custom Hooks
- **API Client:** Axios with TypeScript interfaces

### DevOps & Tooling
- **Package Management:** Poetry (backend), npm (frontend)
- **Code Quality:** Ruff, Black, isort, ESLint
- **Testing:** Pytest (backend), Jest + RTL (frontend planned)
- **CI/CD:** GitHub Actions
- **Deployment Target:** Hetzner VPS

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Poetry
- Node.js 16+ & npm
- Git

### Backend Setup
```bash
# Clone and enter the repository
git clone <repository-url>
cd WNBA-Fantasy-League

# Install Python dependencies
poetry install

# Set up environment variables
cp env.example .env
# Edit .env with your RapidAPI key and other settings

# Initialize database
poetry run alembic upgrade head

# (Optional) Seed with demo data
poetry run python scripts/seed_demo.py

# Start the API server
make dev
# API docs available at http://localhost:8000/docs
```

### Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# UI available at http://localhost:5173
```

### Running Tests
```bash
# Backend tests
make test

# Linting and formatting
make lint
make format
```

---

### 📊 Key Workflows
#### League Creation & Management

Commissioner creates league with custom settings
Invite code generated for player recruitment
Players join with invite code and team name
Commissioner starts draft when ready

#### Draft Process

Snake draft with configurable timer (default 60s)
Real-time updates via WebSocket
Player queue system for planning picks
Auto-pick on timer expiration
Position requirements enforced

#### Season Management

Nightly stats ingestion (3 AM UTC default)
Automatic fantasy point calculations
Weekly roster moves (3 per team)
Starting lineup management (5 starters required)
Weekly and season-long standings

---

### 🔧 Configuration
##### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=sqlite:///./prod.db
SECRET_KEY=your-secret-key-here
RAPIDAPI_KEY=your-rapidapi-key
INGEST_HOUR_UTC=3
DRAFT_TIMER_SECONDS=60

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

Scheduled Jobs

* Nightly Stats Ingest: 3:00 UTC
* Score Calculation: 3:30 UTC
* Weekly Bonus Calc: Monday 5:59 UTC
* Move Reset: Monday 5:00 UTC
* Player Profile Update: Tuesday 2:00 UTC
* Analytics Calculation: 4:00 UTC

---

### 📁 Project Structure

```
WNBA-Fantasy-League/
├── app/                    # FastAPI backend
│   ├── api/               # API endpoints
│   ├── core/              # Core utilities
│   ├── models/            # SQLAlchemy models
│   ├── services/          # Business logic
│   └── jobs/              # Scheduled tasks
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/        # Route pages
│   │   ├── hooks/        # Custom hooks
│   │   └── lib/          # API client
│   └── public/           # Static assets
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```