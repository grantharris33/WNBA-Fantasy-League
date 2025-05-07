# FANTASY‑5 — Public JSON REST Endpoints

> **Goal:** Expose core read‑only data (leagues, teams, standings) to the front‑end via typed FastAPI routes.

---

**Status:** Complete

## 1  Context

Front‑end needs simple, versioned endpoints to load initial data sets. All endpoints are **GET**, publicly accessible once authenticated, and documented by OpenAPI.

---

## 2  Sub‑Tasks

| Key                      | Title                                                            | What / Why                                                                                                      | Acceptance Criteria |
| ------------------------ | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------- |
| **5‑A Pydantic Schemas** | DTOs `LeagueOut`, `TeamOut`, `ScoreOut`, plus pagination wrapper | `mypy` passes (strict); unit tests validate schema `.model_dump()` shapes.                                      |                     |
| **5‑B List Leagues**     | Route `GET /api/v1/leagues`                                      | Query params `limit` (default 20) & `offset` (default 0). Response JSON matches pagination schema; returns 200. |                     |
| **5‑C Team Detail**      | Route `GET /api/v1/teams/{team_id}`                              | Response includes roster array and latest season totals. Returns 404 for missing id; 200 otherwise.             |                     |
| **5‑D Current Scores**   | Route `GET /api/v1/scores/current`                               | Returns array sorted desc by season points; each item contains weekly delta and bonus breakdown.                |                     |
