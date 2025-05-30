export interface LeagueBasic {
  id: number;
  name: string;
}

export interface LeagueOut extends LeagueBasic {
  description: string | null;
  draft_status: string; // Consider using an enum: 'PRE_DRAFT', 'ACTIVE', 'COMPLETE'
  draft_date: string | null;
  owner_id: number;
  created_at: string;
  // Add commissioner_id if available and needed
}