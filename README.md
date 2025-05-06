# WNBA Fantasy League
[![CI](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml/badge.svg)](https://github.com/grantharris33/WNBA-Fantasy-League/actions/workflows/ci.yml)

*A lightweight fantasy women's basketball web app.*

WNBA Fantasy League lets a small, private group draft WNBA (or NBA) players, track nightly box‑scores, and see real‑time standings for a season-long fantasy competition in a clean React UI backed by a FastAPI service.

---

## Core Features

| Done? | Feature                                  |
| ----- | ---------------------------------------- |
| ❌     | Snake‑draft lobby with live countdown    |
| ❌     | Positional roster rules (≥2 G, ≥1 F/F‑C) |
| ❌     | Automatic nightly stat ingest & scoring  |
| ❌     | Weekly objective bonuses                 |
| ❌     | Change‑log for every roster move         |
| ❌     | JWT **or** cookie auth (toggle)          |
| ❌     | Responsive React + Tailwind front‑end    |

---

## Tech Stack

* **Backend:** FastAPI / Python 3.10, SQLAlchemy ORM, SQLite
* **Front‑end:** React + Vite, Tailwind CSS, shadcn/ui, Chart.js
* **Dev Tooling:** Poetry, Ruff, Black, Isort, Pytest, Pre‑commit hooks
* **CI/CD:** GitHub Actions

---

## Quick Start (Dev)

### Prerequisites
- macOS: `brew install poetry`
- Linux / WSL: `curl -sSL https://install.python-poetry.org | python3 -`

```bash
# clone & install
poetry install

# run all quality checks
pre-commit run --all-files

# start API (reloads)
make dev

# start front‑end in another terminal
npm install --prefix frontend && npm run dev --prefix frontend
```

The API will be live at `http://localhost:8000/docs` and the UI at `http://localhost:5173`.

---

## Useful Links

* **Architecture overview:** [`docs/Architecture.md`](docs/Architecture.md)
* **Issue board:** see GitHub Projects › MVP
* **Contribution guide:** `CONTRIBUTING.md`
