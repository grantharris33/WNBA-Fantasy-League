# FANTASY‑13 — Scoreboard & Standings UI

> **Goal:** Build a responsive dashboard that shows league standings, weekly trends, and top performers so users can quickly gauge who’s winning.

---

## 1  Design Notes

* Layout: **Card grid** — Standings table left, sparkline + performers right on desktop; stacked on mobile.
* Charts: Use `react-chartjs-2` wrapper around Chart.js for sparklines. MUI X sparkline is an alternative.
* Data source: `/api/v1/scores/current` (see FANTASY‑5) already includes weekly delta & bonus summaries.

---

## 2  Sub‑Tasks

| Key                            | Title                                                                           | What / Why                                                                                                                                           | Acceptance Criteria |
| ------------------------------ | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **13‑A Standings Table**       | Create React table component listing Team, Season Pts, Weekly Δ                 | Fetches from `/scores/current`; sorts desc by Season Pts; refreshes every 30 s via SWR.                                                              |                     |
| **13‑B Sparkline Component**   | Mini line chart shows last 4 weekly totals per team                             | Uses Chart.js sparkline or MUI X sparkline; renders within each table row; unit test mounts component with sample data. citeturn0link1turn0link2 |                     |
| **13‑C Top Performers Widget** | Side card shows top 3 players of current week with avatar, stat line, bonus pts | Data from `/scores/current` `top_players` field; displays player photo from CDN fallback.                                                            |                     |
