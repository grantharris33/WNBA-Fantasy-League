# API Field Mapping (Box Score per-player)

_Only endpoints exposing per-player box-scores were compared._

| Unified Field | RapidAPI – WNBA Stats | Notes |
|---------------|----------------------|-------|
| `player_id` | `athlete.id` | numeric string |
| `team_id` | parent team object → `team.id` | |
| `minutes` | `stats[0]` labelled "minutes" | String → convert "32" to int |
| `fgm` | parse `fieldGoalsMade-fieldGoalsAttempted` → split before dash | |
| `fga` | parse same | |
| `fg3m` | parse `threePointFieldGoalsMade-threePointFieldGoalsAttempted` | |
| `fg3a` | ^ | |
| `ftm` | parse `freeThrowsMade-freeThrowsAttempted` | |
| `fta` | ^ | |
| `oreb` | `offensiveRebounds` | |
| `dreb` | `defensiveRebounds` | |
| `reb` | `rebounds` | |
| `ast` | `assists` | |
| `stl` | `steals` | |
| `blk` | `blocks` | |
| `tov` | `turnovers` | |
| `pf` | `fouls` | |
| `plus_minus` | `plusMinus` | signed int |
| `pts` | `points` | |

> Other candidate APIs did not supply granular per-player stat lines, making direct mapping impossible.