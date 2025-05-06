# FANTASY‑3 — Nightly Stats Ingest Service

> **Goal:** Pull daily box‑scores from the selected API, store them in `stat_line`, and log any ingest issues — all on an automatic schedule.

---

## 1  Context

Scoring and standings depend on fresh stat lines. We’ll use **APScheduler** embedded in FastAPI (in‑process) for simplicity. Tasks run once per day at 03:00 UTC; can be overridden by env var.

---

## 2  Sub‑Tasks

| Key                        | Title                                                      | What / Why                                                                                                                   | Acceptance Criteria |
| -------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **3‑A APScheduler Setup**  | Integrate scheduler, add startup event                     | Scheduler starts with app, survives auto‑reload via `FastAPI lifespan`; job listed in `/jobs` debug route. citeturn0link1 |                     |
| **3‑B API Client Wrapper** | Resilient fetch with retry/back‑off (tenacity)             | Unit tests hit pytest‑httpx mock; ≥ 90 % branch coverage via `coverage xml`.                                                 |                     |
| **3‑C Upsert Logic**       | Insert or update `player` and `stat_line`                  | Running job twice for same date results in identical row counts (no dups).                                                   |                     |
| **3‑D Error Log Table**    | Persist failures in `ingest_log` with error msg & provider | Admin route `/admin/ingest-log` paginates 100 rows; manual clear button.                                                     |                     |
