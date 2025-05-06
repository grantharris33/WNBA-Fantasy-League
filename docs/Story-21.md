**Jira Story: FANTASY-21 — League-Wide Information Access (Schedule, News, Injuries)**

> **Goal:** Provide frontend with access to league-wide information such as WNBA game schedules for a specific date, latest general WNBA news, and overall league injury reports.
>
> **Acceptance Criteria:**
> -   Frontend can retrieve WNBA game schedule by specifying a date.
> -   Frontend can retrieve a list of recent WNBA news articles with a configurable limit.
> -   Frontend can retrieve a league-wide injury report.
> -   All endpoints are documented via OpenAPI and return data structured by Pydantic schemas.

**Tasks for FANTASY-21:**

1.  **FANTASY-21A: WNBA Schedule by Date Endpoint**
    *   **Description:** Create a `GET /api/v1/schedule` endpoint that accepts an optional `date` (YYYY-MM-DD) query parameter. If no date is provided, it could default to the current day or yesterday.
    *   **Sub-Tasks:**
        *   Define `ScheduledGameCompetitorOut`, `ScheduledGameOut`, and `ScheduleDayOut` (containing a list of games for that day) Pydantic schemas based on `/wnbaschedule` response.
        *   Adapt/use the `fetch_schedule(date_iso: str)` logic (from `app/jobs/ingest.py`, now in `RapidApiClient`) to take year, month, day. The endpoint can parse the input `date` string.
        *   Implement the FastAPI endpoint.
        *   Map RapidAPI response to `ScheduleDayOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/wnbaschedule`.

2.  **FANTASY-21B: WNBA News Endpoint**
    *   **Description:** Create a `GET /api/v1/news` endpoint that accepts an optional `limit` query parameter.
    *   **Sub-Tasks:**
        *   Define `NewsArticleOut` Pydantic schema to structure news items from `/wnba-news`.
        *   Add `async def fetch_wnba_news(self, limit: int = 20)` method to `RapidApiClient`.
        *   Implement the FastAPI endpoint.
        *   Map RapidAPI response to a list of `NewsArticleOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/wnba-news`.

3.  **FANTASY-21C: League-Wide Injuries Endpoint**
    *   **Description:** Create a `GET /api/v1/injuries` endpoint to fetch league-wide injury information.
    *   **Sub-Tasks:**
        *   Define `PlayerInjuryDetailOut`, `TeamInjuryListOut`, and `LeagueInjuryReportOut` Pydantic schemas based on `/injuries` response.
        *   Add `async def fetch_league_injuries(self)` method to `RapidApiClient`.
        *   Implement the FastAPI endpoint.
        *   Map RapidAPI response to `LeagueInjuryReportOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/injuries`.