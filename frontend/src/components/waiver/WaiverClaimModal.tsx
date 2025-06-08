import React, { useState, useEffect } from 'react';
import { WaiverPlayer, WaiverClaimRequest } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface WaiverClaimModalProps {
  player: WaiverPlayer;
  teamId: number;
  onClose: () => void;
  onClaimSubmitted: () => void;
}

interface RosterPlayer {
  id: number;
  player_id: number;
  position: string;
  is_starter: boolean;
  player: {
    id: number;
    full_name: string;
    position: string;
    team_abbr: string;
  };
}

const WaiverClaimModal: React.FC<WaiverClaimModalProps> = ({
  player,
  teamId,
  onClose,
  onClaimSubmitted
}) => {
  const [rosterPlayers, setRosterPlayers] = useState<RosterPlayer[]>([]);
  const [selectedDropPlayer, setSelectedDropPlayer] = useState<number | null>(null);
  const [priority, setPriority] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [fetchingRoster, setFetchingRoster] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRosterPlayers();
  }, [teamId]);

  const fetchRosterPlayers = async () => {
    try {
      setFetchingRoster(true);
      const response = await fetch(`/api/v1/teams/${teamId}/roster`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch roster');
      }

      const roster = await response.json();
      setRosterPlayers(roster);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch roster');
    } finally {
      setFetchingRoster(false);
    }
  };

  const handleSubmitClaim = async () => {
    try {
      setLoading(true);
      setError(null);

      const claimData: WaiverClaimRequest = {
        player_id: player.id,
        priority: priority,
      };

      if (selectedDropPlayer) {
        claimData.drop_player_id = selectedDropPlayer;
      }

      const response = await fetch(`/api/v1/teams/${teamId}/waiver-claims`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(claimData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit waiver claim');
      }

      onClaimSubmitted();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit claim');
    } finally {
      setLoading(false);
    }
  };

  const requiresDropPlayer = rosterPlayers.length >= 10;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Submit Waiver Claim
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Player Info */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900">{player.full_name}</h4>
            <p className="text-sm text-gray-600">
              {player.position} • {player.team_abbr || 'FA'}
            </p>
            {player.waiver_expires_at && (
              <p className="text-sm text-red-600 mt-1">
                Waiver expires: {new Date(player.waiver_expires_at).toLocaleString()}
              </p>
            )}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          {fetchingRoster ? (
            <div className="flex justify-center py-4">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Claim Priority
                </label>
                <input
                  type="number"
                  min="1"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="1 = highest priority"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Lower numbers = higher priority
                </p>
              </div>

              {/* Drop Player Selection */}
              {requiresDropPlayer && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Drop Player (Roster Full) *
                  </label>
                  <select
                    value={selectedDropPlayer || ''}
                    onChange={(e) => setSelectedDropPlayer(e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    <option value="">Select player to drop</option>
                    {rosterPlayers.map((rosterPlayer) => (
                      <option key={rosterPlayer.player_id} value={rosterPlayer.player_id}>
                        {rosterPlayer.player.full_name} ({rosterPlayer.player.position})
                        {rosterPlayer.is_starter ? ' - Starter' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {rosterPlayers.length < 10 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Drop Player (Optional)
                  </label>
                  <select
                    value={selectedDropPlayer || ''}
                    onChange={(e) => setSelectedDropPlayer(e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">No player to drop</option>
                    {rosterPlayers.map((rosterPlayer) => (
                      <option key={rosterPlayer.player_id} value={rosterPlayer.player_id}>
                        {rosterPlayer.player.full_name} ({rosterPlayer.player.position})
                        {rosterPlayer.is_starter ? ' - Starter' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={onClose}
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitClaim}
                  disabled={loading || (requiresDropPlayer && !selectedDropPlayer)}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md disabled:opacity-50 flex items-center"
                >
                  {loading && <LoadingSpinner className="w-4 h-4 mr-2" />}
                  Submit Claim
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WaiverClaimModal;