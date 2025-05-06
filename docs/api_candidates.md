# WNBA Stat API – Candidate Comparison

| Provider | Base URL | Auth Method | Free Daily Cap | Seasons Available (as of 2024) | Notes |
|----------|----------|-------------|----------------|---------------------------------|-------|
| **balldontlie** | https://www.balldontlie.io/api/v1 | None (open) | Unlimited (public CDN, polite usage) | NBA only – _no WNBA_ | Not suitable – NBA data only. |
| **TheSportsDB** | https://www.thesportsdb.com/api/v1/json/ | API key (free) | 1 000 / day on free tier | Some WNBA seasons (irregular coverage) | Team / player endpoints but _no box-scores_. |
| **RapidAPI – WNBA Stats** (<https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/wnba-api>) | https://wnba-api.p.rapidapi.com | `X-RapidAPI-Key` header | 1 000 / hr · 500 K / month (platform global free limits) | Historical ≥ 2018 plus current (2025) | Has **schedule, teams, box-scores, player + team stats**. Single unified JSON derived from ESPN feed. |

> The RapidAPI endpoint is the only option that exposes per-game box-scores and covers all modern WNBA seasons while fitting within the free-tier request budget (<500 calls / day).