# FANTASY‑2 — Design & Bootstrap Database Schema

> **Goal:** Establish relational model in SQLite using SQLAlchemy and Alembic so future stories can persist data safely and run migrations.

---

## 1  Context

The app needs tables for users, leagues, teams, roster slots, stat lines, scores, and logs. We’ll sketch relationships first, then implement with **SQLAlchemy** (Pydantic‑first ORM) and **Alembic** migrations. Local dev DB = `dev.db` (SQLite file), prod can swap to Postgres later by env var.

---

## 2  Sub‑Tasks

| Key                          | Title                                                                           | What / Why                                                                                               | Acceptance Criteria |
| ---------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------- |
| **2‑A ER Diagram**           | Visualize entities & relations                                                  |                                                                                                          |                     |
| **2‑B SQLModel Definitions** | Create `app/models/__init__.py` with SQLAlchemy classes for all tables            | Running `alembic revision --autogenerate -m "init"` produces diff with expected tables (no warnings).    |                     |
| **2‑C Initial Migration**    | Bootstrap Alembic env & generate schema                                         | `uvicorn app.main:app` on clean clone auto‑creates `dev.db`; `/health` still works.                      |                     |
| **2‑D Seed Script**          | Script `scripts/seed_demo.py` inserts 4 demo users, a league, and default teams | After `poetry run python scripts/seed_demo.py`, dev can log in as user `demo1@example.com` / `password`. |                     |
