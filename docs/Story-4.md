# FANTASY‑4 — Scoring Engine

> **Goal:** Convert raw `stat_line` rows into fantasy points per player and aggregate to team totals on a nightly schedule.

---

## 1  Context

League uses custom points (Pts 1, Reb 1.2, Ast/Stl/Blk 2, 3PM 1, TO −2, dbl‑dbl 5, trpl‑dbl 10). Engine must be deterministic, idempotent, and performant for \~5 k stat lines per season.

---

## 2  Sub‑Tasks

| Key                            | Title                                                               | What / Why                                                                                             | Acceptance Criteria |
| ------------------------------ | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------- |
| **4‑A Point Formula Function** | Stand‑alone Python function `calc_points(stats: StatLine) -> float` | Unit tests: triple‑double, negative TO, 40‑rebound edge. Reference ESPN scoring doc. citeturn0link1 |                     |
| **4‑B Engine Service**         | Batch iterate unscored `stat_line` rows, sum to `team_score`        | After run, each `team_score` has correct daily & season totals; db constraint prevents double count.   |                     |
| **4‑C Cron Trigger**           | APScheduler job `recompute_scores` nightly 03:30 UTC                | Processes full season (<120 s on M1 Mac with 5 k rows). Timing logged in ingest\_log.                  |                     |
| **4‑D Backfill Command**       | CLI `python manage.py backfill 2024`                                | Drops existing scores for year, recomputes; prints duration; exit 0.                                   |                     |
