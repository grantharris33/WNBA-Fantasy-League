import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import type { CurrentScores, UserTeam } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

import DashboardLayout from '../components/layout/DashboardLayout';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentScoresData, setCurrentScoresData] = useState<CurrentScores>([]);
  const [scoresLoading, setScoresLoading] = useState<boolean>(true);
  const [scoresError, setScoresError] = useState<string | null>(null);
  const [userTeams, setUserTeams] = useState<UserTeam[]>([]);
  const [recentGames, setRecentGames] = useState<Array<{ id: string; date: string; home_team: string; away_team: string; home_score: number; away_score: number }>>([]);

  const fetchCurrentScores = useCallback(async () => {
    setScoresLoading(true);
    setScoresError(null);
    try {
      const scores = await api.scores.getCurrent();
      setCurrentScoresData(scores);
    } catch (error) {
      setScoresError(error instanceof Error ? error.message : 'Failed to fetch current scores.');
    }
    setScoresLoading(false);
  }, []);

  const fetchUserTeams = useCallback(async () => {
    try {
      const teams = await api.users.getMyTeams();
      setUserTeams(teams);
    } catch (error) {
      console.error('Failed to fetch user teams:', error);
    }
  }, []);

  const fetchRecentGames = useCallback(async () => {
    try {
      const games = await api.games.getRecentGames();
      setRecentGames(games);
    } catch (error) {
      console.error('Failed to fetch recent games:', error);
    }
  }, []);

  useEffect(() => {
    fetchCurrentScores();
    fetchUserTeams();
    fetchRecentGames();
  }, [fetchCurrentScores, fetchUserTeams, fetchRecentGames]);

  const totalSeasonPoints = Array.isArray(userTeams) ? userTeams.reduce((sum, team) => sum + (team?.season_points || 0), 0) : 0;
  const totalMovesUsed = Array.isArray(userTeams) ? userTeams.reduce((sum, team) => sum + (team?.moves_this_week || 0), 0) : 0;

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold leading-tight text-[#0d141c]">League Dashboard</h1>
        <p className="text-slate-500 text-sm font-normal leading-normal">Welcome back! Here's a snapshot of your league.</p>
      </div>

      {/* League Standings Section */}
      <section className="mb-8">
        <h2 className="text-2xl font-bold leading-tight tracking-[-0.015em] text-[#0d141c] mb-4">League Standings</h2>
        <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
          {scoresLoading && (
            <div className="p-8">
              <LoadingSpinner message="Loading current standings..." />
            </div>
          )}

          {scoresError && (
            <div className="p-6">
              <ErrorMessage message={scoresError} />
            </div>
          )}

          {!scoresLoading && !scoresError && Array.isArray(currentScoresData) && currentScoresData.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px]">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Rank</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Team</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Owner</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Wins</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Losses</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {currentScoresData.map((score, index) => (
                    <tr key={score.team_id || index} className="hover:bg-slate-50 transition-colors cursor-pointer" onClick={() => navigate(`/team/${score.team_id}`)}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-700">{index + 1}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-[#0c7ff2]">{score.team_name || 'Unknown Team'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{score.owner_name || 'Unknown'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">-</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">-</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-800">
                        {typeof score.season_points === 'number' ? score.season_points.toFixed(1) : '0.0'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!scoresLoading && !scoresError && (!currentScoresData || currentScoresData.length === 0) && (
            <div className="p-8 text-center">
              <h3 className="text-lg font-medium text-slate-900 mb-2">No Standings Available</h3>
              <p className="text-slate-600 mb-6">
                Create or join a league to start tracking your performance and see standings.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Team Stats Snapshot */}
      <section className="mb-8">
        <h2 className="text-2xl font-bold leading-tight tracking-[-0.015em] text-[#0d141c] mb-4">Team Stats Snapshot</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="flex items-center text-slate-500 mb-1">
              <span className="material-icons text-lg mr-2">scoreboard</span>
              <p className="text-sm font-medium">Total Season Points</p>
            </div>
            <p className="text-[#0c7ff2] text-3xl font-bold">{(totalSeasonPoints || 0).toFixed(1)}</p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="flex items-center text-slate-500 mb-1">
              <span className="material-icons text-lg mr-2">sports_basketball</span>
              <p className="text-sm font-medium">Active Teams</p>
            </div>
            <p className="text-[#0c7ff2] text-3xl font-bold">{Array.isArray(userTeams) ? userTeams.length : 0}</p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="flex items-center text-slate-500 mb-1">
              <span className="material-icons text-lg mr-2">trending_up</span>
              <p className="text-sm font-medium">Moves Used This Week</p>
            </div>
            <p className="text-[#0c7ff2] text-3xl font-bold">{totalMovesUsed}/{Array.isArray(userTeams) ? userTeams.length * 3 : 0}</p>
          </div>
        </div>
      </section>

      {/* Recent League Activity */}
      <section>
        <h2 className="text-2xl font-bold leading-tight tracking-[-0.015em] text-[#0d141c] mb-4">Recent League Activity</h2>
        <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
          <ul className="space-y-6">
            {Array.isArray(recentGames) && recentGames.length > 0 ? (
              recentGames.slice(0, 3).map(game => (
                <li
                  key={game.id}
                  className="flex items-start space-x-4 hover:bg-slate-50 -mx-6 px-6 py-2 rounded-lg cursor-pointer transition-colors"
                  onClick={() => navigate(`/game/${game.id}`)}
                >
                  <div className="flex-shrink-0 pt-1">
                    <span className="material-icons text-xl text-[#0c7ff2]">sports_basketball</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      Game: {game.away_team} vs {game.home_team} ({game.away_score}-{game.home_score})
                    </p>
                    <p className="text-xs text-slate-500">{new Date(game.date).toLocaleDateString()}</p>
                  </div>
                </li>
              ))
            ) : (
              <li className="flex items-start space-x-4">
                <div className="flex-shrink-0 pt-1">
                  <span className="material-icons text-xl text-slate-400">info</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-800">No recent activity available</p>
                  <p className="text-xs text-slate-500">Check back later for updates</p>
                </div>
              </li>
            )}
          </ul>
        </div>
      </section>
    </DashboardLayout>
  );
};

export default DashboardPage;