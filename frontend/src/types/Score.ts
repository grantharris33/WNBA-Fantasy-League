export interface BonusDetail {
  category: string;
  points: number;
  player_name: string;
}

export interface TeamScoreData {
  rank?: number; // To be calculated on the frontend
  team_id: number;
  team_name: string;
  owner_name?: string; // If available from API
  season_points: number;
  weekly_delta: number; // Changed from weekly_change to match API
  weekly_bonus_points: number;
  bonuses: BonusDetail[]; // Changed from weekly_bonuses to match API
  // Potentially league_id if the scores are global and need filtering client-side
}

// The API returns an array of TeamScoreData directly
export type CurrentScores = TeamScoreData[];

// New types for enhanced scoreboard features

export interface PlayerScoreBreakdown {
  player_id: number;
  player_name: string;
  position?: string;
  points_scored: number;
  games_played: number;
  is_starter: boolean;
}

export interface TeamScoreHistory {
  team_id: number;
  team_name: string;
  week: number;
  weekly_score: number;
  season_total: number;
  rank: number;
  player_breakdown: PlayerScoreBreakdown[];
}

export interface WeeklyScores {
  week: number;
  scores: TeamScoreHistory[];
}

export interface LeagueChampion {
  team_id: number;
  team_name: string;
  owner_name?: string;
  final_score: number;
  weeks_won: number;
}

export interface TopPerformer {
  player_id: number;
  player_name: string;
  team_name: string;
  position?: string;
  points_scored: number;
  category: string; // e.g., "top_scorer", "top_rebounder"
}

export interface ScoreTrend {
  team_id: number;
  team_name: string;
  weekly_scores: number[];
  weeks: number[];
}