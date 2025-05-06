# FANTASY‑1 — Spike: Research Free RapidAPI WNBA Stat APIs

> **Goal:** Research the RapidAPI WNBA API and prepare a test PoC fetch script along with a recommendation memo describing how the rest of the app should be strutuctured to make use of the API
>
> **Outcome:** PoC fetch script • data‑shape comparison • recommendation memo.

---

**Status:** Complete

## 1  Context

Small private league ⇒ low request volume (< 500 calls / day). We need:

1. Player & game endpoints with per‑game box‑score stats.
2. Historical seasons ≥ 2018.
3. Free tier or open API key.

Candidate:

* **RapidAPI WNBA Stats** — various community endpoints; rate‑limit depends on plan (Using https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/wnba-api)

---

## 2  Sub‑Tasks

| Key                            | Title                                                         | What / Why                                                                                          | Acceptance Criteria                                                                    |
| ------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **1‑A Compile Candidates**     | Research docs, rate‑limits, season coverage                   | Produce table `docs/api_candidates.md` listing **base URL**, **auth**, **daily cap**, **seasons**.  | Table includes balldontlie + TheSportsDB + ≥1 RapidAPI endpoint; seasons ≥ 2018 noted. |
| **1‑B Prototype Fetch Script** | Create PoC script `scripts/fetch_demo.py`                     | `python scripts/fetch_demo.py 2025-05-04` prints ≥ 5 players’ box‑scores from the games that happened in last 24 hours.        |                                                                                        |
| **1‑C Compare Data Shapes**    | Map JSON to unified fields (pts, reb, ast, stl, blk, 3pm, to) | Markdown matrix saved `docs/api_comparison.md`.                                                     |                                                                                        |
| **1‑D Recommendation Memo**    | Outline architecture for interacting with RadidAPI WNBA API                                     | Memo `docs/api_recommendation.md` citing coverage, freshness, free tier; decision logged in ticket. |                                                                                        |
