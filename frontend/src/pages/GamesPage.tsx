import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import DashboardLayout from '../components/layout/DashboardLayout';

interface GameInfo {
  game_id: string;
  start_time: string;
  venue: string;
  completed: boolean;
  competitors: Array<{
    team_id: string;
    abbrev: string;
    display_name: string;
    score: number;
    is_home: boolean;
    winner: boolean | null;
  }>;
}

interface ScheduleDay {
  date: string;
  games: GameInfo[];
}

const GamesPage: React.FC = () => {
  const navigate = useNavigate();
  const [scheduleData, setScheduleData] = useState<ScheduleDay | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'upcoming'>('all');
  const [teamFilter, setTeamFilter] = useState('');

  const fetchGames = useCallback(async (date: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.games.getSchedule(date);
      setScheduleData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch games');
      toast.error('Failed to load games');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGames(selectedDate);
  }, [fetchGames, selectedDate]);

  const filteredGames = useMemo(() => {
    if (!scheduleData?.games) return [];

    return scheduleData.games.filter(game => {
      // Status filter
      if (statusFilter === 'completed' && !game.completed) return false;
      if (statusFilter === 'upcoming' && game.completed) return false;

      // Team filter
      if (teamFilter) {
        const hasTeam = game.competitors.some(
          competitor =>
            competitor.abbrev.toLowerCase().includes(teamFilter.toLowerCase()) ||
            competitor.display_name.toLowerCase().includes(teamFilter.toLowerCase())
        );
        if (!hasTeam) return false;
      }

      return true;
    });
  }, [scheduleData, statusFilter, teamFilter]);

  const availableTeams = useMemo(() => {
    if (!scheduleData?.games) return [];
    const teams = new Set<string>();
    scheduleData.games.forEach(game => {
      game.competitors.forEach(competitor => {
        teams.add(competitor.display_name);
      });
    });
    return Array.from(teams).sort();
  }, [scheduleData]);

  const formatDateTime = (dateTime: string) => {
    const date = new Date(dateTime);
    return {
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      date: date.toLocaleDateString()
    };
  };

  const getGameStatus = (game: GameInfo) => {
    if (game.completed) {
      const winner = game.competitors.find(c => c.winner);
      const loser = game.competitors.find(c => !c.winner);
      return {
        status: 'completed',
        text: 'Final',
        winner: winner?.display_name,
        score: `${winner?.score || 0} - ${loser?.score || 0}`
      };
    } else {
      const now = new Date();
      const gameTime = new Date(game.start_time);
      if (gameTime > now) {
        return {
          status: 'upcoming',
          text: formatDateTime(game.start_time).time,
          score: 'vs'
        };
      } else {
        return {
          status: 'in_progress',
          text: 'In Progress',
          score: `${game.competitors[0]?.score || 0} - ${game.competitors[1]?.score || 0}`
        };
      }
    }
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedDate(e.target.value);
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner message="Loading games..." />
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
            onClick={() => fetchGames(selectedDate)}
            className="mt-4 bg-[#0c7ff2] hover:bg-[#0a68c4] text-white font-medium py-2 px-4 rounded-lg transition-colors"
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
          <h1 className="text-3xl font-bold leading-tight text-[#0d141c]">WNBA Games</h1>
          <p className="text-slate-500 text-sm font-normal leading-normal mt-2">
            View game schedules, scores, and results
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Filter Games</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="date" className="block text-sm font-medium text-slate-700 mb-1">
                Date
              </label>
              <input
                id="date"
                type="date"
                value={selectedDate}
                onChange={handleDateChange}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-[#0c7ff2] focus:border-[#0c7ff2] transition-colors"
              />
            </div>
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-slate-700 mb-1">
                Status
              </label>
              <select
                id="status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-[#0c7ff2] focus:border-[#0c7ff2] bg-white transition-colors"
              >
                <option value="all">All Games</option>
                <option value="completed">Completed</option>
                <option value="upcoming">Upcoming</option>
              </select>
            </div>
            <div>
              <label htmlFor="team" className="block text-sm font-medium text-slate-700 mb-1">
                Team
              </label>
              <select
                id="team"
                value={teamFilter}
                onChange={(e) => setTeamFilter(e.target.value)}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-[#0c7ff2] focus:border-[#0c7ff2] bg-white transition-colors"
              >
                <option value="">All Teams</option>
                {availableTeams.map(team => (
                  <option key={team} value={team}>{team}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setStatusFilter('all');
                  setTeamFilter('');
                  setSelectedDate(new Date().toISOString().split('T')[0]);
                }}
                className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Games */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-slate-900">
              Games for {new Date(selectedDate).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </h2>
            <div className="text-sm text-slate-600">
              {filteredGames.length} game{filteredGames.length !== 1 ? 's' : ''}
            </div>
          </div>

          {filteredGames.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-slate-500 mb-4">No games found</div>
              <p className="text-sm text-slate-400">
                {scheduleData?.games.length === 0
                  ? 'No games scheduled for this date'
                  : 'No games match your current filters'
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredGames.map(game => {
                const gameStatus = getGameStatus(game);
                const away = game.competitors.find(c => !c.is_home);
                const home = game.competitors.find(c => c.is_home);

                return (
                  <div
                    key={game.game_id}
                    onClick={() => navigate(`/game/${game.game_id}`)}
                    className="bg-white border border-slate-200 rounded-lg p-6 hover:shadow-lg hover:border-[#0c7ff2] cursor-pointer transition-all duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        {/* Teams */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-4">
                            <div className="text-right">
                              <div className="font-semibold text-slate-900">{away?.display_name}</div>
                              <div className="text-sm text-slate-600">{away?.abbrev}</div>
                            </div>
                            <div className="text-2xl font-bold text-slate-400">@</div>
                            <div className="text-left">
                              <div className="font-semibold text-slate-900">{home?.display_name}</div>
                              <div className="text-sm text-slate-600">{home?.abbrev}</div>
                            </div>
                          </div>

                          {/* Score/Status */}
                          <div className="text-right">
                            <div className={`text-lg font-bold ${
                              gameStatus.status === 'completed' ? 'text-slate-900' :
                              gameStatus.status === 'in_progress' ? 'text-green-600' :
                              'text-[#0c7ff2]'
                            }`}>
                              {gameStatus.status === 'upcoming' ? gameStatus.text : gameStatus.score}
                            </div>
                            <div className="text-sm text-slate-600">{gameStatus.text}</div>
                          </div>
                        </div>

                        {/* Game Details */}
                        <div className="flex items-center justify-between text-sm text-slate-500">
                          <div>
                            {game.venue && <span>{game.venue}</span>}
                          </div>
                          <div>
                            {formatDateTime(game.start_time).date}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default GamesPage;