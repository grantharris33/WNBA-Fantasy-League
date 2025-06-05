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

export interface DataQualityDashboard {
  checks_summary: Record<string, number>;
  recent_anomalies: AnomalyEntry[];
  severity_breakdown: Record<string, number>;
  total_unresolved_anomalies: number;
}

export interface QualityCheck {
  id: number;
  check_name: string;
  check_type: string;
  target_table: string;
  status: string;
  last_run?: string;
  last_result?: string;
  consecutive_failures: number;
  is_active: boolean;
}

export interface ValidationRule {
  id: number;
  entity_type: string;
  field_name: string;
  rule_type: string;
  rule_config: Record<string, any>;
  is_active: boolean;
}

export interface AnomalyEntry {
  id: number;
  entity_type: string;
  entity_id: string;
  anomaly_type: string;
  description: string;
  severity: string;
  detected_at: string;
  is_resolved: boolean;
  resolved_at?: string;
  resolution_notes?: string;
}

export interface IngestLogEntry {
  id: number;
  timestamp: string;
  provider: string;
  message: string;
}

export interface CreateQualityCheckRequest {
  check_name: string;
  check_type: string;
  target_table: string;
  check_query: string;
  expected_result?: string;
  failure_threshold?: number;
}

export interface CreateValidationRuleRequest {
  entity_type: string;
  field_name: string;
  rule_type: string;
  rule_config: Record<string, any>;
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

  // Data Quality Methods
  
  /**
   * Get data quality dashboard overview
   */
  async getDataQualityDashboard(): Promise<DataQualityDashboard> {
    return fetchJSON<DataQualityDashboard>('/admin/data-quality/dashboard');
  }

  /**
   * List all quality checks
   */
  async getQualityChecks(activeOnly: boolean = true): Promise<QualityCheck[]> {
    const params = new URLSearchParams({ active_only: activeOnly.toString() });
    return fetchJSON<QualityCheck[]>(`/admin/data-quality/checks?${params}`);
  }

  /**
   * Create a new quality check
   */
  async createQualityCheck(checkData: CreateQualityCheckRequest): Promise<QualityCheck> {
    return fetchJSON<QualityCheck>('/admin/data-quality/checks', {
      method: 'POST',
      body: checkData
    });
  }

  /**
   * Create a new validation rule
   */
  async createValidationRule(ruleData: CreateValidationRuleRequest): Promise<ValidationRule> {
    return fetchJSON<ValidationRule>('/admin/data-quality/validation-rules', {
      method: 'POST',
      body: ruleData
    });
  }

  /**
   * List validation rules
   */
  async getValidationRules(entityType?: string): Promise<ValidationRule[]> {
    const params = entityType ? new URLSearchParams({ entity_type: entityType }) : '';
    return fetchJSON<ValidationRule[]>(`/admin/data-quality/validation-rules?${params}`);
  }

  /**
   * Run a specific quality check
   */
  async runQualityCheck(checkId: number): Promise<AdminActionResponse> {
    return fetchJSON<AdminActionResponse>(`/admin/data-quality/checks/${checkId}/run`, {
      method: 'POST'
    });
  }

  /**
   * List anomalies
   */
  async getAnomalies(
    unresolvedOnly: boolean = true,
    severity?: string,
    limit: number = 50
  ): Promise<AnomalyEntry[]> {
    const params = new URLSearchParams({
      unresolved_only: unresolvedOnly.toString(),
      limit: limit.toString()
    });
    
    if (severity) {
      params.append('severity', severity);
    }

    return fetchJSON<AnomalyEntry[]>(`/admin/data-quality/anomalies?${params}`);
  }

  /**
   * Get system logs (ingest logs, job logs, etc.)
   */
  async getIngestLogs(limit: number = 100, offset: number = 0, provider?: string): Promise<IngestLogEntry[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (provider) {
      params.append('provider', provider);
    }
    
    return fetchJSON<IngestLogEntry[]>(`/logs/ingest?${params}`);
  }

  /**
   * Run all quality checks
   */
  async runAllQualityChecks(): Promise<any> {
    return fetchJSON<any>('/admin/data-quality/checks/run-all', {
      method: 'POST'
    });
  }

  /**
   * Get quality trends
   */
  async getQualityTrends(days: number = 30): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    return fetchJSON<any>(`/admin/data-quality/trends?${params}`);
  }

  /**
   * Resolve an anomaly
   */
  async resolveAnomaly(anomalyId: number, resolutionNotes: string): Promise<AdminActionResponse> {
    return fetchJSON<AdminActionResponse>(`/admin/data-quality/anomalies/${anomalyId}/resolve`, {
      method: 'POST',
      body: { resolution_notes: resolutionNotes }
    });
  }

  /**
   * Trigger anomaly detection
   */
  async detectAnomalies(gameDate?: string): Promise<any> {
    const params = gameDate ? new URLSearchParams({ game_date: gameDate }) : '';
    return fetchJSON<any>(`/admin/data-quality/detect-anomalies?${params}`, {
      method: 'POST'
    });
  }
}

export const adminApi = new AdminApiService();