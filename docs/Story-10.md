# FANTASY‑10 — Roster Management (Add / Drop Free Agents)

> **Parent story:** Roster Management (extends tasks 10‑A → 10‑C)
>
> Allows users to pick up undrafted or waived players and drop players to the free‑agent pool while enforcing weekly move limits and positional rules. Trades are out of scope.

---

## Table of Contents

1. Context & Rules
2. Sub‑tasks (10‑D → 10‑K)
3. Open Questions

---

## 1  Context & Business Rules

| Rule                | Detail                                                                                |
| ------------------- | ------------------------------------------------------------------------------------- |
| Weekly move cap     | Max **3 roster moves** (add or drop) per team per ISO week (Mon–Sun)                  |
| Positional legality | After add/drop, roster must still satisfy **≥2 G** & **≥1 F/F‑C** among 5 starters    |
| Waivers             | None (first‑come, first‑served)                                                       |
| Effective time      | Change applies immediately; points start accumulating next calendar day (00:00 local) |
| Logging             | Every add/drop creates `transaction_log` row & bumps `moves_this_week`                |

---

## 2  Sub‑Tasks

| Key                             | Title                                                                                                  | Description & Deliverables                                                                                                               | Acceptance Criteria                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **10‑D List Free Agents**       | `GET /leagues/{id}/free-agents`                                                                        | Return players **not on any roster** for that league, sortable by PPG & last‑7 average. Add SQLModel `view_free_agents(league_id)` util. | 200 returns ≥1 player when pool non‑empty; supports `?sort=ppg` param. |
| **10‑E Add Free Agent**         | `POST /teams/{id}/add` body `{player_id, to_slot}`                                                     | Validate weekly‑move limit, positional legality, and duplicates; insert into `roster_slot` (`is_bench` flag per `to_slot`).              | 409 error if limit reached; 201 success returns updated roster JSON.   |
| **10‑F Drop Player**            | `POST /teams/{id}/drop` body `{player_id}`                                                             | Remove slot row; if dropping starter, auto‑elevate first eligible bench player or reject.                                                | 400 if positional rules violated after drop.                           |
| **10‑G Move Counter Update**    | Increment `moves_this_week` on add/drop and reset via Monday UTC cron (see 10‑I).                      | Integration test: after reset, counter = 0.                                                                                              |                                                                        |
| **10‑H Frontend Pick‑up UI**    | React page: searchable free‑agent list, "Add" button, position badges; confirmation modal.             | Mobile and desktop breakpoints; optimistic UI then WebSocket broadcast.                                                                  |                                                                        |
| **10‑I Weekly Reset Job**       | APScheduler job `reset_moves()` runs every Monday 05:00 UTC setting `moves_this_week=0` for all teams. | Job logged in `ingest_log`; unit test with frozen‑time.                                                                                  |                                                                        |
| **10‑J End‑to‑End Tests**       | Pytest scenario: team makes 3 moves, 4th returns 409; Monday reset allows new moves.                   | All green in CI.                                                                                                                         |                                                                        |
| **10‑K Change‑log Integration** | Middleware records add/drop diff (`+player`, `‑player`).                                               | `transaction_log` entry visible via `/logs` after action.                                                                                |                                                                        |

---

## 3  Open Questions

1. Should add/drop lock during live games? *(Out of scope for MVP—documented for v1)*
2. UI warning when weekly cap is 1 move away? *(Nice‑to‑have)*
