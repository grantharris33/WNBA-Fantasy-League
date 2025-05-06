**Jira Story: FANTASY-22 — Detailed WNBA Team Information and Status**

> **Goal:** Equip the frontend with endpoints to fetch detailed information, schedules, transactions, injuries, and depth charts for specific WNBA teams (not fantasy teams).
>
> **Acceptance Criteria:**
> -   Frontend can retrieve comprehensive details for any WNBA team using a consistent identifier (e.g., WNBA team ID or abbreviation).
> -   Endpoints are documented via OpenAPI and utilize Pydantic schemas for responses.
> -   The system can resolve team identifiers if necessary (e.g., abbreviation to RapidAPI's numeric ID).

**Tasks for FANTASY-22:**

*   **FANTASY-22A: WNBA Team ID Resolution & Caching Strategy**
    *   **Description:** Implement a mechanism to resolve WNBA team abbreviations (like 'LVA' or 'SEA') to the numeric IDs used by RapidAPI. This might involve fetching and caching the `/wnbateamlist` or `/team/id` data.
    *   **Sub-Tasks:**
        *   Add `async def fetch_wnba_team_list(self)` to `RapidApiClient`.
        *   Implement a utility function or a cached service (e.g., using a simple in-memory cache with TTL or Redis if available) that provides `get_wnba_team_id(abbreviation: str) -> Optional[str]`.
        *   This utility will be used by other tasks in this story.
    *   **RapidAPI Endpoints Used:** `/wnbateamlist` (or `/team/id`).

1.  **FANTASY-22B: WNBA Team Details & Statistics Endpoint**
    *   **Description:** Create a `GET /api/v1/wnba-teams/{team_identifier}/details` endpoint. `team_identifier` could be an abbreviation (e.g., "LVA") or the numeric ID. The backend will resolve to ID if an abbreviation is given.
    *   **Sub-Tasks:**
        *   Define `WnbaTeamInfoOut`, `WnbaTeamStatsOut`, and a composite `WnbaTeamDetailsOut` Pydantic schema.
        *   Add `async def fetch_wnba_team_info(self, team_id: str)` and `async def fetch_wnba_team_statistics(self, team_id: str)` methods to `RapidApiClient`.
        *   Implement the FastAPI endpoint (e.g., in a new `wnba_team_router.py`). It should use the resolution mechanism from FANTASY-22A.
        *   Combine and map RapidAPI responses from `/wnbateaminfo` and `/team-statistic` into `WnbaTeamDetailsOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoints Used:** `/wnbateaminfo`, `/team-statistic`.

2.  **FANTASY-22C: WNBA Team Schedule Endpoint**
    *   **Description:** Create `GET /api/v1/wnba-teams/{team_identifier}/schedule` endpoint, accepting optional `season=<YYYY>` and `seasonType=<type>` query parameters.
    *   **Sub-Tasks:**
        *   Define `TeamScheduledGameOut` and `WnbaTeamScheduleOut` Pydantic schemas based on `/team/schedulev2`.
        *   Add `async def fetch_wnba_team_schedule(self, team_id: str, season: str, season_type: Optional[str] = None)` method to `RapidApiClient`. (`seasonType` default is 2 in RapidAPI docs for `/team/schedulev2` but 1 in `/schedule-team` example, clarify if needed).
        *   Implement the FastAPI endpoint, resolving `team_identifier`.
        *   Map RapidAPI response to `WnbaTeamScheduleOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/team/schedulev2` (preferred) or `/schedule-team`.

3.  **FANTASY-22D: WNBA Team Transactions Endpoint**
    *   **Description:** Create `GET /api/v1/wnba-teams/{team_identifier}/transactions` endpoint, accepting an optional `year=<YYYY>` query parameter.
    *   **Sub-Tasks:**
        *   Define `TeamTransactionDetailOut` and `TeamTransactionsOut` (e.g., a dictionary mapping month to list of transactions) Pydantic schemas.
        *   Add `async def fetch_wnba_team_transactions(self, team_id: str, year: Optional[str] = None)` method to `RapidApiClient`.
        *   Implement the FastAPI endpoint, resolving `team_identifier`.
        *   Map RapidAPI response to `TeamTransactionsOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/team/transactions`.

4.  **FANTASY-22E: WNBA Team-Specific Injuries Endpoint**
    *   **Description:** Create `GET /api/v1/wnba-teams/{team_identifier}/injuries` endpoint.
    *   **Sub-Tasks:**
        *   Define `TeamSpecificInjuryOut` and `TeamSpecificInjuryReportOut` Pydantic schemas (can likely reuse or adapt from FANTASY-21C).
        *   Add `async def fetch_wnba_team_injuries(self, team_id: str)` method to `RapidApiClient`.
        *   Implement the FastAPI endpoint, resolving `team_identifier`.
        *   Map RapidAPI response to `TeamSpecificInjuryReportOut`.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/team/injuries`.

5.  **FANTASY-22F: WNBA Team Depth Chart Endpoint**
    *   **Description:** Create `GET /api/v1/wnba-teams/{team_identifier}/depth-chart` endpoint.
        *   *Note:* The API documentation shows a sparse example for `/team/depth`. The actual utility of this endpoint depends on the real data structure. This task might need further investigation once a live response can be inspected.
    *   **Sub-Tasks:**
        *   Investigate the actual response structure of `/team/depth`.
        *   Define `DepthChartPositionOut`, `TeamDepthChartOut` Pydantic schemas if feasible.
        *   Add `async def fetch_wnba_team_depth_chart(self, team_id: str)` method to `RapidApiClient`.
        *   Implement the FastAPI endpoint, resolving `team_identifier`.
        *   Map RapidAPI response.
        *   Write unit and integration tests.
    *   **RapidAPI Endpoint Used:** `/team/depth`.