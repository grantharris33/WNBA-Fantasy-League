import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { useAuth } from '../../contexts/AuthContext';
import { adminApi } from '../../services/adminApi';

interface Team {
  id: number;
  name: string;
  owner_email?: string;
  moves_this_week: number;
}

interface AuditLogEntry {
  id: number;
  timestamp: string;
  admin_email: string;
  action: string;
  details: string;
  path?: string;
  method?: string;
}

interface LineupPlayer {
  player_id: number;
  player_name: string;
  position: string;
  team_abbr: string;
  is_starter: boolean;
}

interface LineupHistoryEntry {
  week_id: number;
  lineup: LineupPlayer[];
  admin_modified: boolean;
  modification_count: number;
  last_modified?: string;
}

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [lineupHistory, setLineupHistory] = useState<LineupHistoryEntry[]>([]);
  const [currentLineup, setCurrentLineup] = useState<LineupPlayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'roster' | 'scoring' | 'audit'>('roster');

  // Form states
  const [modifyLineupForm, setModifyLineupForm] = useState({
    starterIds: [] as number[],
    justification: ''
  });
  const [recalculateForm, setRecalculateForm] = useState({
    justification: ''
  });
  const [grantMovesForm, setGrantMovesForm] = useState({
    additionalMoves: 0,
    justification: ''
  });

  useEffect(() => {
    if (!user?.is_admin) return;

    // Load initial data
    loadTeams();
    loadAuditLogs();
  }, [user]);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const loadTeams = async () => {
    try {
      // This would typically come from a teams API endpoint
      // For now, we'll use a placeholder
      setTeams([
        { id: 1, name: 'Team Alpha', owner_email: 'user1@example.com', moves_this_week: 2 },
        { id: 2, name: 'Team Beta', owner_email: 'user2@example.com', moves_this_week: 1 },
      ]);
    } catch (error) {
      console.error('Failed to load teams:', error);
    }
  };

  const loadAuditLogs = async () => {
    try {
      const logs = await adminApi.getAuditLog();
      setAuditLogs(logs);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    }
  };

  const loadTeamLineupHistory = async (teamId: number) => {
    try {
      setLoading(true);
      clearMessages();
      const history = await adminApi.getTeamLineupHistory(teamId);
      setLineupHistory(history);
    } catch (error) {
      console.error('Failed to load lineup history:', error);
      setError('Failed to load lineup history');
    } finally {
      setLoading(false);
    }
  };

  const loadWeeklyLineup = async (teamId: number, weekId: number) => {
    try {
      setLoading(true);
      clearMessages();
      const lineupData = await adminApi.getAdminLineupView(teamId, weekId);
      setCurrentLineup(lineupData.lineup);
      setModifyLineupForm({
        starterIds: lineupData.lineup.filter((p: { is_starter: boolean }) => p.is_starter).map((p: { player_id: number }) => p.player_id),
        justification: ''
      });
    } catch (error) {
      console.error('Failed to load weekly lineup:', error);
      setError('Failed to load weekly lineup');
    } finally {
      setLoading(false);
    }
  };

  const handleModifyLineup = async () => {
    if (!selectedTeam || !selectedWeek || modifyLineupForm.starterIds.length !== 5) {
      setError('Please select exactly 5 starters');
      return;
    }

    try {
      setLoading(true);
      clearMessages();
      await adminApi.modifyHistoricalLineup(
        selectedTeam,
        selectedWeek,
        modifyLineupForm.starterIds,
        modifyLineupForm.justification
      );
      setSuccess('Lineup modified successfully');

      // Reload data
      await loadTeamLineupHistory(selectedTeam);
      await loadAuditLogs();
    } catch (error) {
      console.error('Failed to modify lineup:', error);
      setError('Failed to modify lineup');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculateScore = async () => {
    if (!selectedTeam || !selectedWeek) {
      setError('Please select a team and week');
      return;
    }

    try {
      setLoading(true);
      clearMessages();
      await adminApi.recalculateScore(selectedTeam, selectedWeek, recalculateForm.justification);
      setSuccess('Score recalculated successfully');

      // Reload audit logs
      await loadAuditLogs();
    } catch (error) {
      console.error('Failed to recalculate score:', error);
      setError('Failed to recalculate score');
    } finally {
      setLoading(false);
    }
  };

  const handleGrantMoves = async () => {
    if (!selectedTeam || grantMovesForm.additionalMoves <= 0) {
      setError('Please select a team and enter a positive number of moves');
      return;
    }

    try {
      setLoading(true);
      clearMessages();
      await adminApi.grantAdditionalMoves(
        selectedTeam,
        grantMovesForm.additionalMoves,
        grantMovesForm.justification
      );
      setSuccess('Additional moves granted successfully');

      // Reload teams and audit logs
      await loadTeams();
      await loadAuditLogs();
    } catch (error) {
      console.error('Failed to grant moves:', error);
      setError('Failed to grant additional moves');
    } finally {
      setLoading(false);
    }
  };

  const toggleStarter = (playerId: number) => {
    const newStarters = modifyLineupForm.starterIds.includes(playerId)
      ? modifyLineupForm.starterIds.filter(id => id !== playerId)
      : [...modifyLineupForm.starterIds, playerId];

    setModifyLineupForm({ ...modifyLineupForm, starterIds: newStarters });
  };

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-red-100 p-3 rounded-full">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 18.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
          <h3 className="text-lg font-medium text-gray-900 text-center">Access Denied</h3>
          <p className="mt-2 text-sm text-gray-500 text-center">
            Admin privileges required to access this page.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-blue-100 p-2 rounded-lg">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        </div>

        {/* Status Messages */}
        {error && <ErrorMessage message={error} onClose={() => setError(null)} />}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">{success}</p>
              </div>
              <div className="ml-auto pl-3">
                <div className="-mx-1.5 -my-1.5">
                  <button
                    onClick={() => setSuccess(null)}
                    className="inline-flex bg-green-50 rounded-md p-1.5 text-green-500 hover:bg-green-100"
                  >
                    <span className="sr-only">Dismiss</span>
                    <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('roster')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'roster'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Roster Management
            </button>
            <button
              onClick={() => setActiveTab('scoring')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'scoring'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Score Management
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'audit'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Audit Log
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'roster' && (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Roster & Lineup Management
              </h3>

              {/* Team and Week Selection */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-6">
                <div>
                  <label htmlFor="team-select" className="block text-sm font-medium text-gray-700">
                    Select Team
                  </label>
                  <select
                    id="team-select"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    value={selectedTeam || ''}
                    onChange={(e) => {
                      const teamId = parseInt(e.target.value);
                      setSelectedTeam(teamId);
                      if (teamId) loadTeamLineupHistory(teamId);
                    }}
                  >
                    <option value="">Choose a team</option>
                    {teams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name} ({team.owner_email})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="week-select" className="block text-sm font-medium text-gray-700">
                    Select Week
                  </label>
                  <select
                    id="week-select"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    value={selectedWeek || ''}
                    onChange={(e) => {
                      const weekId = parseInt(e.target.value);
                      setSelectedWeek(weekId);
                      if (selectedTeam && weekId) {
                        loadWeeklyLineup(selectedTeam, weekId);
                      }
                    }}
                  >
                    <option value="">Choose a week</option>
                    {lineupHistory.map((entry) => (
                      <option key={entry.week_id} value={entry.week_id}>
                        Week {entry.week_id} {entry.admin_modified ? '(Modified)' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {loading && <LoadingSpinner />}

              {/* Lineup Editor */}
              {currentLineup.length > 0 && !loading && (
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-gray-900">Lineup Editor</h4>
                  <div className="space-y-2">
                    {currentLineup.map((player) => (
                      <div
                        key={player.player_id}
                        className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-colors ${
                          modifyLineupForm.starterIds.includes(player.player_id)
                            ? 'bg-blue-50 border-blue-200'
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => toggleStarter(player.player_id)}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${
                            modifyLineupForm.starterIds.includes(player.player_id)
                              ? 'bg-blue-500'
                              : 'bg-gray-300'
                          }`} />
                          <div>
                            <div className="font-medium">{player.player_name}</div>
                            <div className="text-sm text-gray-500">
                              {player.position} - {player.team_abbr}
                            </div>
                          </div>
                        </div>
                        {player.is_starter && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            Current Starter
                          </span>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="text-sm text-gray-600">
                    Selected starters: {modifyLineupForm.starterIds.length}/5
                  </div>

                  <div>
                    <label htmlFor="lineup-justification" className="block text-sm font-medium text-gray-700">
                      Justification
                    </label>
                    <textarea
                      id="lineup-justification"
                      rows={3}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Reason for lineup modification..."
                      value={modifyLineupForm.justification}
                      onChange={(e) => setModifyLineupForm({
                        ...modifyLineupForm,
                        justification: e.target.value
                      })}
                    />
                  </div>

                  <button
                    onClick={handleModifyLineup}
                    disabled={loading || modifyLineupForm.starterIds.length !== 5}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Modifying...' : 'Modify Historical Lineup'}
                  </button>
                </div>
              )}

              {/* Grant Additional Moves */}
              <div className="mt-8 pt-8 border-t border-gray-200">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Grant Additional Moves</h4>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="additional-moves" className="block text-sm font-medium text-gray-700">
                      Additional Moves
                    </label>
                    <input
                      type="number"
                      id="additional-moves"
                      min="1"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      value={grantMovesForm.additionalMoves || ''}
                      onChange={(e) => setGrantMovesForm({
                        ...grantMovesForm,
                        additionalMoves: parseInt(e.target.value) || 0
                      })}
                    />
                  </div>
                  <div>
                    <label htmlFor="moves-justification" className="block text-sm font-medium text-gray-700">
                      Justification
                    </label>
                    <input
                      type="text"
                      id="moves-justification"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Reason for granting moves..."
                      value={grantMovesForm.justification}
                      onChange={(e) => setGrantMovesForm({
                        ...grantMovesForm,
                        justification: e.target.value
                      })}
                    />
                  </div>
                </div>
                <button
                  onClick={handleGrantMoves}
                  disabled={loading || !selectedTeam || grantMovesForm.additionalMoves <= 0}
                  className="mt-4 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Granting...' : 'Grant Additional Moves'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'scoring' && (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Score Recalculation
              </h3>

              <p className="text-sm text-gray-600 mb-6">
                Recalculate scores for a specific team and week. This will update the TeamScore table
                based on the current lineup and stat lines.
              </p>

              <div className="mb-4">
                <label htmlFor="recalc-justification" className="block text-sm font-medium text-gray-700">
                  Justification
                </label>
                <textarea
                  id="recalc-justification"
                  rows={3}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Reason for score recalculation..."
                  value={recalculateForm.justification}
                  onChange={(e) => setRecalculateForm({
                    ...recalculateForm,
                    justification: e.target.value
                  })}
                />
              </div>

              <button
                onClick={handleRecalculateScore}
                disabled={loading || !selectedTeam || !selectedWeek}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Recalculating...' : 'Recalculate Score'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Admin Action Audit Log
              </h3>

              {auditLogs.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No audit log entries found.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Admin
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Action
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Details
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {auditLogs.map((log) => (
                        <tr key={log.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(log.timestamp).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {log.admin_email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {log.action}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                            {log.details}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};