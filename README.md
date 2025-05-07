# WNBA Fantasy League
[![CI](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml/badge.svg)](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml)

*A lightweight fantasy women's basketball web app.*

WNBA Fantasy League lets a small, private group draft WNBA players, track nightly box‑scores, manage rosters, and see real‑time standings for a season-long fantasy competition in a clean React UI backed by a FastAPI service.

---

## Core Features

| Done? | Feature                                              | Notes                                                                 |
| ----- | ---------------------------------------------------- | --------------------------------------------------------------------- |
| ✅     | Snake‑draft lobby with live countdown (Backend)      | Backend logic, API, and WebSocket implemented. UI is placeholder.     |
| ✅     | Positional roster rules (≥2 G, ≥1 F/F‑C for starters) | Enforced during "Set Starters" action.                                |
| ✅     | Automatic nightly stat ingest & scoring              | Fetches from RapidAPI, calculates points, updates team scores.        |
| ❌     | Weekly objective bonuses                             | Planned feature.                                                      |
| ✅     | Change‑log for every roster & draft move             | `TransactionLog` table records actions.                               |
| ✅     | JWT Authentication                                   | Secure API access using JSON Web Tokens.                              |
| ✅     | Frontend Foundation (React + Tailwind)               | Core structure, auth context, basic pages (Login, Dashboard) in place. |
| ✅     | Roster Management (Add/Drop, Set Starters)           | Backend APIs and services implemented. UI is placeholder.             |

---

## Tech Stack

*   **Backend:** FastAPI / Python 3.10+, SQLAlchemy ORM, Alembic, SQLite
*   **Frontend:** React + Vite, TypeScript, Tailwind CSS
*   **Real-time:** FastAPI WebSockets
*   **Scheduling:** APScheduler
*   **External Data:** RapidAPI (WNBA Stats)
*   **Dev Tooling:** Poetry, Ruff, Black, Isort, Pytest, Pre‑commit hooks
*   **CI/CD:** GitHub Actions

---

## Quick Start (Dev)

### Prerequisites

*   Python 3.10 or higher
*   Poetry (Python dependency manager)
    *   macOS: `brew install poetry`
    *   Linux / WSL: `curl -sSL https://install.python-poetry.org | python3 -`
*   Node.js and npm (for frontend)

### Backend Setup & Run

```bash
# Clone the repository
# git clone <repository-url>
# cd WNBA-Fantasy-League

# Install backend dependencies
poetry install

# Initialize/Upgrade the database
poetry run alembic upgrade head

# (Optional) Seed database with demo data
poetry run python scripts/seed_demo.py

# Run pre-commit hooks (optional, but good practice)
poetry run pre-commit run --all-files

# Start API (reloads on change)
make dev
```

The API will be live at `http://localhost:8000/docs`.

### Frontend Setup & Run

```bash
# Navigate to frontend directory
cd frontend

# Install frontend dependencies
npm install

# Start frontend dev server (reloads on change)
npm run dev
```

The UI will be live at `http://localhost:5173`.

---

## Useful Links

*   **Architecture overview:** [`docs/Architecture.md`](docs/Architecture.md)
*   **Issue board:** see GitHub Projects › MVP (or equivalent project planning tool)
*   **Contribution guide:** `CONTRIBUTING.md`
*   **Code of Conduct:** `.github/CODE_OF_CONDUCT.md`
