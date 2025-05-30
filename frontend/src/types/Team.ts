import type { LeagueBasic } from './League';

export interface UserTeam {
  id: number;
  name: string;
  league_id: number;
  league?: LeagueBasic; // Optional: If the API nests basic league info
  // Add other team-specific properties as needed from the API response
}