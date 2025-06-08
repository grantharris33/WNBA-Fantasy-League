/**
 * Waiver wire related TypeScript types and interfaces
 */

export interface WaiverClaim {
  id: number;
  team_id: number;
  player_id: number;
  player_name: string;
  player_position?: string;
  drop_player_id?: number;
  drop_player_name?: string;
  priority: number;
  status: 'pending' | 'successful' | 'failed' | 'cancelled';
  created_at: string; // ISO datetime string
  processed_at?: string; // ISO datetime string
}

export interface WaiverClaimRequest {
  player_id: number;
  drop_player_id?: number;
  priority?: number;
}

export interface WaiverPlayer {
  id: number;
  full_name: string;
  position?: string;
  team_abbr?: string;
  waiver_expires_at?: string; // ISO datetime string
  is_on_waivers: boolean;
}

export interface WaiverPriority {
  team_id: number;
  team_name?: string;
  priority: number;
}

export enum WaiverType {
  REVERSE_STANDINGS = 'reverse_standings',
  CONTINUAL_ROLLING = 'continual_rolling',
  FAAB = 'faab'
}

export interface WaiverSettings {
  waiver_period_days: number;
  waiver_type: WaiverType;
}

export interface WaiverProcessingResult {
  total_claims: number;
  successful_claims: number;
  failed_claims: number;
  processed_leagues: number;
  errors: string[];
}

// API Response types
export interface WaiverClaimResponse extends WaiverClaim {}

export interface WaiverPlayerResponse extends WaiverPlayer {}

export interface WaiverPriorityResponse extends WaiverPriority {}