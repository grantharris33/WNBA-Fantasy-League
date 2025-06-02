import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import type { CurrentScores } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import StandingsTable from '../components/dashboard/StandingsTable';
import MyLeaguesDashboard from '../components/dashboard/MyLeaguesDashboard';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentScoresData, setCurrentScoresData] = useState<CurrentScores>([]);
  const [scoresLoading, setScoresLoading] = useState<boolean>(true);
  const [scoresError, setScoresError] = useState<string | null>(null);

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

  useEffect(() => {
    fetchCurrentScores();
  }, [fetchCurrentScores]);

  return (
    <div className="space-y-8">
      {/* Enhanced Header */}
      <div className="relative overflow-hidden">
        <div className="dashboard-header text-center">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Welcome to Your Dashboard
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 font-light mb-6">
              Manage your leagues and track your fantasy performance
            </p>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/30">
                <div className="text-2xl md:text-3xl font-bold">1</div>
                <div className="text-sm md:text-base text-blue-100">Active Leagues</div>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/30">
                <div className="text-2xl md:text-3xl font-bold">
                  {currentScoresData.length > 0 ? currentScoresData.find(team => team.team_name.includes('Touch'))?.season_points || '0' : '0'}
                </div>
                <div className="text-sm md:text-base text-blue-100">Season Points</div>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/30">
                <div className="text-2xl md:text-3xl font-bold">
                  {currentScoresData.length > 0 ? currentScoresData.findIndex(team => team.team_name.includes('Touch')) + 1 || 'N/A' : 'N/A'}
                </div>
                <div className="text-sm md:text-base text-blue-100">Current Rank</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* My Leagues Section */}
      <section>
        <MyLeaguesDashboard />
      </section>

      {/* Current Standings Section */}
      <section>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <span className="text-3xl">🏆</span>
            Current Standings
          </h2>
          <p className="text-gray-600">Latest rankings and performance metrics</p>
        </div>

        {scoresLoading && (
          <div className="card p-8">
            <LoadingSpinner message="Loading current standings..." />
          </div>
        )}

        {scoresError && (
          <div className="card p-6">
            <ErrorMessage message={scoresError} />
          </div>
        )}

        {!scoresLoading && !scoresError && currentScoresData && currentScoresData.length > 0 && (
          <StandingsTable scores={currentScoresData} />
        )}

        {!scoresLoading && !scoresError && (!currentScoresData || currentScoresData.length === 0) && (
          <div className="card p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Standings Available</h3>
            <p className="text-gray-600 mb-6">
              Create or join a league to start tracking your performance and see standings.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button className="btn-primary">Create League</button>
              <button className="btn-secondary">Join League</button>
            </div>
          </div>
        )}
      </section>

      {/* Quick Actions */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">View Scoreboard</h3>
              <p className="text-sm text-gray-600">Track weekly performance</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/scoreboard')}
            className="btn-primary w-full"
          >
            Go to Scoreboard
          </button>
        </div>

        <div className="card p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">👥</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Join League</h3>
              <p className="text-sm text-gray-600">Enter with invite code</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/join')}
            className="btn-secondary w-full"
          >
            Join Now
          </button>
        </div>

        <div className="card p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Draft Center</h3>
              <p className="text-sm text-gray-600">Participate in drafts</p>
            </div>
          </div>
          <button className="btn-secondary w-full" disabled>
            Coming Soon
          </button>
        </div>
      </section>
    </div>
  );
};

export default DashboardPage;