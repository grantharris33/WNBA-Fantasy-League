# FANTASY‑11 — Weekly Bonus Calculator

> **Goal:** Each Sunday night compute objective weekly leader bonuses (Top Scorer, Top Rebounder, etc.) and add them to team totals.

---

## 1  Bonus Rules Recap

| Category             | Stat Logic                              | Points |
| -------------------- | --------------------------------------- | ------ |
| Top Scorer           | Highest cumulative **PTS** for the week | +5     |
| Top Rebounder        | Highest **REB**                         | +4     |
| Top Playmaker        | Highest **AST**                         | +4     |
| Defensive Beast      | Highest **(STL + BLK)**                 | +4     |
| Efficiency Award     | Best **FG%** (≥ 3 games)                | +3     |
| Double‑Double Streak | ≥ 2 double‑doubles in week              | +5     |
| Triple‑Double        | Each triple‑double logged               | +10    |

Ties → all tied players receive bonus; team receives sum of its players’ awards.

---

## 2  Sub‑Tasks

| Key                     | Title                                                                                    | What / Why                                                                                                     | Acceptance Criteria |
| ----------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------- |
| **11‑A Ranking Query**  | Write SQLModel/SQL to compute weekly leaders in Pts, Reb, Ast, Stl+Blk, FG%              | For fixture data with tie, query returns both player\_ids; unit test asserts tie handling.                     |                     |
| **11‑B Bonus Table**    | Create `weekly_bonus` table with `week_id`, `player_id`, `team_id`, `category`, `points` | `/api/v1/scores/current` aggregates these rows into weekly\_delta; OpenAPI updated.                            |                     |
| **11‑C Scheduler Hook** | APScheduler job `calc_weekly_bonuses` Sunday 23:59 local → 05:59 UTC                     | Unit test uses `freezegun` to mock datetime; after run, `weekly_bonus` rows inserted; no duplicates on re‑run. |                     |
