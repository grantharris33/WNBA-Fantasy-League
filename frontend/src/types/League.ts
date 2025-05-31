export interface LeagueBasic {
  id: number;
  name: string;
}

export interface LeagueOut extends LeagueBasic {
  commissioner_id: number | null;
  created_at: string | null;
  invite_code: string | null; // Only included if user is commissioner
  max_teams: number;
  draft_date: string | null;
  settings: Record<string, unknown>;
  is_active: boolean;
}

export interface LeagueCreate {
  name: string;
  max_teams?: number;
  draft_date?: string;
  settings?: Record<string, unknown>;
}

export interface LeagueUpdate {
  name?: string;
  max_teams?: number;
  draft_date?: string;
  settings?: Record<string, unknown>;
}

export interface JoinLeagueRequest {
  invite_code: string;
  team_name: string;
}

export interface LeagueWithRole {
  league: LeagueOut;
  role: 'commissioner' | 'member';
}

export interface InviteCodeResponse {
  invite_code: string;
}