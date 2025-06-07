import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import ConfirmationModal from '../../common/ConfirmationModal';
import { adminApi, type LineupHistoryEntry, type AdminLineupView } from '../../../services/adminApi';
import { formatWeekWithDates, getCurrentISOWeek } from '../../../lib/weekUtils';

interface Team {
  id: number;
  name: string;
  owner_email?: string;
  moves_this_week: number;
  league_name?: string;
}

interface Player {
  player_id: number;
  player_name: string;
  position: string;
  team_abbr: string;
  is_starter: boolean;
}

const TeamManagementTab: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number>(getCurrentISOWeek());
  const [lineupHistory, setLineupHistory] = useState<LineupHistoryEntry[]>([]);
  const [currentLineup, setCurrentLineup] = useState<AdminLineupView | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Modals
  const [showModifyLineupModal, setShowModifyLineupModal] = useState(false);
  const [showRecalculateModal, setShowRecalculateModal] = useState(false);
  const [showGrantMovesModal, setShowGrantMovesModal] = useState(false);
  
  // Form data
  const [selectedStarters, setSelectedStarters] = useState<number[]>([]);
  const [justification, setJustification] = useState('');
  const [additionalMoves, setAdditionalMoves] = useState(1);

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    if (selectedTeam) {
      loadTeamData();
    }
  }, [selectedTeam, selectedWeek]);

  const loadTeams = async () => {
    try {
      const teamsData = await adminApi.getTeams();
      setTeams(teamsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load teams');
    }
  };

  const loadTeamData = async () => {
    if (!selectedTeam) return;

    try {
      setLoading(true);
      setError(null);

      const [history, lineup] = await Promise.all([
        adminApi.getTeamLineupHistory(selectedTeam),
        selectedWeek ? adminApi.getAdminLineupView(selectedTeam, selectedWeek) : Promise.resolve(null)
      ]);

      setLineupHistory(history);
      setCurrentLineup(lineup);
      
      // Set current starters for the modify form
      if (lineup) {
        const starters = lineup.lineup.filter(p => p.is_starter).map(p => p.player_id);
        setSelectedStarters(starters);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load team data');
    } finally {
      setLoading(false);
    }
  };

  const handleModifyLineup = async () => {
    if (!selectedTeam || !selectedWeek) return;

    try {
      await adminApi.modifyHistoricalLineup(selectedTeam, selectedWeek, selectedStarters, justification);
      setShowModifyLineupModal(false);
      setJustification('');
      loadTeamData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to modify lineup');
    }
  };

  const handleRecalculateScore = async () => {
    if (!selectedTeam || !selectedWeek) return;

    try {
      await adminApi.recalculateScore(selectedTeam, selectedWeek, justification);
      setShowRecalculateModal(false);
      setJustification('');
      // Could refresh score data here
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to recalculate score');
    }
  };

  const handleGrantMoves = async () => {
    if (!selectedTeam) return;

    try {
      await adminApi.grantAdditionalMoves(selectedTeam, additionalMoves, justification);
      setShowGrantMovesModal(false);
      setJustification('');
      setAdditionalMoves(1);
      // Could refresh team data here
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to grant moves');
    }
  };

  const togglePlayerStarter = (playerId: number) => {
    setSelectedStarters(prev => {
      if (prev.includes(playerId)) {
        return prev.filter(id => id !== playerId);
      } else if (prev.length < 5) {
        return [...prev, playerId];
      }
      return prev;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Team Management
        </h3>
      </div>

      {/* Team and Week Selection */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Team
            </label>
            <select
              value={selectedTeam || ''}
              onChange={(e) => setSelectedTeam(e.target.value ? parseInt(e.target.value) : null)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Choose a team...</option>
              {teams.map(team => (
                <option key={team.id} value={team.id}>
                  {team.name} ({team.owner_email})
                </option>
              ))}
            </select>
            {teams.length === 0 && (
              <p className="text-sm text-gray-500 mt-1">
                No teams found.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Week
            </label>
            <input
              type="number"
              value={selectedWeek}
              onChange={(e) => setSelectedWeek(parseInt(e.target.value))}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="e.g., 202501"
            />
            <p className="text-sm text-gray-500 mt-1">
              Current: {formatWeekWithDates(selectedWeek)}
            </p>
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {loading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      )}

      {selectedTeam && !loading && (
        <>
          {/* Current Lineup */}
          {currentLineup && (
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-medium text-gray-900">
                  Current Lineup - {formatWeekWithDates(selectedWeek)}
                </h4>
                <div className="space-x-2">
                  <button
                    onClick={() => setShowModifyLineupModal(true)}
                    className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700"
                  >
                    Modify Lineup
                  </button>
                  <button
                    onClick={() => setShowRecalculateModal(true)}
                    className="bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700"
                  >
                    Recalculate Score
                  </button>
                  <button
                    onClick={() => setShowGrantMovesModal(true)}
                    className="bg-purple-600 text-white px-3 py-2 rounded-md text-sm hover:bg-purple-700"
                  >
                    Grant Moves
                  </button>
                </div>
              </div>

              {currentLineup.admin_modified && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                  <div className="flex">
                    <div className="ml-3">
                      <p className="text-sm text-yellow-700">
                        ⚠️ This lineup has been modified by admin {currentLineup.modification_count} time(s).
                        {currentLineup.last_modified && (
                          <span className="block mt-1">
                            Last modified: {new Date(currentLineup.last_modified).toLocaleString()}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium text-gray-900 mb-3">Starters (5)</h5>
                  <div className="space-y-2">
                    {currentLineup.lineup.filter(p => p.is_starter).map(player => (
                      <PlayerCard key={player.player_id} player={player} isStarter={true} />
                    ))}
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-3">Bench</h5>
                  <div className="space-y-2">
                    {currentLineup.lineup.filter(p => !p.is_starter).map(player => (
                      <PlayerCard key={player.player_id} player={player} isStarter={false} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Lineup History */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h4 className="text-lg font-medium text-gray-900 mb-4">
              Lineup History
            </h4>

            {lineupHistory.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No lineup history found</p>
            ) : (
              <div className="space-y-4">
                {lineupHistory.map(entry => (
                  <div key={entry.week_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h5 className="font-medium text-gray-900">{formatWeekWithDates(entry.week_id)}</h5>
                      <div className="flex items-center space-x-2">
                        {entry.admin_modified && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Admin Modified ({entry.modification_count}x)
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600 mb-3">
                      Starters: {entry.lineup.filter(p => p.is_starter).map(p => p.player_name).join(', ')}
                    </div>

                    {entry.last_modified && (
                      <div className="text-xs text-gray-500">
                        Last modified: {new Date(entry.last_modified).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Modify Lineup Modal */}
      {showModifyLineupModal && currentLineup && (
        <ConfirmationModal
          isOpen={true}
          title="Modify Lineup"
          message="Select exactly 5 starters for this lineup:"
          onConfirm={handleModifyLineup}
          onCancel={() => {
            setShowModifyLineupModal(false);
            setJustification('');
          }}
          confirmText="Modify Lineup"
          confirmDisabled={selectedStarters.length !== 5}
        >
          <div className="space-y-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Justification
              </label>
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                rows={2}
                placeholder="Reason for lineup modification..."
                required
              />
            </div>

            <div>
              <p className="text-sm text-gray-700 mb-2">
                Select 5 starters ({selectedStarters.length}/5 selected):
              </p>
              <div className="space-y-1 max-h-40 overflow-y-auto border border-gray-200 rounded p-2">
                {currentLineup.lineup.map(player => (
                  <label key={player.player_id} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                    <input
                      type="checkbox"
                      checked={selectedStarters.includes(player.player_id)}
                      onChange={() => togglePlayerStarter(player.player_id)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <span className="text-sm">
                      {player.player_name} ({player.position}) - {player.team_abbr}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </ConfirmationModal>
      )}

      {/* Recalculate Score Modal */}
      {showRecalculateModal && (
        <ConfirmationModal
          isOpen={true}
          title="Recalculate Score"
          message={`Recalculate score for team ${selectedTeam}, week ${selectedWeek}?`}
          onConfirm={handleRecalculateScore}
          onCancel={() => {
            setShowRecalculateModal(false);
            setJustification('');
          }}
          confirmText="Recalculate"
        >
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Justification
            </label>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
              rows={2}
              placeholder="Reason for score recalculation..."
              required
            />
          </div>
        </ConfirmationModal>
      )}

      {/* Grant Moves Modal */}
      {showGrantMovesModal && (
        <ConfirmationModal
          isOpen={true}
          title="Grant Additional Moves"
          message={`Grant additional moves to team ${selectedTeam}?`}
          onConfirm={handleGrantMoves}
          onCancel={() => {
            setShowGrantMovesModal(false);
            setJustification('');
            setAdditionalMoves(1);
          }}
          confirmText="Grant Moves"
        >
          <div className="space-y-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Moves
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={additionalMoves}
                onChange={(e) => setAdditionalMoves(parseInt(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Justification
              </label>
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                rows={2}
                placeholder="Reason for granting additional moves..."
                required
              />
            </div>
          </div>
        </ConfirmationModal>
      )}
    </div>
  );
};

interface PlayerCardProps {
  player: Player;
  isStarter: boolean;
}

const PlayerCard: React.FC<PlayerCardProps> = ({ player, isStarter }) => {
  return (
    <div className={`p-3 rounded-lg border ${
      isStarter 
        ? 'bg-green-50 border-green-200' 
        : 'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex justify-between items-center">
        <div>
          <p className="font-medium text-gray-900">{player.player_name}</p>
          <p className="text-sm text-gray-600">{player.position} - {player.team_abbr}</p>
        </div>
        {isStarter && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Starter
          </span>
        )}
      </div>
    </div>
  );
};

export default TeamManagementTab;