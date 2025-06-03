import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';
import api from '../lib/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

interface PlayerSearchResult {
  player_id: number;
  full_name: string;
  jersey_number?: string;
  position?: string;
  team_id?: number;
  team_name?: string;
  team_abbr?: string;
  height?: number;
  weight?: number;
  college?: string;
  years_pro?: number;
  status: string;
  headshot_url?: string;
  ppg: number;
  rpg: number;
  apg: number;
  games_played: number;
}

const PlayersPage: React.FC = () => {
  const navigate = useNavigate();
  const [players, setPlayers] = useState<PlayerSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');

  const formatHeight = (inches?: number) => {
    if (!inches) return 'N/A';
    const feet = Math.floor(inches / 12);
    const remainingInches = inches % 12;
    return `${feet}'${remainingInches}"`;
  };

  const loadInitialPlayers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Load initial players without any filters to get a good starting set
      const results = await api.wnba.searchPlayers(undefined, undefined, undefined, 50);
      setPlayers(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load players');
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (query: string, position: string, team: string) => {
      if (!query.trim() && !position && !team) {
        // If no filters, load initial set
        loadInitialPlayers();
        return;
      }

      setSearchLoading(true);
      try {
        const teamId = team ? parseInt(team, 10) : undefined;
        const results = await api.wnba.searchPlayers(
          query.trim() || undefined,
          teamId,
          position || undefined,
          100 // larger limit for general search
        );
        setPlayers(results);
      } catch (err) {
        console.error('Search error:', err);
        setError('Failed to search players');
      } finally {
        setSearchLoading(false);
      }
    }, 300),
    [loadInitialPlayers]
  );

  useEffect(() => {
    loadInitialPlayers();
  }, [loadInitialPlayers]);

  useEffect(() => {
    debouncedSearch(searchQuery, positionFilter, teamFilter);
    return () => {
      debouncedSearch.cancel();
    };
  }, [searchQuery, positionFilter, teamFilter, debouncedSearch]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handlePositionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPositionFilter(e.target.value);
  };

  const handleTeamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTeamFilter(e.target.value);
  };

  // Get available filters from current results
  const availablePositions = useMemo(() => {
    const positions = new Set(players.map(p => p.position).filter(Boolean) as string[]);
    return Array.from(positions).sort();
  }, [players]);

  const availableTeams = useMemo(() => {
    const teams = new Map<number, string>();
    players.forEach(p => {
      if (p.team_id && p.team_name) {
        teams.set(p.team_id, p.team_name);
      }
    });
    return Array.from(teams.entries()).sort((a, b) => a[1].localeCompare(b[1]));
  }, [players]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner message="Loading players..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <ErrorMessage message={error} />
        <button
          onClick={loadInitialPlayers}
          className="mt-4 btn-primary"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">WNBA Players</h1>
        <p className="text-gray-600 mt-2">
          Explore detailed statistics and information for WNBA players
        </p>
      </div>

      {/* Search and Filters */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Search & Filter</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="playerSearch" className="block text-sm font-medium text-gray-700 mb-1">
              Player Name
            </label>
            <input
              id="playerSearch"
              type="text"
              placeholder="Search by name..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="positionFilter" className="block text-sm font-medium text-gray-700 mb-1">
              Position
            </label>
            <select
              id="positionFilter"
              value={positionFilter}
              onChange={handlePositionChange}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500 bg-white"
            >
              <option value="">All Positions</option>
              {availablePositions.map(pos => (
                <option key={pos} value={pos}>{pos}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="teamFilter" className="block text-sm font-medium text-gray-700 mb-1">
              Team
            </label>
            <select
              id="teamFilter"
              value={teamFilter}
              onChange={handleTeamChange}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500 bg-white"
            >
              <option value="">All Teams</option>
              {availableTeams.map(([teamId, teamName]) => (
                <option key={teamId} value={teamId}>{teamName}</option>
              ))}
            </select>
          </div>
        </div>

        {searchLoading && (
          <div className="mt-4 text-center text-sm text-gray-500">Searching...</div>
        )}
      </div>

      {/* Results */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">
            Players ({players.length})
          </h2>
          <div className="text-sm text-gray-600">
            {(searchQuery || positionFilter || teamFilter) ? 'Filtered results' : 'Showing recent players'}
          </div>
        </div>

        {players.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">No players found</div>
            <button
              onClick={() => {
                setSearchQuery('');
                setPositionFilter('');
                setTeamFilter('');
              }}
              className="btn-secondary"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {players.map(player => (
              <div
                key={player.player_id}
                onClick={() => navigate(`/player/${player.player_id}`)}
                className="bg-white border rounded-lg p-4 hover:shadow-lg hover:border-blue-300 cursor-pointer transition-all duration-200"
              >
                {/* Player Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">{player.full_name}</h3>
                    <div className="text-sm text-gray-600">
                      {player.position}
                      {player.jersey_number && ` • #${player.jersey_number}`}
                    </div>
                  </div>
                  {player.headshot_url && (
                    <img
                      src={player.headshot_url}
                      alt={`${player.full_name} headshot`}
                      className="w-12 h-12 rounded-full object-cover ml-2"
                    />
                  )}
                </div>

                {/* Team Info */}
                <div className="mb-3">
                  <div className="text-sm font-medium text-blue-600">
                    {player.team_name || 'Free Agent'}
                  </div>
                  {player.team_abbr && (
                    <div className="text-xs text-gray-500">{player.team_abbr}</div>
                  )}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 text-center mb-3">
                  <div>
                    <div className="font-bold text-gray-900">{player.ppg.toFixed(1)}</div>
                    <div className="text-xs text-gray-600">PPG</div>
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">{player.rpg.toFixed(1)}</div>
                    <div className="text-xs text-gray-600">RPG</div>
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">{player.apg.toFixed(1)}</div>
                    <div className="text-xs text-gray-600">APG</div>
                  </div>
                </div>

                {/* Additional Info */}
                <div className="text-xs text-gray-500 space-y-1">
                  <div>Height: {formatHeight(player.height)}</div>
                  {player.college && <div>College: {player.college}</div>}
                  <div>Games: {player.games_played}</div>
                </div>

                {/* Status */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                    player.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {player.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlayersPage;