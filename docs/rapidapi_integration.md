# WNBA RapidAPI Integration

This document describes the RapidAPI integration for fetching real WNBA data, including setup instructions, subscription requirements, and endpoint documentation.

## Overview

The application uses the [WNBA API on RapidAPI](https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/wnba-api) to fetch:
- Game schedules
- Player statistics and box scores
- Game summaries and play-by-play data
- WNBA news
- Injury reports

## Setup Instructions

### 1. RapidAPI Subscription

1. Go to [WNBA API on RapidAPI](https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/wnba-api)
2. Sign up for a RapidAPI account if you don't have one
3. Subscribe to the WNBA API:
   - **Basic Plan**: 500 requests/month (free)
   - **Pro Plan**: 10,000 requests/month (paid)
   - **Ultra Plan**: 100,000 requests/month (paid)

### 2. API Key Configuration

1. After subscribing, copy your API key from the RapidAPI dashboard
2. Set the environment variable:
   ```bash
   export RAPIDAPI_KEY="your_api_key_here"
   # OR alternatively:
   export WNBA_API_KEY="your_api_key_here"
   ```
3. For production deployment, add the key to your environment configuration

### 3. Testing the Integration

Run the test script to verify everything works:
```bash
cd /path/to/project
python scripts/test_real_api.py
```

This will test all endpoints and validate data parsing.

## API Endpoints Used

### 1. Schedule Endpoint (`/wnbaschedule`)
- **Purpose**: Fetch game schedules for specific dates
- **Parameters**: `year`, `month`, `day`
- **Response**: List of games with teams, scores, and game IDs
- **Usage**: `await wnba_client.fetch_schedule("2024", "07", "15")`

### 2. Box Score Endpoint (`/wnbabox`)
- **Purpose**: Fetch detailed player statistics for completed games
- **Parameters**: `gameId`
- **Response**: Player stats in format `[MIN, FG, 3PT, FT, OREB, DREB, REB, AST, STL, BLK, TO, PF, +/-, PTS]`
- **Usage**: `await wnba_client.fetch_box_score("401244185")`

### 3. Game Summary Endpoint (`/wnbasummary`)
- **Purpose**: Fetch game summary and basic stats
- **Parameters**: `gameId`
- **Response**: Game summary with key statistics
- **Usage**: `await wnba_client.fetch_game_summary("401244185")`

### 4. Play-by-Play Endpoint (`/wnbaplay`)
- **Purpose**: Fetch detailed play-by-play data
- **Parameters**: `gameId`
- **Response**: Chronological list of game events
- **Usage**: `await wnba_client.fetch_game_playbyplay("401244185")`

### 5. News Endpoint (`/wnba-news`)
- **Purpose**: Fetch recent WNBA news articles
- **Parameters**: `limit` (optional)
- **Response**: List of news articles
- **Usage**: `await wnba_client.fetch_wnba_news(limit=10)`

### 6. Injuries Endpoint (`/injuries`)
- **Purpose**: Fetch league-wide injury information
- **Parameters**: None
- **Response**: Injury reports for all teams
- **Usage**: `await wnba_client.fetch_league_injuries()`

## Data Processing

### Player Statistics Parsing

The box score endpoint returns player stats as an array of strings. The parsing logic in `app/jobs/ingest.py` maps these to our database fields:

```python
# Stats array format: [MIN, FG, 3PT, FT, OREB, DREB, REB, AST, STL, BLK, TO, PF, +/-, PTS]
# Indices:             [0,   1,  2,   3,  4,    5,    6,   7,   8,   9,   10, 11, 12,  13]

stats = ['32', '7-15', '0-0', '4-4', '0', '6', '6', '4', '1', '1', '1', '3', '-23', '18']

parsed = {
    "points": float(stats[13]),      # PTS - 18
    "rebounds": float(stats[6]),     # REB - 6
    "assists": float(stats[7]),      # AST - 4
    "steals": float(stats[8]),       # STL - 1
    "blocks": float(stats[9]),       # BLK - 1
}
```

### Error Handling

The client includes robust error handling for:
- **Rate Limiting (429)**: Raises `RateLimitError`
- **Authentication (401/403)**: Raises `ApiKeyError`
- **General API Errors**: Raises `RapidApiError`
- **Network Issues**: Raises `RapidApiError`

All errors are logged to the `ingest_log` table for monitoring.

## Usage in Jobs

### Daily Data Ingestion

The `ingest_stat_lines()` function runs daily to:
1. Fetch the previous day's game schedule
2. For each game, fetch the box score
3. Parse player statistics
4. Upsert data to the `players` and `stat_lines` tables

```python
# Manual execution
from app.jobs.ingest import ingest_stat_lines
import datetime as dt

# Ingest data for specific date
target_date = dt.date(2024, 7, 15)
await ingest_stat_lines(target_date)
```

### Scheduled Execution

The ingest job should be scheduled to run daily via:
- Cron job
- Kubernetes CronJob
- Cloud scheduler (AWS EventBridge, GCP Cloud Scheduler)

Example cron entry:
```bash
# Run daily at 6 AM UTC (after games are completed)
0 6 * * * cd /path/to/project && poetry run python -c "import asyncio; from app.jobs.ingest import ingest_stat_lines; asyncio.run(ingest_stat_lines())"
```

## Rate Limiting Considerations

- **Basic Plan**: 500 requests/month (~16 requests/day)
- **Typical Usage**:
  - 1 request for schedule
  - 3-6 requests for box scores (depending on games that day)
  - Total: ~7 requests/day during season
- **Recommendation**: Basic plan sufficient for development, Pro plan for production

## Monitoring

### Logs

All API interactions are logged to the `ingest_log` table:
```sql
SELECT * FROM ingest_log
WHERE provider = 'rapidapi'
ORDER BY timestamp DESC
LIMIT 10;
```

### Health Checks

Use the test script for health monitoring:
```bash
# Returns exit code 0 on success, 1 on failure
python scripts/test_real_api.py
```

### Metrics to Monitor

- API response times
- Error rates by endpoint
- Daily request volume
- Rate limit exceptions

## Troubleshooting

### Common Issues

1. **"API key error"**:
   - Verify `RAPIDAPI_KEY` environment variable is set
   - Check subscription is active on RapidAPI dashboard
   - Ensure key has proper permissions

2. **"Rate limit exceeded"**:
   - Upgrade subscription plan
   - Implement request throttling
   - Review daily usage patterns

3. **"No games found"**:
   - Normal during off-season
   - Verify date format (YYYY-MM-DD)
   - Check WNBA season schedule

4. **Stats parsing errors**:
   - API response format may have changed
   - Check sample responses in `scripts/` directory
   - Update parsing logic if needed

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development Notes

### Local Testing

For development without consuming API requests:
1. Use sample data in `scripts/rapidapi_*_output.txt`
2. Mock the API client in tests
3. Set up a staging environment with separate API key

### API Response Changes

If the API response format changes:
1. Update sample files in `scripts/`
2. Modify parsing logic in `app/jobs/ingest.py`
3. Update tests in `tests/test_rapidapi_client.py`
4. Run comprehensive tests with `scripts/test_real_api.py`

## Security

- Store API keys securely (environment variables, secrets manager)
- Use HTTPS for all requests (handled by httpx)
- Implement request signing if required by future API versions
- Monitor for suspicious API usage patterns