import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const [freeAgents, setFreeAgents] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [positionFilter, setPositionFilter] = useState<string>('');
  const [teamFilter, setTeamFilter] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  const fetchFreeAgents = useCallback(async () => {
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
  }, [leagueId]);

  useEffect(() => {
    fetchFreeAgents();
  }, [fetchFreeAgents]);

  const filteredAgents = freeAgents.filter((player) => {
    const matchesSearch = player.full_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPosition = !positionFilter || player.position === positionFilter;
    const matchesTeam = !teamFilter || player.team_abbr === teamFilter;
    return matchesSearch && matchesPosition && matchesTeam;
  });

  const handleAddPlayer = (playerId: number, setAsStarter: boolean = false) => {
    onAddPlayer(playerId, setAsStarter);
  };

  const handlePlayerClick = (playerId: number) => {
    navigate(`/player/${playerId}`);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setPositionFilter('');
    setTeamFilter('');
  };

  const hasActiveFilters = searchTerm || positionFilter || teamFilter;

  const positions = Array.from(new Set(freeAgents.map(p => p.position).filter(Boolean))).sort();
  const teams = Array.from(new Set(freeAgents.map(p => p.team_abbr).filter(Boolean))).sort();

  const isPlayerOnWaivers = (player: Player) => {
    return player.waiver_expires_at && new Date(player.waiver_expires_at) > new Date();
  };

  const formatWaiverExpiration = (expirationDate: string) => {
    const now = new Date();
    const expiry = new Date(expirationDate);
    const diffMs = expiry.getTime() - now.getTime();
    
    if (diffMs <= 0) {
      return 'Expired';
    }
    
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 24) {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ${diffHours % 24}h`;
    } else if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m`;
    } else {
      return `${diffMinutes}m`;
    }
  };

  const renderPlayerCard = (player: Player) => {
    const onWaivers = isPlayerOnWaivers(player);
    
    return (
      <div
        key={player.id}
        className={`bg-white border rounded-lg p-4 hover:shadow-md transition-all cursor-pointer ${
          onWaivers 
            ? 'border-orange-200 bg-orange-50' 
            : 'border-slate-200 hover:border-[#0c7ff2]'
        }`}
        onClick={() => handlePlayerClick(player.id)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-sm font-medium text-slate-900 truncate">{player.full_name}</h3>
              <div className="flex items-center space-x-1">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#0c7ff2] bg-opacity-10 text-[#0c7ff2]">
                  {player.position || 'N/A'}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
                  {player.team_abbr || 'N/A'}
                </span>
                {onWaivers && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                    WAIVER
                  </span>
                )}
              </div>
            </div>

            {onWaivers && player.waiver_expires_at && (
              <div className="text-xs text-orange-600 mb-2">
                Clears in: {formatWaiverExpiration(player.waiver_expires_at)}
              </div>
            )}

          {/* Player Stats */}
          <div className="grid grid-cols-3 gap-2 text-xs text-slate-500 mb-2">
            <div className="text-center">
              <div className="font-medium text-slate-900">{player.stats_2024?.ppg ? player.stats_2024.ppg.toFixed(1) : '--'}</div>
              <div>PPG</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-slate-900">{player.stats_2024?.rpg ? player.stats_2024.rpg.toFixed(1) : '--'}</div>
              <div>RPG</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-slate-900">{player.stats_2024?.apg ? player.stats_2024.apg.toFixed(1) : '--'}</div>
              <div>APG</div>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-2 ml-4">
          {onWaivers ? (
            <div className="text-center">
              <div className="text-xs text-orange-600 font-medium mb-1">On Waivers</div>
              <div className="text-xs text-slate-500">Submit claim via</div>
              <div className="text-xs text-slate-500">Waiver Wire page</div>
            </div>
          ) : (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleAddPlayer(player.id, false);
                }}
                disabled={movesRemaining <= 0}
                className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md transition-colors ${
                  movesRemaining <= 0
                    ? 'text-slate-400 bg-slate-100 cursor-not-allowed'
                    : 'text-white bg-[#0c7ff2] hover:bg-[#0a6bc8]'
                }`}
                title={movesRemaining <= 0 ? 'No moves remaining this week' : 'Add to bench'}
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Add
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleAddPlayer(player.id, true);
                }}
                disabled={movesRemaining <= 0}
                className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md transition-colors ${
                  movesRemaining <= 0
                    ? 'text-slate-400 bg-slate-100 cursor-not-allowed'
                    : 'text-green-700 bg-green-100 hover:bg-green-200'
                }`}
                title={movesRemaining <= 0 ? 'No starter moves remaining this week' : 'Add as starter'}
              >
                <UserPlusIcon className="h-4 w-4 mr-1" />
                Starter
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header with starter moves remaining warning */}
      {movesRemaining <= 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                No starter moves remaining this week
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>You've used all 3 starter moves for this week. You can still add players to your bench.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
        <div className="flex flex-col gap-4">
          {/* Main search bar */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-slate-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search players by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg leading-5 bg-white placeholder-slate-500 focus:outline-none focus:placeholder-slate-400 focus:ring-1 focus:ring-[#0c7ff2] focus:border-[#0c7ff2] sm:text-sm"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`inline-flex items-center px-3 py-2 border border-slate-300 rounded-lg text-sm font-medium transition-colors ${
                  showFilters ? 'bg-[#0c7ff2] bg-opacity-10 text-[#0c7ff2] border-[#0c7ff2]' : 'bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                <FunnelIcon className="h-4 w-4 mr-2" />
                Filters
                {hasActiveFilters && (
                  <span className="ml-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-[#0c7ff2] rounded-full">
                    {[searchTerm, positionFilter, teamFilter].filter(Boolean).length}
                  </span>
                )}
              </button>

              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center px-3 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 transition-colors"
                >
                  <XMarkIcon className="h-4 w-4 mr-1" />
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Filter dropdowns */}
          {showFilters && (
            <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-slate-200">
              <div className="sm:w-48">
                <label className="block text-sm font-medium text-slate-700 mb-1">Position</label>
                <select
                  value={positionFilter}
                  onChange={(e) => setPositionFilter(e.target.value)}
                  className="block w-full px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-[#0c7ff2] focus:border-[#0c7ff2] sm:text-sm"
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
                <label className="block text-sm font-medium text-slate-700 mb-1">Team</label>
                <select
                  value={teamFilter}
                  onChange={(e) => setTeamFilter(e.target.value)}
                  className="block w-full px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-[#0c7ff2] focus:border-[#0c7ff2] sm:text-sm"
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
      <div className="bg-white rounded-xl shadow-lg border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              Free Agents ({filteredAgents.length} players)
            </h2>
          </div>
        </div>

        {error ? (
          <div className="p-6 text-center text-red-600">{error}</div>
        ) : filteredAgents.length === 0 ? (
          <div className="p-6 text-center">
            <UserPlusIcon className="mx-auto h-12 w-12 text-slate-400" />
            <h3 className="mt-2 text-sm font-medium text-slate-900">No players found</h3>
            <p className="mt-1 text-sm text-slate-500">
              {hasActiveFilters ? 'Try adjusting your search criteria.' : 'No free agents available.'}
            </p>
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-200">
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