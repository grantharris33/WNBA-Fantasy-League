// WNBA team information
export interface WNBATeam {
  id: number;
  abbreviation: string;
  full_name: string;
  city: string;
  name: string;
  conference: string;
  primary_color: string | null;
  secondary_color: string | null;
  logo_url: string | null;
}

// Team standings information
export interface Standings {
  team_id: number;
  team_name: string;
  team_abbr: string;
  conference: string;
  wins: number;
  losses: number;
  win_percentage: number;
  games_behind: number | null;
  conference_rank: number;
  overall_rank: number;
  home_record: string;
  away_record: string;
  last_10: string;
  streak: string;
}

// WNBA game information
export interface Game {
  id: number;
  game_date: string; // ISO date string
  season: number;
  week: number;
  home_team_id: number;
  away_team_id: number;
  home_team_abbr: string;
  away_team_abbr: string;
  home_team_score: number | null;
  away_team_score: number | null;
  status: string; // "scheduled", "in_progress", "final", "postponed", "cancelled"
  period: number | null;
  time_remaining: string | null;
  venue: string | null;
  attendance: number | null;
  
  // Metadata
  created_at: string | null;
  updated_at: string | null;
}

// Game with team details
export interface GameWithTeams extends Game {
  home_team: WNBATeam;
  away_team: WNBATeam;
}

// Team roster player (simplified for roster display)
export interface TeamRosterPlayer {
  player_id: number;
  player_name: string;
  position: string | null;
  jersey_number: string | null;
  height: number | null;
  weight: number | null;
  college: string | null;
  years_pro: number | null;
  status: string;
}

export default WNBATeam;