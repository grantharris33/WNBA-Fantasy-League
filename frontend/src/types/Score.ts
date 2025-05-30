export interface BonusDetail {
  reason: string;
  points: number;
}

export interface TeamScoreData {
  rank?: number; // To be calculated on the frontend
  team_id: number;
  team_name: string;
  owner_name?: string; // If available from API
  season_points: number;
  weekly_change: number; // e.g. +10, -5
  weekly_bonuses: BonusDetail[];
  // Potentially league_id if the scores are global and need filtering client-side
}

export interface CurrentScores {
  // Assuming the API returns a list of TeamScoreData
  // It might be wrapped in an object, e.g. { scores: TeamScoreData[] }
  scores: TeamScoreData[];
  last_updated: string; // ISO date string for when scores were last calculated
}