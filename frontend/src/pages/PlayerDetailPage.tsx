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



const PlayerDetailPage: React.FC = () => {
  const { playerId } = useParams<{ playerId: string }>();
  const navigate = useNavigate();
  const [playerStats, setPlayerStats] = useState<WNBAPlayerStats | null>(null);
  const [gameLog, setGameLog] = useState<PlayerGameLog[]>([]);

  const [searchResults, setSearchResults] = useState<PlayerSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'gamelog' | 'teammates'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [positionFilter] = useState('');

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
        // Team roster fetch removed - not used in current UI
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
        if (Array.isArray(results)) {
          setSearchResults(results);
        } else {
          console.error('Search API returned non-array response:', results);
          setSearchResults([]);
        }
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

  const formatHeight = (inches?: number) => {
    if (!inches) return 'N/A';
    const feet = Math.floor(inches / 12);
    const remainingInches = inches % 12;
    return `${feet}'${remainingInches}"`;
  };

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
    <div className="relative flex size-full min-h-screen flex-col bg-slate-50 group/design-root overflow-x-hidden" style={{fontFamily: 'Manrope, "Noto Sans", sans-serif'}}>
      <div className="layout-container flex h-full grow flex-col">
        {/* Header */}
        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-slate-200 px-10 py-3 bg-white">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3 text-slate-900">
              <div className="size-7 text-[#0c7ff2]">
                <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                  <path d="M24 45.8096C19.6865 45.8096 15.4698 44.5305 11.8832 42.134C8.29667 39.7376 5.50128 36.3314 3.85056 32.3462C2.19985 28.361 1.76794 23.9758 2.60947 19.7452C3.451 15.5145 5.52816 11.6284 8.57829 8.5783C11.6284 5.52817 15.5145 3.45101 19.7452 2.60948C23.9758 1.76795 28.361 2.19986 32.3462 3.85057C36.3314 5.50129 39.7376 8.29668 42.134 11.8833C44.5305 15.4698 45.8096 19.6865 45.8096 24L24 24L24 45.8096Z" fill="currentColor"></path>
                </svg>
              </div>
              <h2 className="text-slate-900 text-xl font-bold leading-tight tracking-[-0.015em]">Courtside</h2>
            </div>
            <nav className="flex items-center gap-6">
              <button onClick={() => navigate('/dashboard')} className="text-slate-600 hover:text-[#0c7ff2] text-sm font-medium leading-normal transition-colors">Dashboard</button>
              <button onClick={() => navigate('/my-teams')} className="text-slate-600 hover:text-[#0c7ff2] text-sm font-medium leading-normal transition-colors">My Teams</button>
              <button onClick={() => navigate('/players')} className="text-[#0c7ff2] text-sm font-bold leading-normal">Players</button>
              <button onClick={() => navigate('/games')} className="text-slate-600 hover:text-[#0c7ff2] text-sm font-medium leading-normal transition-colors">Games</button>
            </nav>
          </div>
          <div className="flex flex-1 justify-end gap-4">
            <button 
              onClick={() => navigate('/help')}
              className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 w-10 border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition-colors"
              title="Help"
            >
              <svg fill="currentColor" height="20px" viewBox="0 0 256 256" width="20px" xmlns="http://www.w3.org/2000/svg">
                <path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm16-40a8,8,0,0,1-8,8,16,16,0,0,1-16-16V128a8,8,0,0,1,0-16,16,16,0,0,1,16,16v40A8,8,0,0,1,144,176ZM112,84a12,12,0,1,1,12,12A12,12,0,0,1,112,84Z"></path>
              </svg>
            </button>
            <button 
              onClick={() => navigate('/settings')}
              className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 w-10 border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition-colors"
              title="Settings"
            >
              <svg fill="currentColor" height="20px" viewBox="0 0 256 256" width="20px" xmlns="http://www.w3.org/2000/svg">
                <path d="M128,80a48,48,0,1,0,48,48A48.05,48.05,0,0,0,128,80Zm0,80a32,32,0,1,1,32-32A32,32,0,0,1,128,160Zm88-29.84q.06-2.16,0-4.32l14.92-18.64a8,8,0,0,0,1.48-7.06,107.6,107.6,0,0,0-10.88-26.25,8,8,0,0,0-6-3.93l-23.72-2.64q-1.48-1.56-3.18-3.18L191.26,41a8,8,0,0,0-3.94-6,107.29,107.29,0,0,0-26.25-10.87,8,8,0,0,0-7.06,1.49L135.16,40Q131,40,128,40t-7.16,0L102.2,25.62a8,8,0,0,0-7.06-1.49A107.6,107.6,0,0,0,69,35,8,8,0,0,0,65,41L62.39,64.62Q60.84,66.18,59.16,67.86L35.44,70.5a8,8,0,0,0-3.94,6A107.71,107.71,0,0,0,20.62,102.75a8,8,0,0,0,1.48,7.06L37,128.16Q37,131,37,128t0,7.16L22.1,153.8a8,8,0,0,0-1.48,7.06,107.6,107.6,0,0,0,10.88,26.25,8,8,0,0,0,6,3.93l23.72,2.64q1.49,1.56,3.18,3.18L67,220a8,8,0,0,0,3.94,6,107.71,107.71,0,0,0,26.25,10.87,8,8,0,0,0,7.06-1.49L120.84,221q2.16.06,4.32,0l18.64,14.92a8,8,0,0,0,7.06,1.48,107.21,107.21,0,0,0,26.25-10.87,8,8,0,0,0,3.93-6l2.64-23.72q1.56-1.48,3.18-3.18L209,191.25a8,8,0,0,0,6-3.93,107.71,107.71,0,0,0,10.87-26.25,8,8,0,0,0-1.49-7.06Zm-16.1-6.5a73.93,73.93,0,0,1,0,8.68,8,8,0,0,0,1.74,5.48l14.19,17.73a91.57,91.57,0,0,1-6.23,15L187,173.11a8,8,0,0,0-5.1,2.64,74.11,74.11,0,0,1-6.14,6.14,8,8,0,0,0-2.64,5.1l-2.51,22.58a91.32,91.32,0,0,1-15,6.23l-17.74-14.19a8,8,0,0,0-5-1.75h-.48a73.93,73.93,0,0,1-8.68,0,8.06,8.06,0,0,0-5.48,1.74L100.45,215.8a91.57,91.57,0,0,1-15-6.23L82.89,187a8,8,0,0,0-2.64-5.1,74.11,74.11,0,0,1-6.14-6.14,8,8,0,0,0-5.1-2.64L46.43,170.6a91.32,91.32,0,0,1-6.23-15l14.19-17.74a8,8,0,0,0,1.74-5.48,73.93,73.93,0,0,1,0-8.68,8,8,0,0,0-1.74-5.48L40.2,100.45a91.57,91.57,0,0,1,6.23-15L69,82.89a8,8,0,0,0,5.1-2.64,74.11,74.11,0,0,1,6.14-6.14,8,8,0,0,0,2.64-5.1L85.4,46.43a91.32,91.32,0,0,1,15-6.23l17.74,14.19a8,8,0,0,0,5.48,1.74,73.93,73.93,0,0,1,8.68,0,8,8,0,0,0,5.48-1.74L155.55,40.2a91.57,91.57,0,0,1,15,6.23L173.11,69a8,8,0,0,0,2.64,5.1,74.11,74.11,0,0,1,6.14,6.14,8,8,0,0,0,5.1,2.64l22.58,2.51a91.32,91.32,0,0,1,6.23,15l-14.19,17.74A8,8,0,0,0,199.9,123.66Z"></path>
              </svg>
            </button>
            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border border-slate-300" style={{backgroundImage: 'url("https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face")'}}></div>
          </div>
        </header>

        <div className="grid grid-cols-[320px_1fr] flex-1 bg-slate-100">
          {/* Sidebar for teammates/search */}
          <aside className="flex flex-col border-r border-slate-200 bg-white overflow-y-auto">
            <div className="p-4 sticky top-0 bg-white z-10 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-3">Find Players</h3>
              <label className="flex flex-col min-w-40 h-10 w-full">
                <div className="flex w-full flex-1 items-stretch rounded-md h-full">
                  <div className="text-slate-400 flex border border-slate-300 bg-slate-50 items-center justify-center pl-3 rounded-l-md border-r-0">
                    <svg fill="currentColor" height="20px" viewBox="0 0 256 256" width="20px" xmlns="http://www.w3.org/2000/svg">
                      <path d="M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z"></path>
                    </svg>
                  </div>
                  <input
                    className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-md text-slate-900 focus:outline-0 focus:ring-2 focus:ring-[#0c7ff2] border border-slate-300 bg-slate-50 h-full placeholder:text-slate-400 px-3 rounded-l-none border-l-0 pl-2 text-sm font-normal leading-normal"
                    placeholder="Search players"
                    value={searchQuery}
                    onChange={handleSearchChange}
                  />
                </div>
              </label>
            </div>
            <div className="flex flex-col">
              {searchLoading && (
                <div className="p-4 text-center text-sm text-slate-500">Searching...</div>
              )}
              {Array.isArray(searchResults) && searchResults.length > 0 ? (
                searchResults.map(player => (
                  <button
                    key={player.player_id}
                    onClick={() => navigate(`/player/${player.player_id}`)}
                    className={`flex items-center gap-3 hover:bg-slate-50 px-4 py-3 transition-colors ${
                      player.player_id === playerStats.player_id ? 'bg-[#0c7ff2]/10 border-l-4 border-[#0c7ff2]' : ''
                    }`}
                  >
                    <div className={`bg-center bg-no-repeat aspect-square bg-cover rounded-full h-9 w-9 border ${
                      player.player_id === playerStats.player_id ? 'border-[#0c7ff2]' : 'border-slate-200'
                    }`} style={{backgroundImage: `url("${player.headshot_url || 'https://via.placeholder.com/36x36'}")`}}></div>
                    <div className="flex-1 text-left">
                      <p className={`text-sm font-medium leading-normal truncate ${
                        player.player_id === playerStats.player_id ? 'text-[#0c7ff2] font-bold' : 'text-slate-700'
                      }`}>{player.full_name}</p>
                      <p className="text-xs text-slate-500">{player.position} - {player.team_abbr}</p>
                    </div>
                  </button>
                ))
              ) : searchQuery.trim() ? (
                <div className="p-4 text-center text-sm text-slate-500">
                  No players found matching "{searchQuery}"
                </div>
              ) : (
                <div className="p-4 text-center text-sm text-slate-500">
                  <p className="mb-2">Start typing to search for players</p>
                  <p className="text-xs">or browse by team and position</p>
                </div>
              )}
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-between gap-4 mb-6">
                <h1 className="text-slate-900 text-3xl font-bold leading-tight">{playerStats.player_name}</h1>
                <button className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[#0c7ff2] text-white text-sm font-semibold hover:bg-[#0c7ff2]/90 transition-colors">
                  <svg fill="currentColor" height="16" viewBox="0 0 256 256" width="16" xmlns="http://www.w3.org/2000/svg">
                    <path d="M235.31,116.69l-48-48a8,8,0,0,0-11.32,0L128,116.69,80,68.69l-48,48a8,8,0,0,0,0,11.31L80,176,32,224a8,8,0,0,0,11.31,11.31L128,150.63l84.69,84.68A8,8,0,0,0,224,224l-48-48,48-48A8,8,0,0,0,235.31,116.69ZM128,135.31L53.66,61,61,53.66,128,120.69,195.31,53l7.35,7.34L128,135.31Zm0,35.38L43.31,256l-11.31-11.31L116.69,128,139.31,150.63,54.63,235.31,61,229Z"></path>
                  </svg>
                  Compare Players
                </button>
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
              <div className="mb-6">
                <div className="flex border-b border-slate-300">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 px-4 text-sm font-semibold leading-normal transition-colors ${
                      activeTab === 'overview'
                        ? 'border-[#0c7ff2] text-[#0c7ff2] font-bold'
                        : 'border-transparent text-slate-600 hover:text-[#0c7ff2]'
                    }`}
                  >
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('gamelog')}
                    className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 px-4 text-sm font-semibold leading-normal transition-colors ${
                      activeTab === 'gamelog'
                        ? 'border-[#0c7ff2] text-[#0c7ff2] font-bold'
                        : 'border-transparent text-slate-600 hover:text-[#0c7ff2]'
                    }`}
                  >
                    Stats
                  </button>
                  <button
                    onClick={() => setActiveTab('teammates')}
                    className={`flex items-center justify-center border-b-[3px] pb-3 pt-2 px-4 text-sm font-semibold leading-normal transition-colors ${
                      activeTab === 'teammates'
                        ? 'border-[#0c7ff2] text-[#0c7ff2] font-bold'
                        : 'border-transparent text-slate-600 hover:text-[#0c7ff2]'
                    }`}
                  >
                    Teammates
                  </button>
                </div>
              </div>

              {/* Tab Content */}
              {activeTab === 'gamelog' && (
                <section className="mb-8">
                  <h2 className="text-slate-900 text-xl font-bold leading-tight mb-4">Season Stats</h2>
                  <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">Season</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">Team</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">GP</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">GS</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">MPG</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">FG%</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">3P%</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">FT%</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">RPG</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">APG</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">SPG</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">BPG</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">TOV</th>
                          <th className="px-4 py-3 text-left text-slate-600 font-semibold">PPG</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-t border-slate-200">
                          <td className="px-4 py-3 text-slate-700">{playerStats.season}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.team_abbr || 'N/A'}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.games_played}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.games_started}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.mpg.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.fg_percentage.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.three_point_percentage.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.ft_percentage.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.rpg.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.apg.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.spg.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.bpg.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.topg.toFixed(1)}</td>
                          <td className="px-4 py-3 text-slate-700">{playerStats.ppg.toFixed(1)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {activeTab === 'teammates' && (
                <section className="mb-8">
                  <h2 className="text-slate-900 text-xl font-bold leading-tight mb-4">Team Information</h2>
                  <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">{playerStats.team_name || 'Team Information'}</h3>
                      <p className="text-slate-600 text-sm">
                        {playerStats.player_name} currently plays for the {playerStats.team_name || 'team'} ({playerStats.team_abbr || 'N/A'}).
                      </p>
                    </div>
                    
                    <div className="border-t border-slate-200 pt-4">
                      <h4 className="font-medium text-slate-900 mb-3">Player Information</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-slate-500">Position:</span>
                          <span className="ml-2 font-medium">{playerStats.position || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Jersey:</span>
                          <span className="ml-2 font-medium">#{playerStats.jersey_number || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Height:</span>
                          <span className="ml-2 font-medium">{formatHeight(playerStats.height)}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Weight:</span>
                          <span className="ml-2 font-medium">{playerStats.weight ? `${playerStats.weight} lbs` : 'N/A'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="border-t border-slate-200 pt-4 mt-4">
                      <p className="text-xs text-slate-500">
                        To view teammates and team roster, visit the team page or use the player search to find other players on this team.
                      </p>
                    </div>
                  </div>
                </section>
              )}

              {activeTab === 'overview' && (
                <>
                  <section className="mb-8">
                    <h2 className="text-slate-900 text-xl font-bold leading-tight mb-4">Performance Trends</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                        <p className="text-slate-700 text-base font-semibold leading-normal mb-1">Points Per Game</p>
                        <p className="text-slate-900 text-3xl font-bold leading-tight truncate mb-0.5">{playerStats.ppg.toFixed(1)}</p>
                        <div className="flex gap-1.5 items-center mb-4">
                          <p className="text-slate-500 text-xs font-medium">Last {Math.min(gameLog.length, 5)} Games</p>
                          {gameLog.length >= 2 && (
                            <p className={`text-xs font-semibold ${
                              gameLog[0]?.points > gameLog[1]?.points ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {gameLog[0]?.points > gameLog[1]?.points ? '+' : ''}
                              {gameLog.length >= 2 ? ((gameLog[0]?.points - gameLog[1]?.points) || 0).toFixed(1) : '0.0'}
                            </p>
                          )}
                        </div>
                        <div className="h-36 flex items-end space-x-2">
                          {gameLog.slice(0, 5).reverse().map((game, index) => {
                            const maxPoints = Math.max(...gameLog.slice(0, 5).map(g => g.points)) || 1;
                            const height = (game.points / maxPoints) * 100;
                            return (
                              <div key={index} className="flex-1 flex flex-col items-center">
                                <div 
                                  className="w-full bg-[#0c7ff2] rounded-t-sm transition-all duration-300 hover:bg-[#0a6bc8]"
                                  style={{ height: `${height}%`, minHeight: '4px' }}
                                  title={`${game.points} points vs ${game.opponent_abbr}`}
                                ></div>
                                <span className="text-xs text-slate-500 mt-1">{game.points}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                        <p className="text-slate-700 text-base font-semibold leading-normal mb-1">Rebounds Per Game</p>
                        <p className="text-slate-900 text-3xl font-bold leading-tight truncate mb-0.5">{playerStats.rpg.toFixed(1)}</p>
                        <div className="flex gap-1.5 items-center mb-4">
                          <p className="text-slate-500 text-xs font-medium">Last {Math.min(gameLog.length, 5)} Games</p>
                          {gameLog.length >= 2 && (
                            <p className={`text-xs font-semibold ${
                              gameLog[0]?.rebounds > gameLog[1]?.rebounds ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {gameLog[0]?.rebounds > gameLog[1]?.rebounds ? '+' : ''}
                              {gameLog.length >= 2 ? ((gameLog[0]?.rebounds - gameLog[1]?.rebounds) || 0).toFixed(1) : '0.0'}
                            </p>
                          )}
                        </div>
                        <div className="h-36 flex items-end space-x-2">
                          {gameLog.slice(0, 5).reverse().map((game, index) => {
                            const maxRebounds = Math.max(...gameLog.slice(0, 5).map(g => g.rebounds)) || 1;
                            const height = (game.rebounds / maxRebounds) * 100;
                            return (
                              <div key={index} className="flex-1 flex flex-col items-center">
                                <div 
                                  className="w-full bg-[#0c7ff2] rounded-t-sm transition-all duration-300 hover:bg-[#0a6bc8]"
                                  style={{ height: `${height}%`, minHeight: '4px' }}
                                  title={`${game.rebounds} rebounds vs ${game.opponent_abbr}`}
                                ></div>
                                <span className="text-xs text-slate-500 mt-1">{game.rebounds}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </section>

                  <section>
                    <h2 className="text-slate-900 text-xl font-bold leading-tight mb-4">Fantasy Projections</h2>
                    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-100">
                          <tr>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Date</th>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Opponent</th>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Minutes</th>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Points</th>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Rebounds</th>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Assists</th>
                            <th className="px-4 py-3 text-left text-slate-600 font-semibold">Fantasy Points</th>
                          </tr>
                        </thead>
                        <tbody>
                          {gameLog.slice(0, 3).map((game) => (
                            <tr key={game.game_id} className="border-t border-slate-200">
                              <td className="px-4 py-3 text-slate-700">{new Date(game.date).toLocaleDateString()}</td>
                              <td className="px-4 py-3 text-slate-700">{game.is_home ? 'vs' : 'at'} {game.opponent_abbr}</td>
                              <td className="px-4 py-3 text-slate-700">{game.minutes_played}</td>
                              <td className="px-4 py-3 text-slate-700">{game.points}</td>
                              <td className="px-4 py-3 text-slate-700">{game.rebounds}</td>
                              <td className="px-4 py-3 text-slate-700">{game.assists}</td>
                              <td className="px-4 py-3 text-slate-700 font-semibold text-[#0c7ff2]">{(game.points + game.rebounds + game.assists + game.steals + game.blocks - game.turnovers).toFixed(1)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default PlayerDetailPage;