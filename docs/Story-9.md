# FANTASY‑9 — Draft API & Real‑Time Orchestration

> **Goal:** Provide endpoints and real‑time channels so 2–4 users can conduct a timed snake draft entirely in the web app.

---

## 1  Business Rules

| Rule                | Detail                                                                      |
| ------------------- | --------------------------------------------------------------------------- |
| Draft type          | Snake: 1 → 4, 4 → 1, repeat until roster slots filled (10 rounds)           |
| Pick timer          | 60 seconds per pick (config via env)                                        |
| Auto‑pick           | If timer hits 0, best remaining ADP player is picked                        |
| Positional legality | After draft, roster must already satisfy ≥ 2 G and ≥ 1 F/F‑C among starters |
| Pause/resume        | Commissioner (league owner) can pause/resume draft                          |
| Persistence         | Draft state survives server restarts (stored in `draft_state` table)        |

---

## 2  Sub‑Tasks

| Key                             | Title                                                                                                         | What / Why                                                                                                                                 | Acceptance Criteria |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| **9‑A Start Draft**             | `POST /api/v1/leagues/{league_id}/draft/start`                                                                | Generates snake order list, creates `draft_state` rows; returns 400 if already started.                                                    |                     |
| **9‑B Pick Endpoint**           | `POST /api/v1/draft/{draft_id}/pick` body `{player_id}`                                                       | Validates: it’s caller’s turn, clock not expired, player not taken, roster positional rules still satisfiable. Returns updated state JSON. |                     |
| **9‑C Auto‑Pick Fallback**      | APScheduler job monitors active draft clocks; on expiry selects top‑ranked ADP player via pre‑loaded rankings | Unit test with `freezegun` asserts auto‑pick executed at 60 s.                                                                             |                     |
| **9‑D WebSocket Channel**       | `/ws/draft/{league_id}` broadcasts `draft_event` messages (pick, clock, pause)                                | Front‑end receives and updates UI in <250 ms round‑trip on local network.                                                                  |                     |
| **9‑E Pause / Resume Endpoint** | `POST /api/v1/draft/{id}/pause` & `/resume` (commissioner only)                                               | Clock stops/starts; WS broadcast `status=paused/resumed`.                                                                                  |                     |
| **9‑F State Endpoint**          | `GET /api/v1/draft/{id}/state`                                                                                | Returns current round, pick index, clock seconds left, drafted players list.                                                               |                     |
| **9‑G Persistence Model**       | Add `draft_state` and `draft_pick` SQLModel tables                                                            | On app restart, scheduler restores clocks from DB.                                                                                         |                     |
| **9‑H Frontend Draft Room**     | React page shows: current pick, countdown, available list with search, user’s queue                           | UI tested in Cypress scripted draft flow.                                                                                                  |                     |
| **9‑I Integration Tests**       | End‑to‑end pytest with WebSocket client simulating 4 users                                                    | Scenario completes 10‑round draft without error; asserts roster sizes.                                                                     |                     |
