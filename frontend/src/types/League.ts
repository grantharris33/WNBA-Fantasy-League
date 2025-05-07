export interface LeagueOut {
  id: number;
  name: string;
  description: string | null;
  draft_status: string;
  draft_date: string | null;
  owner_id: number;
  created_at: string;
}