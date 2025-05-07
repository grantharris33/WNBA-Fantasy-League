# FANTASY‑23 — Production Setup and Data Priming

> **Goal:** Create a script and processes to reliably set up a production-ready instance of the application with predefined users, a league, and all necessary WNBA player and statistical data for the current season (e.g., 2025) up to a specified date (e.g., the fantasy draft date).

---

## 1. Context & Requirements

For the initial MVP launch with a small group of friends, we need a way to:
1.  Create specific user accounts (4 fantasy participants + 1 admin).
2.  Create a fantasy league and associate the participating users with fantasy teams within this league. The admin user will be the commissioner.
3.  Populate the database with a comprehensive list of all draftable WNBA players for the current season (e.g., 2025).
4.  Ingest all historical player statistics (`StatLine` entries) for the current season from its official start date up to the fantasy draft date.
5.  Ensure that the fantasy scoring system can correctly account for player stats accrued *before* they were drafted onto a fantasy team, if league rules dictate this.

This setup process should be distinct from the local development seed script (`scripts/seed_demo.py`) and cater to a fresh production database.

---

## 2. Sub‑Tasks

| Key                       | Title                                                                      | Description & Deliverables                                                                                                                                                                                                                                                                                          | Acceptance Criteria                                                                                                                                                                                                                           |
| ------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **23-A: User/League Setup Script** | Create `scripts/setup_production_league.py`.                               | Script accepts parameters (or uses a config file) for 4 user emails/passwords and 1 admin email/password. Creates these users if they don't exist. Creates a "WNBA Fantasy 2025" league, assigns the admin as commissioner, and creates a fantasy team for each of the 4 participating users, linked to the league. | Script runs without errors. Specified users, league, and fantasy teams are created in the database. Admin is commissioner. Users can log in.                                                                                         |
| **23-B: Master Player List Ingestion** | Enhance/create a job or script function to populate `Player` table.      | Fetches all players from active WNBA team rosters at the start of the season (e.g., using RapidAPI's `/wnbateamlist` then `/players/id` for each team, or a similar comprehensive player listing endpoint). Stores `id`, `full_name`, `position`, `team_abbr` in the `Player` table. Should be runnable independently. | `Player` table contains a comprehensive list of 2025 WNBA players (e.g., >140 players). Player details are accurate.                                                                                                              |
| **23-C: Historical StatLine Ingestion Script** | Create `scripts/ingest_historical_stats.py`.                         | Script takes a start date and end date. For each date in the range, it calls the existing `app.jobs.ingest.ingest_stat_lines(target_date)` function. Logs progress and any errors to `IngestLog` and console.                                                                                                 | Script runs successfully. `StatLine` table is populated with player game stats for all games played between the start and end date of the 2025 season. `Player` table is updated/created for any players found in these historical stats. |
| **23-D: Define Pre-Draft Stat Attribution Rule** | Document and decide on scoring rule.                             | Decision on how (or if) `StatLine` data from before a player is drafted to a fantasy team contributes to that fantasy team's weekly score. E.g., "Stats for the entire ISO week of the draft count if player is on roster by end of week" OR "Only stats from day after draft count." | Clear rule documented.                                                                                                                                                                                                                        |
| **23-E: (If Needed) Modify Scoring Engine for Pre-Draft Stats** | Adjust `app.services.scoring.update_weekly_team_scores`. | Based on rule from 23-D, modify the scoring aggregation if necessary. For example, if retroactive scoring for the draft week is chosen, the query for `StatLine` might need to consider player's draft date.                                                                  | `TeamScore` reflects the chosen rule for pre-draft stats. Unit tests for scoring service cover this scenario.                                                                                                                             |
| **23-F: Update `setup_production_league.py`** | Integrate player and stat ingestion.                                 | The main setup script from 23-A should orchestrate calls to the master player list ingestion (23-B) and historical StatLine ingestion (23-C) for the 2025 season up to a configurable "draft day".                                                                   | Running the single `setup_production_league.py` script sets up users, league, teams, all 2025 players, and their stats up to the draft day.                                                                                          |

---

## 3. Open Questions / Considerations

*   **Source for Master Player List**: Confirm the best RapidAPI endpoint(s) for a full WNBA player roster dump at the start of a season.
*   **StatLine Ingestion for Past Dates**: The `ingest_stat_lines` function seems suitable for this. Ensure RapidAPI allows fetching historical data for the required period.
*   **Idempotency**: User/league creation should be idempotent. Stat ingestion is generally idempotent due to unique constraints (`uq_stat_line_player_date`).
*   **Configuration**: How will user details and dates be passed to the scripts? (e.g., CLI args, `.env` for production script, simple Python dict in the script). For initial MVP, hardcoding or simple dicts in the script might be acceptable for a one-off setup.