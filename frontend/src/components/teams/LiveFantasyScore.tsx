import React, { useState, useEffect, useCallback } from 'react';

interface LiveFantasyScore {
  team_id: number;
  total_fantasy_points: number;
  starter_points: number;
  player_scores: Array<{
    player_id: number;
    player_name: string;
    position?: string;
    is_starter: boolean;
    fantasy_points: number;
    has_live_game: boolean;
  }>;
  last_updated: string;
}

interface LiveFantasyScoreProps {
  teamId: number;
  autoUpdate?: boolean;
  updateInterval?: number; // in seconds
}

const LiveFantasyScore: React.FC<LiveFantasyScoreProps> = ({ 
  teamId, 
  autoUpdate = true, 
  updateInterval = 60 
}) => {
  const [fantasyScore, setFantasyScore] = useState<LiveFantasyScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const fetchFantasyScore = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/live/teams/${teamId}/fantasy-score`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch live fantasy score');
      }

      const data = await response.json();
      setFantasyScore(data);
      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch fantasy score');
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  const connectWebSocket = useCallback(() => {
    if (!autoUpdate) return;

    const WS_URL_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${WS_URL_BASE}/api/v1/live/ws/teams/${teamId}/fantasy-score`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected to live fantasy score:', teamId);
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Live fantasy score update received:', message);

        switch (message.event) {
          case 'initial_fantasy_score':
            setFantasyScore(message.data);
            setLastUpdate(new Date().toLocaleTimeString());
            break;
          case 'fantasy_score_update':
            setFantasyScore(message.data);
            setLastUpdate(new Date().toLocaleTimeString());
            break;
          case 'pong':
            // Keep-alive response
            break;
          default:
            console.log('Unknown fantasy score event:', message.event);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected from live fantasy score');
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
  }, [teamId, autoUpdate]);

  useEffect(() => {
    fetchFantasyScore();
    
    let cleanup: (() => void) | undefined;
    if (autoUpdate) {
      cleanup = connectWebSocket();
    }

    // Fallback polling if WebSocket is not available
    const pollInterval = setInterval(() => {
      if (!isConnected && autoUpdate) {
        fetchFantasyScore();
      }
    }, updateInterval * 1000);

    return () => {
      clearInterval(pollInterval);
      if (cleanup) cleanup();
    };
  }, [fetchFantasyScore, connectWebSocket, autoUpdate, updateInterval, isConnected]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/4 mb-2"></div>
        <div className="h-8 bg-slate-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 text-sm">
        <span className="material-icons text-sm mr-1">error</span>
        {error}
      </div>
    );
  }

  if (!fantasyScore) {
    return (
      <div className="text-slate-500 text-sm">
        No fantasy score data available
      </div>
    );
  }

  const activePlayers = fantasyScore.player_scores.filter(p => p.has_live_game);
  const starterCount = fantasyScore.player_scores.filter(p => p.is_starter).length;

  return (
    <div className="space-y-4">
      {/* Main Score Display */}
      <div className="bg-gradient-to-r from-[#0c7ff2] to-[#0a68c4] rounded-lg p-4 text-white">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold">Live Fantasy Score</h3>
          {autoUpdate && (
            <div className="flex items-center text-sm">
              <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-400' : 'bg-yellow-400'}`}></div>
              {isConnected ? 'Live' : 'Polling'}
            </div>
          )}
        </div>
        <div className="text-3xl font-bold mb-1">
          {fantasyScore.total_fantasy_points.toFixed(1)} pts
        </div>
        <div className="text-sm opacity-90">
          Starters: {fantasyScore.starter_points.toFixed(1)} pts ({starterCount} players)
        </div>
      </div>

      {/* Live Players Summary */}
      {activePlayers.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-slate-900">Players in Live Games</h4>
            <span className="text-sm text-slate-500">{activePlayers.length} active</span>
          </div>
          <div className="space-y-2">
            {activePlayers
              .sort((a, b) => b.fantasy_points - a.fantasy_points)
              .slice(0, 5) // Show top 5 performers
              .map((player) => (
                <div key={player.player_id} className="flex items-center justify-between">
                  <div className="flex items-center">
                    {player.is_starter && (
                      <span className="material-icons text-yellow-500 text-sm mr-1">star</span>
                    )}
                    <div>
                      <span className="text-sm font-medium text-slate-900">{player.player_name}</span>
                      <span className="text-xs text-slate-500 ml-1">({player.position})</span>
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-[#0c7ff2]">
                    {player.fantasy_points.toFixed(1)}
                  </span>
                </div>
              ))}
          </div>
          {activePlayers.length > 5 && (
            <div className="text-xs text-slate-500 mt-2 text-center">
              +{activePlayers.length - 5} more players
            </div>
          )}
        </div>
      )}

      {/* Update Info */}
      <div className="text-xs text-slate-500 text-center">
        {lastUpdate && `Last updated: ${lastUpdate}`}
        {activePlayers.length === 0 && (
          <div className="text-sm text-slate-600 mt-2">
            No players in live games today
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveFantasyScore;