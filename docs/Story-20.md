**Jira Story: FANTASY-20 — Detailed WNBA Game Information Views**

> **Goal:** Enable frontend to display detailed information for specific WNBA games, including comprehensive summaries and live/historical play-by-play data.
>
> **Acceptance Criteria:**
> -   Frontend can retrieve game summaries and play-by-play data for a given `game_id`.
> -   Endpoints are documented via OpenAPI.
> -   Responses are strongly typed using Pydantic schemas.
> -   Graceful error handling for invalid `game_id` or API issues.

**Tasks for FANTASY-20:**

1.  **FANTASY-20A: Game Summary Endpoint**
    *   **Description:** Create a `GET /api/v1/games/{game_id}/summary` endpoint. This will use the `/wnbasummary` endpoint from RapidAPI, which includes box score, game info (venue, officials), etc.
    *   **Sub-Tasks:**
        *   Define `GameSummaryBoxScoreTeamOut`, `GameSummaryPlayerStatsOut`, `GameInfoOut`, and a composite `GameSummaryOut` Pydantic schema in `app/api/schemas.py`.
        *   Add `async def fetch_game_summary(self, game_id: str)` method to the `RapidApiClient`.
        *   Implement the FastAPI endpoint in `app/api/endpoints_v1.py` (or a new `game_router.py`).
        *   Map the RapidAPI response to `GameSummaryOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/wnbasummary`.

2.  **FANTASY-20B: Game Play-by-Play Endpoint**
    *   **Description:** Create a `GET /api/v1/games/{game_id}/playbyplay` endpoint.
    *   **Sub-Tasks:**
        *   Define `PlayByPlayEventOut`, `GamePlayByPlayOut` (containing a list of events and game context) Pydantic schemas.
        *   Add `async def fetch_game_playbyplay(self, game_id: str)` method to `RapidApiClient`.
        *   Implement the FastAPI endpoint.
        *   Map the RapidAPI response from `/wnbaplay` to schemas.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/wnbaplay`.