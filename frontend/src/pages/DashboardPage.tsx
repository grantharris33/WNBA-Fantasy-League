import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import type { CurrentScores, UserTeam } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import StandingsTable from '../components/dashboard/StandingsTable';
import MyLeaguesDashboard from '../components/dashboard/MyLeaguesDashboard';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentScoresData, setCurrentScoresData] = useState<CurrentScores>([]);
  const [scoresLoading, setScoresLoading] = useState<boolean>(true);
  const [scoresError, setScoresError] = useState<string | null>(null);
  const [activeDrafts, setActiveDrafts] = useState<Array<{ leagueId: number; status: string }>>([]);
  const [userTeams, setUserTeams] = useState<UserTeam[]>([]);

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

  const fetchActiveDrafts = useCallback(async () => {
    try {
      const userLeagues = await api.leagues.getMine();
      const drafts: Array<{ leagueId: number; status: string }> = [];

      for (const { league } of userLeagues) {
        try {
          const draftState = await api.leagues.getDraftState(league.id);
          if (draftState && ['active', 'paused'].includes(draftState.status)) {
            drafts.push({ leagueId: league.id, status: draftState.status });
          }
        } catch {
          // No draft for this league
        }
      }

      setActiveDrafts(drafts);
    } catch (error) {
      console.error('Failed to fetch draft states:', error);
    }
  }, []);

  useEffect(() => {
    fetchCurrentScores();
    fetchActiveDrafts();
    fetchUserTeams();
  }, [fetchCurrentScores, fetchActiveDrafts, fetchUserTeams]);

  const totalSeasonPoints = userTeams.reduce((sum, team) => sum + team.season_points, 0);
  const totalMovesUsed = userTeams.reduce((sum, team) => sum + team.moves_this_week, 0);

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
                <div className="text-2xl md:text-3xl font-bold">{userTeams.length}</div>
                <div className="text-sm md:text-base text-blue-100">Active Teams</div>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/30">
                <div className="text-2xl md:text-3xl font-bold">
                  {totalSeasonPoints.toFixed(1)}
                </div>
                <div className="text-sm md:text-base text-blue-100">Total Season Points</div>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/30">
                <div className="text-2xl md:text-3xl font-bold">
                  {totalMovesUsed}/{userTeams.length * 3}
                </div>
                <div className="text-sm md:text-base text-blue-100">Moves Used This Week</div>
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
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🏀</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">My Teams</h3>
              <p className="text-sm text-gray-600">
                {userTeams.length > 0
                  ? `Manage ${userTeams.length} team${userTeams.length > 1 ? 's' : ''}`
                  : 'No teams yet'
                }
              </p>
            </div>
          </div>
          {userTeams.length > 0 ? (
            userTeams.length === 1 ? (
              <button
                onClick={() => navigate(`/team/${userTeams[0].id}`)}
                className="btn-primary w-full"
              >
                Manage {userTeams[0].name}
              </button>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-gray-500 mb-2">Select a team:</div>
                {userTeams.slice(0, 2).map((team) => (
                  <button
                    key={team.id}
                    onClick={() => navigate(`/team/${team.id}`)}
                    className="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    <div className="font-medium">{team.name}</div>
                    <div className="text-xs text-gray-600">
                      {team.season_points.toFixed(1)} pts • {team.moves_this_week}/3 moves
                    </div>
                  </button>
                ))}
                {userTeams.length > 2 && (
                  <div className="text-xs text-gray-500 text-center">
                    +{userTeams.length - 2} more teams
                  </div>
                )}
              </div>
            )
          ) : (
            <button
              onClick={() => navigate('/join')}
              className="btn-secondary w-full"
            >
              Join a League
            </button>
          )}
        </div>

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
              <p className="text-sm text-gray-600">
                {activeDrafts.length > 0
                  ? `${activeDrafts.length} active draft${activeDrafts.length > 1 ? 's' : ''}`
                  : 'Participate in drafts'
                }
              </p>
            </div>
          </div>
          {activeDrafts.length > 0 ? (
            <button
              className="btn-primary w-full"
              onClick={() => navigate(`/draft/${activeDrafts[0].leagueId}`)}
            >
              Go to Draft Room
            </button>
          ) : (
            <button className="btn-secondary w-full" disabled>
              No Active Drafts
            </button>
          )}
        </div>
      </section>
    </div>
  );
};

export default DashboardPage;