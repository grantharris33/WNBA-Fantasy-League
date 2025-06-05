import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';

interface LiveGameData {
  game_id: string;
  status: string;
  quarter?: number;
  time_remaining?: string;
  last_update: string;
  home_team: {
    id: number;
    name: string;
    score: number;
  };
  away_team: {
    id: number;
    name: string;
    score: number;
  };
  live_stats: Array<{
    player_id: number;
    player_name: string;
    position?: string;
    team_abbr?: string;
    points: number;
    rebounds: number;
    assists: number;
    steals: number;
    blocks: number;
    turnovers: number;
    fantasy_points: number;
    is_final: boolean;
  }>;
}


const LiveGameTracker: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const [gameData, setGameData] = useState<LiveGameData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const connectWebSocket = useCallback(() => {
    if (!gameId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/live/ws/games/${gameId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected to live game:', gameId);
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Live game update received:', message);

        switch (message.event) {
          case 'initial_data':
            setGameData(message.data);
            setLastUpdate(new Date().toLocaleTimeString());
            break;
          case 'game_update':
            setGameData(prev => prev ? { ...prev, ...message.data } : message.data);
            setLastUpdate(new Date().toLocaleTimeString());
            break;
          case 'player_stats_update':
            setGameData(prev => prev ? { 
              ...prev, 
              live_stats: message.data.live_stats 
            } : prev);
            setLastUpdate(new Date().toLocaleTimeString());
            break;
          case 'pong':
            // Keep-alive response
            break;
          default:
            console.log('Unknown live game event:', message.event);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected from live game');
      setIsConnected(false);
      // Attempt to reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error. Retrying...');
    };

    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [gameId]);

  const fetchLiveGameData = useCallback(async () => {
    if (!gameId) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/v1/live/games/${gameId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch live game data');
      }

      const data = await response.json();
      setGameData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch live game data');
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchLiveGameData();
    const cleanup = connectWebSocket();
    
    return cleanup;
  }, [fetchLiveGameData, connectWebSocket]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'in_progress':
        return 'text-green-600 bg-green-100';
      case 'final':
        return 'text-gray-600 bg-gray-100';
      case 'scheduled':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatStatus = (status: string, quarter?: number, timeRemaining?: string) => {
    if (status === 'in_progress') {
      if (quarter && timeRemaining) {
        return `Q${quarter} - ${timeRemaining}`;
      }
      return 'Live';
    }
    if (status === 'final') return 'Final';
    if (status === 'scheduled') return 'Scheduled';
    return status;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0c7ff2]"></div>
        <span className="ml-2 text-slate-600">Loading live game data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <span className="material-icons text-red-500 mr-2">error</span>
          <span className="text-red-700">{error}</span>
        </div>
        <button
          onClick={fetchLiveGameData}
          className="mt-2 text-red-600 hover:text-red-800 text-sm underline"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!gameData) {
    return (
      <div className="text-center p-8 text-slate-600">
        No live game data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between bg-slate-50 rounded-lg p-3">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-slate-600">
            {isConnected ? 'Live Updates Connected' : 'Reconnecting...'}
          </span>
        </div>
        {lastUpdate && (
          <span className="text-xs text-slate-500">
            Last update: {lastUpdate}
          </span>
        )}
      </div>

      {/* Game Header */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(gameData.status)}`}>
            {formatStatus(gameData.status, gameData.quarter, gameData.time_remaining)}
          </div>
          <div className="text-sm text-slate-500">
            Game ID: {gameData.game_id}
          </div>
        </div>

        {/* Score Display */}
        <div className="grid grid-cols-3 gap-4 items-center">
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-900">{gameData.away_team.name}</div>
            <div className="text-3xl font-bold text-slate-800">{gameData.away_team.score}</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-slate-500 uppercase tracking-wide">VS</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-900">{gameData.home_team.name}</div>
            <div className="text-3xl font-bold text-slate-800">{gameData.home_team.score}</div>
          </div>
        </div>
      </div>

      {/* Live Player Stats */}
      {gameData.live_stats.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900">Live Player Stats</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Player</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">PTS</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">REB</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">AST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">STL</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">BLK</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">TO</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">FPTS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {gameData.live_stats
                  .sort((a, b) => b.fantasy_points - a.fantasy_points)
                  .map((stat) => (
                    <tr key={stat.player_id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div>
                          <div className="text-sm font-medium text-slate-900">{stat.player_name}</div>
                          <div className="text-xs text-slate-500">{stat.position} • {stat.team_abbr}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900">{stat.points}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{stat.rebounds}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{stat.assists}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{stat.steals}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{stat.blocks}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{stat.turnovers}</td>
                      <td className="px-4 py-3">
                        <span className="text-sm font-semibold text-[#0c7ff2]">
                          {stat.fantasy_points.toFixed(1)}
                        </span>
                        {stat.is_final && (
                          <span className="ml-1 text-xs text-green-600">(Final)</span>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Live Fantasy Scores Section */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Live Fantasy Impact</h3>
        <div className="text-sm text-slate-600">
          Fantasy points are calculated in real-time and update as the game progresses.
          Final scores will be reflected in your team's weekly totals after the game ends.
        </div>
      </div>
    </div>
  );
};

export default LiveGameTracker;