import { api } from './api';

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  admin_email: string;
  action: string;
  details: string;
  path?: string;
  method?: string;
}

export interface LineupHistoryEntry {
  week_id: number;
  lineup: Array<{
    player_id: number;
    player_name: string;
    position: string;
    team_abbr: string;
    is_starter: boolean;
  }>;
  admin_modified: boolean;
  modification_count: number;
  last_modified?: string;
}

export interface AdminActionResponse {
  success: boolean;
  message: string;
  data?: any;
}

export interface AdminLineupView {
  team_id: number;
  week_id: number;
  lineup: Array<{
    player_id: number;
    player_name: string;
    position: string;
    team_abbr: string;
    is_starter: boolean;
  }>;
  admin_modified: boolean;
  modification_count: number;
  last_modified?: string;
}

class AdminApiService {
  /**
   * Modify historical lineup for a team and week
   */
  async modifyHistoricalLineup(
    teamId: number,
    weekId: number,
    starterIds: number[],
    justification: string = ''
  ): Promise<AdminActionResponse> {
    const response = await api.put(`/admin/teams/${teamId}/lineups/${weekId}`, {
      starter_ids: starterIds,
      justification
    });
    return response.data;
  }

  /**
   * Recalculate score for a specific team and week
   */
  async recalculateScore(
    teamId: number,
    weekId: number,
    justification: string = ''
  ): Promise<AdminActionResponse> {
    const response = await api.post(`/admin/teams/${teamId}/weeks/${weekId}/recalculate`, {
      justification
    });
    return response.data;
  }

  /**
   * Grant additional moves to a team
   */
  async grantAdditionalMoves(
    teamId: number,
    additionalMoves: number,
    justification: string = ''
  ): Promise<AdminActionResponse> {
    const response = await api.post(`/admin/teams/${teamId}/moves/grant`, {
      additional_moves: additionalMoves,
      justification
    });
    return response.data;
  }

  /**
   * Get admin audit log
   */
  async getAuditLog(
    teamId?: number,
    limit: number = 100,
    offset: number = 0
  ): Promise<AuditLogEntry[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });

    if (teamId) {
      params.append('team_id', teamId.toString());
    }

    const response = await api.get(`/admin/audit-log?${params}`);
    return response.data;
  }

  /**
   * Get team lineup history with admin modification indicators
   */
  async getTeamLineupHistory(teamId: number): Promise<LineupHistoryEntry[]> {
    const response = await api.get(`/admin/teams/${teamId}/lineup-history`);
    return response.data;
  }

  /**
   * Get detailed lineup view for admin modification
   */
  async getAdminLineupView(teamId: number, weekId: number): Promise<AdminLineupView> {
    const response = await api.get(`/admin/teams/${teamId}/weeks/${weekId}/lineup`);
    return response.data;
  }
}

export const adminApi = new AdminApiService();