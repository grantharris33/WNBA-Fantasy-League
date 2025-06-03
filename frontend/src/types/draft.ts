export interface Player {
  id: number;
  full_name: string;
  position?: string | null;
  team_abbr?: string | null;
  // 2024 season stats for draft comparison
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

export interface DraftPick {
  id: number;
  round: number;
  pick_number: number;
  team_id: number;
  team_name: string;
  player_id: number;
  player_name: string;
  player_position?: string | null;
  timestamp: string; // Consider using Date type after parsing
  is_auto: boolean;
}

export interface DraftState {
  id: number;
  league_id: number;
  current_round: number;
  current_pick_index: number;
  status: 'pending' | 'active' | 'paused' | 'completed'; // More specific than string
  seconds_remaining: number;
  current_team_id: number;
  picks: DraftPick[];
}

// For WebSocket messages, specific event types
export interface DraftStartedEvent {
  type: 'draft_started';
  data: DraftState;
}

export interface PickMadeEvent {
  type: 'pick_made';
  data: {
    pick: DraftPick;
    updated_draft: DraftState; // Or just the parts of draft state that changed
  };
}

export interface DraftPausedEvent {
  type: 'draft_paused';
  data: DraftState; // Or just the updated status and relevant fields
}

export interface DraftResumedEvent {
  type: 'draft_resumed';
  data: DraftState; // Or just the updated status and relevant fields
}

export interface DraftCompletedEvent {
  type: 'draft_completed';
  data: {
    status: 'completed';
    // Potentially final draft state or summary
  };
}

// Union type for all possible WebSocket messages
export type DraftWebSocketMessage =
  | DraftStartedEvent
  | PickMadeEvent
  | DraftPausedEvent
  | DraftResumedEvent
  | DraftCompletedEvent;

// For the user's team(s)
export interface UserTeam {
  id: number;
  name: string;
  league_id: number;
  // any other relevant team properties
}

export interface League {
  id: number;
  name: string;
  commissioner_id?: number;
  created_at?: string; // or Date
}