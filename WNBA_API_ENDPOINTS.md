# Fantasy WNBA League API Documentation

This document describes the comprehensive set of API endpoints for the WNBA Fantasy League application. The API covers everything from WNBA data and statistics to complete fantasy league management, including live drafts, roster management, scoring, and administration.

## Base URL
All endpoints are prefixed with `/api/v1` unless otherwise noted.

## Authentication
Most endpoints require authentication via JWT token. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

Get a token via:
```
POST /token
```

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

## Fantasy League Management

### User Management (`/users`)

#### Create User
```
POST /users/
```
Create a new user account with hashed password.

#### Get Current User
```
GET /users/me
GET /api/v1/me
```
Get current authenticated user's information.

### User Profile (`/api/v1/profile`)

#### Get Profile
```
GET /api/v1/profile
```
Get current user's detailed profile.

#### Update Profile
```
PUT /api/v1/profile
```
Update current user's profile information.

#### Profile Preferences
```
GET /api/v1/profile/preferences
PUT /api/v1/profile/preferences
```
Get and update user preferences and settings.

#### Avatar Management
```
POST /api/v1/profile/avatar
DELETE /api/v1/profile/avatar
```
Upload or delete user avatar image.

#### Account Settings
```
PUT /api/v1/profile/email
PUT /api/v1/profile/password
POST /api/v1/profile/verify-email/{token}
POST /api/v1/profile/resend-verification
```
Update email, password, and handle email verification.

### League Management (`/api/v1/leagues`)

#### Create League
```
POST /api/v1/leagues
```
Create a new fantasy league with custom settings.

#### Get Leagues
```
GET /api/v1/leagues
GET /api/v1/leagues/mine
```
List all leagues or get leagues where user has a team.

#### League Details
```
GET /api/v1/leagues/{league_id}
PUT /api/v1/leagues/{league_id}
DELETE /api/v1/leagues/{league_id}
```
Get, update, or delete league information.

#### Join League
```
POST /api/v1/leagues/join
```
Join a league using an invite code.

#### Invite Management
```
POST /api/v1/leagues/{league_id}/invite-code
```
Generate a new invite code for the league.

### Team Management

#### Create Team
```
POST /api/v1/leagues/{league_id}/teams
```
Create a new team in a league.

#### Team Operations
```
GET /api/v1/teams/{team_id}
PUT /api/v1/teams/{team_id}
DELETE /api/v1/leagues/{league_id}/teams/{team_id}
```
Get, update, or remove teams.

#### User Teams
```
GET /api/v1/users/me/teams
GET /api/v1/leagues/{league_id}/teams
```
Get user's teams or all teams in a league.

## Draft System

### Draft Management (`/draft`)

#### Start Draft
```
POST /draft/leagues/{league_id}/start
```
Initialize and start a draft for a league.

#### Draft Actions
```
POST /draft/{draft_id}/pick
POST /draft/{draft_id}/pause
POST /draft/{draft_id}/resume
```
Make picks, pause, or resume an active draft.

#### Draft State
```
GET /draft/{draft_id}/state
PUT /draft/{draft_id}/timer
```
Get current draft state or update timer settings.

#### Real-time Updates
```
WebSocket /draft/ws/{league_id}
```
WebSocket endpoint for real-time draft updates and notifications.

#### League Draft Info
```
GET /api/v1/leagues/{league_id}/draft/state
```
Get draft state for a specific league.

## Roster Management

### Free Agents
```
GET /api/v1/leagues/{league_id}/free-agents
```
Get available free agents for a league.

### Roster Operations
```
POST /api/v1/teams/{team_id}/roster/add
POST /api/v1/teams/{team_id}/roster/drop
PUT /api/v1/teams/{team_id}/roster/starters
```
Add/drop players and set starting lineup.

### Weekly Lineups
```
GET /api/v1/teams/{team_id}/lineups/{week_id}
GET /api/v1/teams/{team_id}/lineups/history
PUT /api/v1/teams/{team_id}/lineups/{week_id}/starters
```
Manage weekly lineups and view historical lineups.

#### Lineup Management (Admin)
```
POST /api/v1/admin/lineups/lock/{week_id}
```
Lock lineups for a specific week (admin only).

## Scoring System

### Current Scores
```
GET /api/v1/scores/current
```
Get current week's fantasy scores.

### Historical Data
```
GET /api/v1/scores/history
GET /api/v1/scores/trends
```
View score history and trends over time.

### League Leaders
```
GET /api/v1/scores/top-performers
GET /api/v1/scores/champion
```
Get top performers and league champion.

### Manual Updates
```
POST /scores/update
```
Manually trigger score calculation for current week.

## Analytics & Player Insights

### Player Analytics (`/api/v1/analytics`)

#### Player Performance
```
GET /api/v1/players/{player_id}/analytics
GET /api/v1/players/{player_id}/trends
```
Get comprehensive analytics and recent performance trends.

#### Projections
```
GET /api/v1/analytics/projections
```
Get fantasy projections for all players.

#### Matchup Analysis
```
GET /api/v1/players/{player_id}/matchup-history
```
Historical performance against specific teams.

#### Manual Calculation
```
POST /api/v1/analytics/calculate
```
Trigger analytics recalculation.

## Live Game Tracking

### Live Games (`/api/v1/live`)

#### Today's Games
```
GET /api/v1/live/games/today
```
Get all live games for today with current status.

#### Game Details
```
GET /api/v1/live/games/{game_id}
```
Get detailed live data for a specific game.

#### Fantasy Scoring
```
GET /api/v1/live/teams/{team_id}/fantasy-score
```
Get live fantasy score for a team.

#### Live Tracking Control (Admin)
```
POST /api/v1/live/games/{game_id}/start-tracking
POST /api/v1/live/games/{game_id}/stop-tracking
```
Start or stop live tracking for games.

#### Cache Management
```
GET /api/v1/live/cache/stats
```
Get cache statistics (admin only).

#### Real-time Updates
```
WebSocket /api/v1/live/ws/games/{game_id}
WebSocket /api/v1/live/ws/teams/{team_id}/fantasy-score
```
WebSocket endpoints for live game and fantasy score updates.

## Administration

### Admin Operations (`/api/v1/admin`)
*All admin endpoints require admin privileges*

#### Team Management
```
PUT /api/v1/admin/teams/{team_id}/lineups/{week_id}
POST /api/v1/admin/teams/{team_id}/weeks/{week_id}/recalculate
POST /api/v1/admin/teams/{team_id}/moves/grant
```
Modify lineups, recalculate scores, and grant additional moves.

#### Detailed Team Operations
```
GET /api/v1/admin/teams/{team_id}/lineup-history
GET /api/v1/admin/teams/{team_id}/weeks/{week_id}/lineup
POST /api/v1/admin/teams/{team_id}/weeks/{week_id}/grant-moves
GET /api/v1/admin/teams/{team_id}/weeks/{week_id}/move-summary
PUT /api/v1/admin/teams/{team_id}/weeks/{week_id}/force-roster
```
Advanced team management and move tracking.

#### Audit & Logging
```
GET /api/v1/admin/audit-log
GET /api/v1/logs
GET /api/v1/logs/ingest
```
View audit logs and system transaction logs.

#### Data Quality Management
```
GET /api/v1/admin/data-quality/dashboard
POST /api/v1/admin/data-quality/checks
GET /api/v1/admin/data-quality/checks
POST /api/v1/admin/data-quality/checks/{check_id}/run
```
Monitor and manage data quality checks.

## Additional Game Data

### Schedule & News (`/league_router`)

#### WNBA Schedule
```
GET /schedule
```
Get WNBA schedule for a specific date.

#### League Information
```
GET /news
GET /injuries
```
Get WNBA news and injury reports.

### Enhanced Game Data (`/games`)

#### Game Details
```
GET /games/{game_id}/summary
GET /games/{game_id}/playbyplay
GET /games/{game_id}/enhanced
GET /games/{game_id}/comprehensive-stats
```
Various levels of game data from summary to comprehensive statistics.

## Response Formats

All endpoints return JSON responses with consistent formatting:
- Dates are in ISO format
- Statistics are rounded to appropriate decimal places
- Missing data is handled gracefully with null values or empty arrays
- Pagination is provided for large datasets using `limit` and `offset` parameters

## Error Handling

- `401` - Unauthorized (invalid or missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Resource not found (team, player, game, league)
- `400` - Invalid parameters (malformed IDs, invalid stat categories)
- `409` - Conflict (draft already started, player already on roster)
- `500` - Server errors

All error responses include a `detail` field with a description of the error.

## WebSocket Connections

The application provides real-time updates via WebSocket for:
- **Draft updates**: `/draft/ws/{league_id}`
- **Live game tracking**: `/api/v1/live/ws/games/{game_id}`
- **Fantasy score updates**: `/api/v1/live/ws/teams/{team_id}/fantasy-score`

WebSocket connections require authentication and will broadcast relevant updates to connected clients.

## Performance Notes

- The lookup endpoints are optimized for quick batch operations
- Player search is limited to prevent excessive database queries
- Season statistics are cached when possible
- Use the batch lookup endpoint when resolving multiple IDs simultaneously
- Live game tracking uses efficient caching to minimize API calls
- WebSocket connections are managed efficiently with automatic cleanup