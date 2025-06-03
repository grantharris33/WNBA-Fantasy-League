import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { debounce } from 'lodash';
import api from '../lib/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

interface WNBAPlayerStats {
  player_id: number;
  player_name: string;
  team_id?: number;
  team_name?: string;
  team_abbr?: string;
  position?: string;
  jersey_number?: string;
  height?: number;
  weight?: number;
  college?: string;
  years_pro?: number;
  status: string;
  headshot_url?: string;
  season: number;
  games_played: number;
  games_started: number;
  ppg: number;
  rpg: number;
  apg: number;
  spg: number;
  bpg: number;
  topg: number;
  mpg: number;
  fg_percentage: number;
  three_point_percentage: number;
  ft_percentage: number;
  per: number;
  true_shooting_percentage: number;
  usage_rate: number;
  fantasy_ppg: number;
  consistency_score: number;
  ceiling: number;
  floor: number;
}

interface PlayerGameLog {
  game_id: string;
  date: string;
  opponent_id?: number;
  opponent_name: string;
  opponent_abbr: string;
  is_home: boolean;
  is_starter: boolean;
  minutes_played: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  field_goals_made: number;
  field_goals_attempted: number;
  field_goal_percentage: number;
  three_pointers_made: number;
  three_pointers_attempted: number;
  three_point_percentage: number;
  free_throws_made: number;
  free_throws_attempted: number;
  free_throw_percentage: number;
  plus_minus: number;
  did_not_play: boolean;
}

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

interface TeamRosterPlayer {
  player_id: number;
  full_name: string;
  jersey_number?: string;
  position?: string;
  height?: number;
  weight?: number;
  college?: string;
  years_pro?: number;
  status: string;
  headshot_url?: string;
  games_played: number;
  ppg: number;
  rpg: number;
  apg: number;
  mpg: number;
  fg_percentage: number;
}

const PlayerDetailPage: React.FC = () => {
  const { playerId } = useParams<{ playerId: string }>();
  const navigate = useNavigate();
  const [playerStats, setPlayerStats] = useState<WNBAPlayerStats | null>(null);
  const [gameLog, setGameLog] = useState<PlayerGameLog[]>([]);
  const [teamRoster, setTeamRoster] = useState<TeamRosterPlayer[]>([]);
  const [searchResults, setSearchResults] = useState<PlayerSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'gamelog' | 'teammates'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [positionFilter, setPositionFilter] = useState('');

  const fetchPlayerData = useCallback(async () => {
    if (!playerId) return;

    setLoading(true);
    setError(null);
    try {
      const playerIdNum = parseInt(playerId, 10);
      const [statsData, gameLogData] = await Promise.all([
        api.wnba.getPlayerStats(playerIdNum),
        api.wnba.getPlayerGameLog(playerIdNum, 10)
      ]);

      setPlayerStats(statsData);
      setGameLog(gameLogData);

      // Fetch team roster if player has a team
      if (statsData.team_id) {
        const rosterData = await api.wnba.getTeamRoster(statsData.team_id);
        setTeamRoster(rosterData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch player data');
      toast.error('Failed to load player details');
    } finally {
      setLoading(false);
    }
  }, [playerId]);

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (query: string, position: string) => {
      if (!query.trim() && !position) {
        setSearchResults([]);
        setSearchLoading(false);
        return;
      }

      setSearchLoading(true);
      try {
        const results = await api.wnba.searchPlayers(
          query.trim() || undefined,
          undefined, // team_id
          position || undefined,
          20 // limit
        );
        setSearchResults(results);
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    fetchPlayerData();
  }, [fetchPlayerData]);

  useEffect(() => {
    debouncedSearch(searchQuery, positionFilter);
    return () => {
      debouncedSearch.cancel();
    };
  }, [searchQuery, positionFilter, debouncedSearch]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handlePositionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPositionFilter(e.target.value);
  };

  const formatHeight = (inches?: number) => {
    if (!inches) return 'N/A';
    const feet = Math.floor(inches / 12);
    const remainingInches = inches % 12;
    return `${feet}'${remainingInches}"`;
  };

  const availablePositions = useMemo(() => {
    const positions = new Set(searchResults.map(p => p.position).filter(Boolean) as string[]);
    return Array.from(positions).sort();
  }, [searchResults]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner message="Loading player details..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <ErrorMessage message={error} />
        <button
          onClick={() => navigate(-1)}
          className="mt-4 btn-secondary"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!playerStats) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Player Not Found</h1>
        <p className="text-gray-600 mb-6">The player details you're looking for are not available.</p>
        <button
          onClick={() => navigate(-1)}
          className="btn-primary"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-6">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-blue-600 hover:text-blue-800 text-sm mb-2 flex items-center gap-1"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">{playerStats.player_name}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
            <span>{playerStats.position}</span>
            {playerStats.jersey_number && <span>#{playerStats.jersey_number}</span>}
            <span>{playerStats.team_name}</span>
          </div>
        </div>

        {/* Player Search */}
        <div className="w-full lg:w-96">
          <div className="card p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Search Players</h3>
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Search by name..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              />
              <select
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

            {/* Search Results */}
            {searchLoading && (
              <div className="mt-3 text-center text-sm text-gray-500">Searching...</div>
            )}
            {searchResults.length > 0 && (
              <div className="mt-3 max-h-64 overflow-y-auto">
                <div className="space-y-2">
                  {searchResults.map(player => (
                    <div
                      key={player.player_id}
                      onClick={() => navigate(`/player/${player.player_id}`)}
                      className="p-2 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer transition-colors"
                    >
                      <div className="font-medium text-sm text-gray-900">{player.full_name}</div>
                      <div className="text-xs text-gray-600">
                        {player.position} • {player.team_abbr} • {player.ppg.toFixed(1)} PPG
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Player Info Card */}
      <div className="card p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Basic Info */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Basic Information</h3>
            <div className="space-y-2 text-sm">
              <div><span className="text-gray-600">Height:</span> {formatHeight(playerStats.height)}</div>
              <div><span className="text-gray-600">Weight:</span> {playerStats.weight ? `${playerStats.weight} lbs` : 'N/A'}</div>
              <div><span className="text-gray-600">College:</span> {playerStats.college || 'N/A'}</div>
              <div><span className="text-gray-600">Years Pro:</span> {playerStats.years_pro || 'N/A'}</div>
              <div><span className="text-gray-600">Status:</span> {playerStats.status}</div>
            </div>
          </div>

          {/* Season Averages */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Season Averages</h3>
            <div className="space-y-2 text-sm">
              <div><span className="text-gray-600">Points:</span> {playerStats.ppg.toFixed(1)}</div>
              <div><span className="text-gray-600">Rebounds:</span> {playerStats.rpg.toFixed(1)}</div>
              <div><span className="text-gray-600">Assists:</span> {playerStats.apg.toFixed(1)}</div>
              <div><span className="text-gray-600">Steals:</span> {playerStats.spg.toFixed(1)}</div>
              <div><span className="text-gray-600">Blocks:</span> {playerStats.bpg.toFixed(1)}</div>
              <div><span className="text-gray-600">Minutes:</span> {playerStats.mpg.toFixed(1)}</div>
            </div>
          </div>

          {/* Shooting */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Shooting</h3>
                         <div className="space-y-2 text-sm">
               <div><span className="text-gray-600">FG%:</span> {playerStats.fg_percentage.toFixed(1)}%</div>
               <div><span className="text-gray-600">3P%:</span> {playerStats.three_point_percentage.toFixed(1)}%</div>
               <div><span className="text-gray-600">FT%:</span> {playerStats.ft_percentage.toFixed(1)}%</div>
               <div><span className="text-gray-600">True Shooting%:</span> {playerStats.true_shooting_percentage.toFixed(1)}%</div>
               <div><span className="text-gray-600">PER:</span> {playerStats.per.toFixed(1)}</div>
               <div><span className="text-gray-600">Usage Rate:</span> {playerStats.usage_rate.toFixed(1)}%</div>
             </div>
          </div>
        </div>

        {/* Fantasy Stats */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-3">Fantasy Performance</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="bg-blue-50 p-3 rounded">
              <div className="text-2xl font-bold text-blue-600">{playerStats.fantasy_ppg.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Fantasy PPG</div>
            </div>
            <div className="bg-green-50 p-3 rounded">
              <div className="text-2xl font-bold text-green-600">{playerStats.consistency_score.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Consistency</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-2xl font-bold text-purple-600">{playerStats.ceiling.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Ceiling</div>
            </div>
            <div className="bg-orange-50 p-3 rounded">
              <div className="text-2xl font-bold text-orange-600">{playerStats.floor.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Floor</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Season Stats
          </button>
          <button
            onClick={() => setActiveTab('gamelog')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'gamelog'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Recent Games
          </button>
          {playerStats.team_id && (
            <button
              onClick={() => setActiveTab('teammates')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'teammates'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Teammates
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="card p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Season Statistics Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Games</h4>
              <div className="text-sm space-y-1">
                <div>Games Played: {playerStats.games_played}</div>
                <div>Games Started: {playerStats.games_started}</div>
                <div>Start Percentage: {playerStats.games_played > 0 ? ((playerStats.games_started / playerStats.games_played) * 100).toFixed(1) : 0}%</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Advanced Metrics</h4>
                             <div className="text-sm space-y-1">
                 <div>Player Efficiency Rating: {playerStats.per.toFixed(1)}</div>
                 <div>True Shooting %: {playerStats.true_shooting_percentage.toFixed(1)}%</div>
                 <div>Usage Rate: {playerStats.usage_rate.toFixed(1)}%</div>
               </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'gamelog' && (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Opponent</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Min</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pts</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reb</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ast</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stl</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Blk</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FG%</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">+/-</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {gameLog.map(game => (
                <tr
                  key={game.game_id}
                  className={`hover:bg-gray-50 cursor-pointer ${game.is_starter ? 'bg-blue-50' : ''}`}
                  onClick={() => navigate(`/game/${game.game_id}`)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(game.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {game.is_home ? 'vs' : '@'} {game.opponent_abbr}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{game.minutes_played}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{game.points}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{game.rebounds}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{game.assists}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{game.steals}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{game.blocks}</td>
                                     <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                     {game.field_goals_attempted > 0 ? game.field_goal_percentage.toFixed(1) + '%' : 'N/A'}
                   </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {game.plus_minus > 0 ? '+' : ''}{game.plus_minus}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'teammates' && playerStats.team_id && (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                {playerStats.team_name} Roster
              </h3>
              <span className="text-sm text-gray-600">{teamRoster.length} players</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {teamRoster.map(teammate => (
                <div
                  key={teammate.player_id}
                  className={`p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors ${
                    teammate.player_id === playerStats.player_id ? 'bg-blue-50 border-blue-200' : 'bg-white'
                  }`}
                  onClick={() => navigate(`/player/${teammate.player_id}`)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-gray-900">{teammate.full_name}</div>
                    {teammate.jersey_number && (
                      <span className="text-sm text-gray-600">#{teammate.jersey_number}</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    {teammate.position} • {formatHeight(teammate.height)}
                  </div>
                  <div className="text-xs text-gray-500 grid grid-cols-3 gap-2">
                    <div>{teammate.ppg.toFixed(1)} PPG</div>
                    <div>{teammate.rpg.toFixed(1)} RPG</div>
                    <div>{teammate.apg.toFixed(1)} APG</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerDetailPage;