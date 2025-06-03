import React, { useState, useEffect } from 'react';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  UserPlusIcon,
  FunnelIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import api from '../../lib/api';
import type { Player } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';

interface FreeAgentsViewProps {
  leagueId: number;
  onAddPlayer: (playerId: number, setAsStarter?: boolean) => void;
  movesRemaining: number;
}

const FreeAgentsView: React.FC<FreeAgentsViewProps> = ({ leagueId, onAddPlayer, movesRemaining }) => {
  const [freeAgents, setFreeAgents] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [positionFilter, setPositionFilter] = useState<string>('');
  const [teamFilter, setTeamFilter] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchFreeAgents();
  }, [leagueId]);

  const fetchFreeAgents = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.roster.getFreeAgents(leagueId);
      setFreeAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load free agents');
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = freeAgents.filter((player) => {
    const matchesSearch = player.full_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPosition = !positionFilter || player.position === positionFilter;
    const matchesTeam = !teamFilter || player.team_abbr === teamFilter;
    return matchesSearch && matchesPosition && matchesTeam;
  });

  const handleAddPlayer = (playerId: number, setAsStarter: boolean = false) => {
    onAddPlayer(playerId, setAsStarter);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setPositionFilter('');
    setTeamFilter('');
  };

  const hasActiveFilters = searchTerm || positionFilter || teamFilter;

  const positions = Array.from(new Set(freeAgents.map(p => p.position).filter(Boolean))).sort();
  const teams = Array.from(new Set(freeAgents.map(p => p.team_abbr).filter(Boolean))).sort();

  const renderPlayerCard = (player: Player) => (
    <div key={player.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">{player.full_name}</h3>
            <div className="flex items-center space-x-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                {player.position || 'N/A'}
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                {player.team_abbr || 'N/A'}
              </span>
            </div>
          </div>

          {/* Player Stats Placeholder - TODO: Integrate with real stats when available */}
          <div className="grid grid-cols-3 gap-2 text-xs text-gray-500 mb-2">
            <div className="text-center">
              <div className="font-medium text-gray-900">--</div>
              <div>PPG</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-900">--</div>
              <div>RPG</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-900">--</div>
              <div>APG</div>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-2 ml-4">
          <button
            onClick={() => handleAddPlayer(player.id, false)}
            disabled={movesRemaining <= 0}
            className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md transition-colors ${
              movesRemaining <= 0
                ? 'text-gray-400 bg-gray-100 cursor-not-allowed'
                : 'text-blue-700 bg-blue-100 hover:bg-blue-200'
            }`}
            title={movesRemaining <= 0 ? 'No moves remaining this week' : 'Add to bench'}
          >
            <PlusIcon className="h-4 w-4 mr-1" />
            Add
          </button>
          <button
            onClick={() => handleAddPlayer(player.id, true)}
            disabled={movesRemaining <= 0}
            className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md transition-colors ${
              movesRemaining <= 0
                ? 'text-gray-400 bg-gray-100 cursor-not-allowed'
                : 'text-green-700 bg-green-100 hover:bg-green-200'
            }`}
            title={movesRemaining <= 0 ? 'No moves remaining this week' : 'Add as starter'}
          >
            <UserPlusIcon className="h-4 w-4 mr-1" />
            Starter
          </button>
        </div>
      </div>
    </div>
  );

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header with moves remaining warning */}
      {movesRemaining <= 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                No moves remaining this week
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>You've used all 3 moves for this week. Try again next week.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col gap-4">
          {/* Main search bar */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search players by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium transition-colors ${
                  showFilters ? 'bg-blue-50 text-blue-700 border-blue-300' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <FunnelIcon className="h-4 w-4 mr-2" />
                Filters
                {hasActiveFilters && (
                  <span className="ml-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-blue-600 rounded-full">
                    {[searchTerm, positionFilter, teamFilter].filter(Boolean).length}
                  </span>
                )}
              </button>

              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                >
                  <XMarkIcon className="h-4 w-4 mr-1" />
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Filter dropdowns */}
          {showFilters && (
            <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-gray-200">
              <div className="sm:w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                <select
                  value={positionFilter}
                  onChange={(e) => setPositionFilter(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">All Positions</option>
                  {positions.map((position) => (
                    <option key={position} value={position || ''}>
                      {position}
                    </option>
                  ))}
                </select>
              </div>

              <div className="sm:w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">Team</label>
                <select
                  value={teamFilter}
                  onChange={(e) => setTeamFilter(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">All Teams</option>
                  {teams.map((team) => (
                    <option key={team} value={team || ''}>
                      {team}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Free Agents List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Free Agents ({filteredAgents.length} players)
            </h2>
          </div>
        </div>

        {error ? (
          <div className="p-6 text-center text-red-600">{error}</div>
        ) : filteredAgents.length === 0 ? (
          <div className="p-6 text-center">
            <UserPlusIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No players found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {hasActiveFilters ? 'Try adjusting your search criteria.' : 'No free agents available.'}
            </p>
          </div>
        ) : (
          <>
            <div className="divide-y divide-gray-200">
              {filteredAgents.map((player) => (
                <div key={player.id} className="p-4">
                  {renderPlayerCard(player)}
                </div>
              ))}
            </div>


          </>
        )}
      </div>
    </div>
  );
};

export default FreeAgentsView;