// Comprehensive Player interface matching backend PlayerOut schema
export interface Player {
  id: number;
  full_name: string;
  position: string | null;
  team_abbr: string | null;

  // Biographical fields
  first_name: string | null;
  last_name: string | null;
  jersey_number: string | null;
  height: number | null; // in inches
  weight: number | null; // in pounds
  birth_date: string | null; // ISO date string
  birth_place: string | null;
  college: string | null;
  draft_year: number | null;
  draft_round: number | null;
  draft_pick: number | null;
  years_pro: number | null;
  status: string; // "active", "injured", "inactive"
  headshot_url: string | null;

  // Metadata
  created_at: string | null; // ISO date string
  updated_at: string | null; // ISO date string
  team_id: number | null;

  // Waiver wire
  waiver_expires_at: string | null; // ISO date string
}

// Simplified Player interface for cases where full data isn't needed
export interface PlayerBasic {
  id: number;
  full_name: string;
  position?: string | null;
  team_abbr?: string | null;
}

// Player with 2024 season stats for draft comparison
export interface PlayerWithStats extends Player {
  stats_2024?: {
    ppg: number;
    rpg: number;
    apg: number;
    spg: number;
    bpg: number;
    fg_percentage: number;
    three_point_percentage: number;
    ft_percentage: number;
    mpg: number;
    fantasy_ppg: number;
    games_played: number;
  } | null;
}

// Comprehensive player statistics from a game
export interface ComprehensivePlayerStats {
  player_id: number;
  player_name: string;
  position: string | null;
  is_starter: boolean;
  did_not_play: boolean;

  // Basic stats
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;

  // Detailed stats
  minutes_played: number;
  field_goals_made: number;
  field_goals_attempted: number;
  field_goal_percentage: number;
  three_pointers_made: number;
  three_pointers_attempted: number;
  three_point_percentage: number;
  free_throws_made: number;
  free_throws_attempted: number;
  free_throw_percentage: number;

  // Advanced stats
  offensive_rebounds: number;
  defensive_rebounds: number;
  turnovers: number;
  personal_fouls: number;
  plus_minus: number;
  fantasy_points: number;
}

// Player game log entry
export interface PlayerGameLog {
  game_id: number;
  player_id: number;
  game_date: string;
  opponent: string;
  stats: ComprehensivePlayerStats;
}

// League leader entry
export interface LeagueLeader {
  player_id: number;
  player_name: string;
  position: string | null;
  team_abbr: string | null;
  stat_value: number;
  stat_category: string;
}

// Detailed player stats for roster management
export interface DetailedPlayerStats {
  player_id: number;
  season_stats: ComprehensivePlayerStats;
  recent_games: PlayerGameLog[];
  fantasy_avg: number;
  injury_status: string | null;
}

export default Player;