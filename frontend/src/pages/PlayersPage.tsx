import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';
import api from '../lib/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import DashboardLayout from '../components/layout/DashboardLayout';

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
  const [myRosterPlayers, setMyRosterPlayers] = useState<PlayerSearchResult[]>([]);
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

  const loadMyRosterPlayers = useCallback(async () => {
    try {
      const teams = await api.users.getMyTeams();
      const rosterPlayerIds = teams.flatMap(team => 
        team.roster_slots?.map(slot => slot.player_id) || []
      );
      
      if (rosterPlayerIds.length > 0) {
        // Fetch player details for roster players
        const rosterPlayers = await Promise.all(
          rosterPlayerIds.map(async (playerId) => {
            try {
              return await api.wnba.getPlayerDetails(playerId);
            } catch {
              return null;
            }
          })
        );
        setMyRosterPlayers(rosterPlayers.filter(player => player !== null));
      }
    } catch (err) {
      console.error('Failed to load roster players:', err);
    }
  }, []);

  const loadInitialPlayers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Load initial players without any filters to get a good starting set
      const results = await api.wnba.searchPlayers(undefined, undefined, undefined, 50);
      if (Array.isArray(results)) {
        setPlayers(results);
      } else {
        console.error('API returned non-array response:', results);
        setError('Invalid response format from server');
      }
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
        if (Array.isArray(results)) {
          setPlayers(results);
        } else {
          console.error('API returned non-array response:', results);
          setError('Invalid response format from server');
        }
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
    loadMyRosterPlayers();
  }, [loadInitialPlayers, loadMyRosterPlayers]);

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
    if (!Array.isArray(players)) {
      console.error('Players is not an array:', players);
      return [];
    }
    const positions = new Set(players.map(p => p.position).filter(Boolean) as string[]);
    return Array.from(positions).sort();
  }, [players]);

  const availableTeams = useMemo(() => {
    if (!Array.isArray(players)) {
      return [];
    }
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
      <DashboardLayout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner message="Loading players..." />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="max-w-4xl mx-auto p-6">
          <ErrorMessage message={error} />
          <button
            onClick={loadInitialPlayers}
            className="mt-4 flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-[#0c7ff2] text-white text-sm font-semibold hover:bg-[#0a68c4] transition-colors shadow-sm"
          >
            Try Again
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">WNBA Players</h1>
        <p className="text-slate-600 mt-2">
          Explore detailed statistics and information for WNBA players
        </p>
      </div>

      {/* My Roster Players */}
      {myRosterPlayers.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-[#0c7ff2]">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
            <span className="material-icons text-[#0c7ff2] mr-2">groups</span>
            My Roster Players
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {myRosterPlayers.map(player => (
              <div
                key={player.player_id}
                className="bg-slate-50 rounded-lg p-4 hover:bg-slate-100 cursor-pointer transition-colors"
                onClick={() => navigate(`/player/${player.player_id}`)}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-[#0c7ff2] rounded-full flex items-center justify-center text-white font-semibold">
                    {player.full_name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">
                      {player.full_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {player.position} • {player.team_abbr}
                    </p>
                    <div className="flex space-x-2 mt-1">
                      <span className="text-xs text-slate-600">{player.ppg?.toFixed(1)} PPG</span>
                      <span className="text-xs text-slate-600">{player.rpg?.toFixed(1)} RPG</span>
                      <span className="text-xs text-slate-600">{player.apg?.toFixed(1)} APG</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Search & Filter</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="playerSearch" className="block text-sm font-medium text-slate-700 mb-1">
              Player Name
            </label>
            <input
              id="playerSearch"
              type="text"
              placeholder="Search by name..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full p-2 border border-slate-300 rounded-lg focus:ring-[#0c7ff2] focus:border-[#0c7ff2] text-slate-900"
            />
          </div>
          <div>
            <label htmlFor="positionFilter" className="block text-sm font-medium text-slate-700 mb-1">
              Position
            </label>
            <select
              id="positionFilter"
              value={positionFilter}
              onChange={handlePositionChange}
              className="w-full p-2 border border-slate-300 rounded-lg focus:ring-[#0c7ff2] focus:border-[#0c7ff2] bg-white text-slate-900"
            >
              <option value="">All Positions</option>
              {availablePositions.map(pos => (
                <option key={pos} value={pos}>{pos}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="teamFilter" className="block text-sm font-medium text-slate-700 mb-1">
              Team
            </label>
            <select
              id="teamFilter"
              value={teamFilter}
              onChange={handleTeamChange}
              className="w-full p-2 border border-slate-300 rounded-lg focus:ring-[#0c7ff2] focus:border-[#0c7ff2] bg-white text-slate-900"
            >
              <option value="">All Teams</option>
              {availableTeams.map(([teamId, teamName]) => (
                <option key={teamId} value={teamId}>{teamName}</option>
              ))}
            </select>
          </div>
        </div>

        {searchLoading && (
          <div className="mt-4 text-center text-sm text-slate-500">Searching...</div>
        )}
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-900">
            Players ({Array.isArray(players) ? players.length : 0})
          </h2>
          <div className="text-sm text-slate-600">
            {(searchQuery || positionFilter || teamFilter) ? 'Filtered results' : 'Showing recent players'}
          </div>
        </div>

        {!Array.isArray(players) || players.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-slate-500 mb-4">No players found</div>
            <button
              onClick={() => {
                setSearchQuery('');
                setPositionFilter('');
                setTeamFilter('');
              }}
              className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-slate-200 text-slate-800 text-sm font-medium hover:bg-slate-300 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.isArray(players) && players.map(player => (
              <div
                key={player.player_id}
                onClick={() => navigate(`/player/${player.player_id}`)}
                className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-lg hover:border-[#0c7ff2] cursor-pointer transition-all duration-200"
              >
                {/* Player Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 truncate">{player.full_name}</h3>
                    <div className="text-sm text-slate-600">
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
                  <div className="text-sm font-medium text-[#0c7ff2]">
                    {player.team_name || 'Free Agent'}
                  </div>
                  {player.team_abbr && (
                    <div className="text-xs text-slate-500">{player.team_abbr}</div>
                  )}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 text-center mb-3">
                  <div>
                    <div className="font-bold text-slate-900">{player.ppg.toFixed(1)}</div>
                    <div className="text-xs text-slate-600">PPG</div>
                  </div>
                  <div>
                    <div className="font-bold text-slate-900">{player.rpg.toFixed(1)}</div>
                    <div className="text-xs text-slate-600">RPG</div>
                  </div>
                  <div>
                    <div className="font-bold text-slate-900">{player.apg.toFixed(1)}</div>
                    <div className="text-xs text-slate-600">APG</div>
                  </div>
                </div>

                {/* Additional Info */}
                <div className="text-xs text-slate-500 space-y-1">
                  <div>Height: {formatHeight(player.height)}</div>
                  {player.college && <div>College: {player.college}</div>}
                  <div>Games: {player.games_played}</div>
                </div>

                {/* Status */}
                <div className="mt-3 pt-3 border-t border-slate-200">
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                    player.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-slate-100 text-slate-800'
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
    </DashboardLayout>
  );
};

export default PlayersPage;