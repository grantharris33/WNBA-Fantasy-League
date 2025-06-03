import { fetchJSON } from '../lib/api';

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
  data?: unknown;
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
    return fetchJSON<AdminActionResponse>(`/admin/teams/${teamId}/lineups/${weekId}`, {
      method: 'PUT',
      body: {
        starter_ids: starterIds,
        justification
      }
    });
  }

  /**
   * Recalculate score for a specific team and week
   */
  async recalculateScore(
    teamId: number,
    weekId: number,
    justification: string = ''
  ): Promise<AdminActionResponse> {
    return fetchJSON<AdminActionResponse>(`/admin/teams/${teamId}/weeks/${weekId}/recalculate`, {
      method: 'POST',
      body: { justification }
    });
  }

  /**
   * Grant additional moves to a team
   */
  async grantAdditionalMoves(
    teamId: number,
    additionalMoves: number,
    justification: string = ''
  ): Promise<AdminActionResponse> {
    return fetchJSON<AdminActionResponse>(`/admin/teams/${teamId}/moves/grant`, {
      method: 'POST',
      body: {
        additional_moves: additionalMoves,
        justification
      }
    });
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

    return fetchJSON<AuditLogEntry[]>(`/admin/audit-log?${params}`);
  }

  /**
   * Get team lineup history with admin modification indicators
   */
  async getTeamLineupHistory(teamId: number): Promise<LineupHistoryEntry[]> {
    return fetchJSON<LineupHistoryEntry[]>(`/admin/teams/${teamId}/lineup-history`);
  }

  /**
   * Get detailed lineup view for admin modification
   */
  async getAdminLineupView(teamId: number, weekId: number): Promise<AdminLineupView> {
    return fetchJSON<AdminLineupView>(`/admin/teams/${teamId}/weeks/${weekId}/lineup`);
  }
}

export const adminApi = new AdminApiService();