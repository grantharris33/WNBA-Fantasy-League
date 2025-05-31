import type { LeagueBasic } from './League';
import type { Player } from './draft';

export interface UserTeam {
  id: number;
  name: string;
  league_id: number | null;
  owner_id: number | null;
  moves_this_week: number;
  roster: Player[];
  season_points: number;
  league?: LeagueBasic; // Optional: If the API nests basic league info
  // Add other team-specific properties as needed from the API response
}