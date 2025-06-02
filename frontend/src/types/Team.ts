import type { LeagueBasic } from './League';
import type { Player } from './draft';

export interface UserTeam {
  id: number;
  name: string;
  league_id: number | null;
  owner_id: number | null;
  moves_this_week: number;
  roster?: Player[]; // For backward compatibility
  roster_slots?: RosterSlot[]; // New detailed roster information
  season_points: number;
  league?: LeagueBasic; // Optional: If the API nests basic league info
  // Add other team-specific properties as needed from the API response
}

// New types for roster management
export interface RosterSlot {
  id: number;
  player_id: number;
  position?: string | null;
  is_starter: boolean;
  player?: Player;
}

export interface TeamWithRosterSlots extends Omit<UserTeam, 'roster'> {
  roster_slots: RosterSlot[];
}

export interface AddPlayerRequest {
  player_id: number;
  set_as_starter?: boolean;
}

export interface DropPlayerRequest {
  player_id: number;
}

export interface SetStartersRequest {
  starter_player_ids: number[];
}

export interface Pagination<T> {
  total: number;
  limit: number;
  offset: number;
  items: T[];
}