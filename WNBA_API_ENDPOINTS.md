# WNBA API Endpoints Documentation

This document describes the comprehensive set of API endpoints for accessing WNBA teams, standings, player statistics, and game data. These endpoints are designed to provide rich data for the frontend to display team and player names instead of IDs, and to offer detailed statistics and views for game pages.

## Base URL
All endpoints are prefixed with `/api/v1`

## WNBA Data Endpoints (`/api/v1/wnba`)

### Teams

#### Get All Teams
```
GET /api/v1/wnba/teams
```
Returns all WNBA teams with their basic information including names, abbreviations, logos, and current season stats.

#### Get Team by ID
```
GET /api/v1/wnba/teams/{team_id}
```
Returns detailed information for a specific team.

#### Get Team by Abbreviation
```
GET /api/v1/wnba/teams/by-abbreviation/{abbreviation}
```
Returns team information using the team abbreviation (e.g., "LAS", "NYL").

### Standings

#### Get Current Standings
```
GET /api/v1/wnba/standings?season={year}
```
Returns current league standings with wins, losses, win percentage, games behind, home/away records, and more.

### Team Details

#### Get Team Roster
```
GET /api/v1/wnba/teams/{team_id}/roster?season={year}
```
Returns the complete roster for a team including player stats and biographical information.

#### Get Team Schedule
```
GET /api/v1/wnba/teams/{team_id}/schedule?season={year}&limit={number}
```
Returns recent and upcoming games for a team with results and opponent information.

#### Get Team Statistics
```
GET /api/v1/wnba/teams/{team_id}/stats?season={year}
```
Returns aggregated team statistics including offensive and defensive averages.

### Player Data

#### Get Player Game Log
```
GET /api/v1/wnba/players/{player_id}/game-log?limit={number}
```
Returns recent game-by-game statistics for a player.

#### Get Detailed Player Stats
```
GET /api/v1/wnba/players/{player_id}/stats?season={year}
```
Returns comprehensive player statistics including advanced metrics like PER, true shooting percentage, usage rate, and fantasy scoring averages.

#### Search Players
```
GET /api/v1/wnba/players/search?query={name}&team_id={id}&position={pos}&limit={number}&offset={number}
```
Search for players with various filters including name, team, and position.

#### Get Trending Players
```
GET /api/v1/wnba/players/trending?limit={number}
```
Returns top performing players based on recent fantasy performance.

### League Leaders

#### Get League Leaders
```
GET /api/v1/wnba/league-leaders?stat_category={category}&season={year}&limit={number}
```
Returns league leaders in various statistical categories:
- `points` - Points per game
- `rebounds` - Rebounds per game
- `assists` - Assists per game
- `steals` - Steals per game
- `blocks` - Blocks per game
- `field_goal_percentage` - Field goal percentage
- `three_point_percentage` - Three-point percentage
- `free_throw_percentage` - Free throw percentage
- `minutes` - Minutes per game
- `fantasy_points` - Fantasy points per game

## Lookup Endpoints (`/api/v1/lookup`)

These endpoints provide quick lookups to resolve IDs to names and basic information.

#### Lookup Teams
```
GET /api/v1/lookup/teams?team_ids={comma_separated_ids}
```
Returns a dictionary mapping team IDs to their names, abbreviations, and logo URLs.

#### Lookup Players
```
GET /api/v1/lookup/players?player_ids={comma_separated_ids}
```
Returns a dictionary mapping player IDs to their names, positions, jersey numbers, and team information.

#### Batch Lookup
```
GET /api/v1/lookup/batch?team_ids={ids}&player_ids={ids}
```
Performs both team and player lookups in a single request.

## Enhanced Game Endpoints (`/api/v1/games`)

#### Enhanced Game View
```
GET /api/v1/games/{game_id}/enhanced
```
Returns comprehensive game data with:
- Full team names and logos instead of IDs
- Player names and detailed statistics
- Team totals and shooting percentages
- Game leaders in key statistical categories
- Properly sorted player lists (starters first)

This endpoint is specifically designed for rich game page displays.

## Usage Examples

### Frontend Integration for Name Resolution

Instead of showing "Team ID: 123", use:
```javascript
// Lookup multiple teams at once
const response = await fetch('/api/v1/lookup/teams?team_ids=1,2,3');
const teams = await response.json();
// teams[1].name gives you the team name
```

### Rich Game Page Data

```javascript
// Get enhanced game view
const response = await fetch('/api/v1/games/12345/enhanced');
const gameData = await response.json();

// Now you have:
// gameData.home_team.name - Team name
// gameData.home_team.players - Array of players with full details
// gameData.home_team.totals - Team statistical totals
// gameData.game_leaders - Top performers in the game
```

### Player Statistics for Fantasy

```javascript
// Get detailed player stats
const response = await fetch('/api/v1/wnba/players/456/stats?season=2024');
const playerStats = await response.json();

// Includes fantasy_ppg, consistency_score, ceiling, floor, etc.
```

### League Standings

```javascript
// Get current standings
const response = await fetch('/api/v1/wnba/standings');
const standings = await response.json();

// Each team includes rank, record, games behind, etc.
```

## Response Formats

All endpoints return JSON responses with consistent formatting:
- Dates are in ISO format
- Statistics are rounded to appropriate decimal places
- Missing data is handled gracefully with null values or empty arrays
- Pagination is provided for large datasets using `limit` and `offset` parameters

## Error Handling

- `404` - Resource not found (team, player, game)
- `400` - Invalid parameters (malformed IDs, invalid stat categories)
- `500` - Server errors

All error responses include a `detail` field with a description of the error.

## Performance Notes

- The lookup endpoints are optimized for quick batch operations
- Player search is limited to prevent excessive database queries
- Season statistics are cached when possible
- Use the batch lookup endpoint when resolving multiple IDs simultaneously