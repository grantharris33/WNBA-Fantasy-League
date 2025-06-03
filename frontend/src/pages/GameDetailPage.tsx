import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

interface PlayByPlayEvent {
  clock: string;
  description: string;
  team_id: string | null;
  period: number;
}

interface PlayByPlayResponse {
  game_id: string;
  events: PlayByPlayEvent[];
}

interface GameInfo {
  id: string;
  date: string;
  home_team_id: number;
  away_team_id: number;
  home_score: number;
  away_score: number;
  status: string;
  venue: string;
  attendance: number | null;
}

interface PlayerStats {
  player_id: number;
  player_name: string;
  position: string;
  is_starter: boolean;
  did_not_play: boolean;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  minutes_played: number;
  field_goals_made: number;
  field_goals_attempted: number;
  field_goal_percentage: number;
  three_pointers_made: number;
  three_pointers_attempted: number;
  three_point_percentage: number;
  free_throws_made: number;
  free_throws_attempted: number;
  free_throw_percentage: number;
  offensive_rebounds: number;
  defensive_rebounds: number;
  turnovers: number;
  personal_fouls: number;
  plus_minus: number;
  team_id: number;
  opponent_id: number;
  is_home_game: boolean;
}

interface ComprehensiveStatsResponse {
  game: GameInfo;
  player_stats: PlayerStats[];
}

const GameDetailPage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [gameStats, setGameStats] = useState<ComprehensiveStatsResponse | null>(null);
  const [playByPlay, setPlayByPlay] = useState<PlayByPlayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'stats' | 'playbyplay'>('stats');

  const fetchGameData = useCallback(async () => {
    if (!gameId) return;

    setLoading(true);
    setError(null);
    try {
      const [statsData, playByPlayData] = await Promise.all([
        api.games.getComprehensiveStats(gameId),
        api.games.getPlayByPlay(gameId)
      ]);

      setGameStats(statsData);
      setPlayByPlay(playByPlayData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch game data');
      toast.error('Failed to load game details');
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchGameData();
  }, [fetchGameData]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner message="Loading game details..." />
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

  if (!gameStats || !playByPlay) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Game Not Found</h1>
        <p className="text-gray-600 mb-6">The game details you're looking for are not available.</p>
        <button
          onClick={() => navigate(-1)}
          className="btn-primary"
        >
          Go Back
        </button>
      </div>
    );
  }

  const { game, player_stats } = gameStats;

  // Group players by team
  const homeTeamPlayers = player_stats.filter(p => p.team_id === game.home_team_id);
  const awayTeamPlayers = player_stats.filter(p => p.team_id === game.away_team_id);

  // Group events by period for play-by-play
  const eventsByPeriod = playByPlay.events.reduce((acc, event) => {
    if (!acc[event.period]) acc[event.period] = [];
    acc[event.period].push(event);
    return acc;
  }, {} as Record<number, PlayByPlayEvent[]>);

  const formatPlayerStats = (player: PlayerStats) => {
    const fg = `${player.field_goals_made}/${player.field_goals_attempted}`;
    const threePt = `${player.three_pointers_made}/${player.three_pointers_attempted}`;
    const ft = `${player.free_throws_made}/${player.free_throws_attempted}`;
    return { fg, threePt, ft };
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-blue-600 hover:text-blue-800 text-sm mb-2 flex items-center gap-1"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Game Details</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
            <span>{new Date(game.date).toLocaleDateString()}</span>
            <span>{game.venue}</span>
            {game.attendance && <span>{game.attendance.toLocaleString()} attendance</span>}
          </div>
        </div>
      </div>

      {/* Game Score */}
      <div className="card p-6">
        <div className="text-center">
          <div className="text-sm text-gray-500 mb-2">Final Score</div>
          <div className="flex justify-center items-center gap-8">
            <div className="text-center">
              <div className="text-lg font-medium text-gray-600">Away Team (ID: {game.away_team_id})</div>
              <div className="text-4xl font-bold text-gray-900">{game.away_score}</div>
            </div>
            <div className="text-2xl text-gray-400">-</div>
            <div className="text-center">
              <div className="text-lg font-medium text-gray-600">Home Team (ID: {game.home_team_id})</div>
              <div className="text-4xl font-bold text-gray-900">{game.home_score}</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-500 capitalize">{game.status}</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('stats')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'stats'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Player Statistics
          </button>
          <button
            onClick={() => setActiveTab('playbyplay')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'playbyplay'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Play-by-Play
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'stats' && (
        <div className="space-y-8">
          {/* Away Team Stats */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Away Team (ID: {game.away_team_id}) - {game.away_score}
            </h2>
            <div className="card overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Player</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Min</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pts</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reb</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ast</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FG</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">3PT</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FT</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">+/-</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {awayTeamPlayers
                    .filter(p => !p.did_not_play)
                    .sort((a, b) => (b.is_starter ? 1 : 0) - (a.is_starter ? 1 : 0))
                    .map(player => {
                      const { fg, threePt, ft } = formatPlayerStats(player);
                      return (
                        <tr key={player.player_id} className={player.is_starter ? 'bg-blue-50' : ''}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="font-medium text-gray-900">{player.player_name}</div>
                              <div className="text-sm text-gray-500">{player.position}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.minutes_played}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{player.points}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.rebounds}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.assists}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{fg}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{threePt}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{ft}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.plus_minus > 0 ? '+' : ''}{player.plus_minus}</td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </section>

          {/* Home Team Stats */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Home Team (ID: {game.home_team_id}) - {game.home_score}
            </h2>
            <div className="card overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Player</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Min</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pts</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reb</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ast</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FG</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">3PT</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FT</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">+/-</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {homeTeamPlayers
                    .filter(p => !p.did_not_play)
                    .sort((a, b) => (b.is_starter ? 1 : 0) - (a.is_starter ? 1 : 0))
                    .map(player => {
                      const { fg, threePt, ft } = formatPlayerStats(player);
                      return (
                        <tr key={player.player_id} className={player.is_starter ? 'bg-blue-50' : ''}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="font-medium text-gray-900">{player.player_name}</div>
                              <div className="text-sm text-gray-500">{player.position}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.minutes_played}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{player.points}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.rebounds}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.assists}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{fg}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{threePt}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{ft}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{player.plus_minus > 0 ? '+' : ''}{player.plus_minus}</td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {activeTab === 'playbyplay' && (
        <div className="space-y-6">
          {Object.keys(eventsByPeriod)
            .sort((a, b) => parseInt(b) - parseInt(a))
            .map(period => (
              <section key={period} className="card p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  {period === '1' ? '1st Quarter' :
                   period === '2' ? '2nd Quarter' :
                   period === '3' ? '3rd Quarter' :
                   period === '4' ? '4th Quarter' :
                   `Period ${period}`}
                </h3>
                <div className="space-y-2">
                  {eventsByPeriod[parseInt(period)]
                    .slice()
                    .reverse()
                    .map((event, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-start p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex-1">
                          <span className="text-sm text-gray-900">{event.description}</span>
                        </div>
                        <div className="text-sm font-mono text-gray-600 ml-4">
                          {event.clock}
                        </div>
                      </div>
                    ))}
                </div>
              </section>
            ))}
        </div>
      )}
    </div>
  );
};

export default GameDetailPage;