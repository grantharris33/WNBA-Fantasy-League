# Architecture


> **Scope:** MVP as defined in tickets FANTASY‑0 → FANTASY‑18

---

## 1. High‑Level Components

| Layer               | Responsibility                                 | Key Tech                                       |
| ------------------- | ---------------------------------------------- | ---------------------------------------------- |
| **Front‑end**       | Draft room, scoreboard, roster moves           | React + Vite, shadcn/ui, WebSocket (draft)     |
| **API Gateway**     | REST + WebSocket endpoints, auth, OpenAPI docs | FastAPI, Uvicorn                               |
| **Domain Services** | Draft engine, scoring engine, bonus calculator | Python service layer (plain classes)           |
| **Persistence**     | Relational data, change log, ingest log        | SQLite via SQLAlchemy                            |
| **Scheduler**       | Nightly ingest + weekly bonus jobs             | APScheduler (in‑process)                       |
| **External Data**   | Box‑scores & players                           | balldontlie (primary) / TheSportsDB (fallback) |

---

## 2. Repo Layout

```
WNBA-Fantasy-League/
├── app/                  # FastAPI package
│   ├── main.py           # ASGI entrypoint
│   ├── api/              # Routers (v1)
│   ├── services/         # Domain logic (draft, scoring)
│   ├── models/           # SQLModel ORM classes
│   ├── jobs/             # APScheduler tasks
│   └── core/             # Config, auth deps, utils
├── frontend/             # React (Vite)
├── tests/
├── alembic/              # Migrations (even SQLite needs versioning)
├── scripts/              # One‑off admin & seed scripts
└── ops/
    ├── Dockerfile
    └── docker-compose.yaml
```

---

## 3. Data Model (v0)

```mermaiderDiagram
    user ||--o{ team : owns
    league ||--o{ team : contains
    team ||--o{ roster_slot : has
    player ||--o{ roster_slot : fills
    player ||--o{ stat_line : produces
    team ||--o{ team_score : accumulates
    user ||--o{ transaction_log : triggers
```

*See `app/models/*.py` for exact fields.*

---

## 4. Runtime Flow

1. **Draft phase**

   * `/leagues/{id}/draft/start` generates order → WebSocket pushes to UI.
   * Each pick validated (positional rules) then persisted to `roster_slot`.
2. **Nightly ingest** (03:00 UTC)

   * Scheduler hits API → `stat_line` upserts.
   * Scoring engine aggregates into `team_score`.
3. **Weekly bonuses** (Mon 0500 UTC)

   * Bonus service queries leaders → writes bonus rows → refreshes standings.
4. **Front‑end polling / WS**

   * Standings page GETs `/scores/current` every 30 s.
   * Draft room listens to `/ws/draft/{league}`.

---

## 5. Auth Strategy

* **JWT bearer** (default): stateless; token TTL = 30 d.
* **Signed cookie** (optional): toggled via `AUTH_MODE=cookie` env var.
* Passwords hashed with **bcrypt** via `passlib`.

---

## 6. Observability & Logs

* **Access log:** standard Uvicorn
* **Change‑log:** middleware diff → `transaction_log` table
* **Ingest log:** errors & rate‑limit events → `ingest_log` table
* **Metrics:** Optional Prometheus exporter via `prometheus_fastapi_instrumentator`

---

## 7. Deployment Pipeline

1. Push to `main` ⇒ GitHub Actions matrix:

   * lint → test → build multi‑arch Docker image
2. `fly deploy` via Fly Secrets (DATABASE\_URL etc.)
3. Post‑deploy step: `alembic upgrade head`.

---

## 8. Local Dev Tips

* Use `make format` before committing.
* VS Code users: recommended extensions in `.vscode/extensions.json`.
* To reset DB: `rm dev.db && poetry run alembic upgrade head`.

---

## 9. Future Extensions

| Idea                 | Notes                                         |
| -------------------- | --------------------------------------------- |
| OAuth (Google) login | Lowers friction; swap FastAPI‑Users providers |
| Dockerized Postgres  | Swap SQLite for Postgres in prod              |
| Public league page   | Read‑only scoreboard share link               |
| Push Notifications    | Push daily standings to users                  |
