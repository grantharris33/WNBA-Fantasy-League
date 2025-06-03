import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { UsersIcon, CogIcon, TrophyIcon } from '@heroicons/react/24/outline';
import api from '../lib/api';
import type { UserTeam, LeagueOut } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

interface TeamWithLeague extends UserTeam {
  league?: LeagueOut;
}

const MyTeamsPage: React.FC = () => {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<TeamWithLeague[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMyTeams = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const userTeams = await api.users.getMyTeams();

      // Fetch league details for each team
      const teamsWithLeagues = await Promise.all(
        userTeams.map(async (team) => {
          try {
            if (team.league_id) {
              const league = await api.leagues.getById(team.league_id);
              return { ...team, league };
            }
            return team;
          } catch (err) {
            console.error(`Failed to fetch league ${team.league_id}:`, err);
            return team;
          }
        })
      );

      setTeams(teamsWithLeagues as TeamWithLeague[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch teams');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMyTeams();
  }, [fetchMyTeams]);



  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner message="Loading your teams..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <ErrorMessage message={error} />
        <button
          onClick={() => navigate('/')}
          className="mt-4 btn-secondary"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
        <div>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:text-blue-800 text-sm mb-2 flex items-center gap-1"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900">My Teams</h1>
          <p className="text-gray-600 mt-2">
            Manage all your fantasy teams across different leagues
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/join')}
            className="btn-secondary"
          >
            Join League
          </button>
          <button
            onClick={() => navigate('/')}
            className="btn-primary"
          >
            Create League
          </button>
        </div>
      </div>

      {/* Teams Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-blue-600">{teams.length}</div>
          <div className="text-sm text-gray-600">Total Teams</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-green-600">
            {teams.reduce((sum, team) => sum + team.season_points, 0).toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Total Points</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-purple-600">
            {teams.reduce((sum, team) => sum + team.moves_this_week, 0)}
          </div>
          <div className="text-sm text-gray-600">Moves Used</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-orange-600">
            {teams.filter(team => team.season_points > 0).length}
          </div>
          <div className="text-sm text-gray-600">Active Teams</div>
        </div>
      </div>

      {/* Teams List */}
      {teams.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <div key={team.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
                  <div className="flex items-center gap-2 mt-2">
                    {team.league && (
                      <span className="badge bg-blue-100 text-blue-800">
                        {team.league.name}
                      </span>
                    )}
                    {team.season_points > 0 && (
                      <span className="badge badge-success">
                        Active
                      </span>
                    )}
                  </div>
                </div>
                {team.season_points > 50 && (
                  <TrophyIcon className="h-6 w-6 text-yellow-500" />
                )}
              </div>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Season Points:</span>
                  <span className="font-medium text-gray-900">{team.season_points.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Moves This Week:</span>
                  <span className="font-medium text-gray-900">{team.moves_this_week}/3</span>
                </div>
                {team.league && (
                  <>
                    <div className="flex justify-between">
                      <span>League:</span>
                      <span className="font-medium text-gray-900">
                        {team.league.max_teams} teams
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className={`font-medium ${team.league.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                        {team.league.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </>
                )}
              </div>

              {/* Quick Stats Bars */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Weekly Activity</span>
                  <span>{Math.round((team.moves_this_week / 3) * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min((team.moves_this_week / 3) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Performance Indicator */}
              {team.season_points > 0 && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Performance</span>
                    <div className="flex items-center gap-1">
                      {team.season_points >= 100 ? (
                        <span className="text-green-600 text-sm font-medium">Excellent</span>
                      ) : team.season_points >= 50 ? (
                        <span className="text-blue-600 text-sm font-medium">Good</span>
                      ) : (
                        <span className="text-gray-600 text-sm font-medium">Building</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => navigate(`/team/${team.id}`)}
                  className="flex-1 btn-primary text-sm flex items-center justify-center gap-1"
                >
                  <UsersIcon className="h-4 w-4" />
                  Manage
                </button>

                {team.league && (
                  <button
                    onClick={() => navigate(`/league/${team.league!.id}`)}
                    className="flex-1 btn-secondary text-sm flex items-center justify-center gap-1"
                  >
                    <CogIcon className="h-4 w-4" />
                    League
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <UsersIcon className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No teams yet
            </h3>
            <p className="text-gray-600 mb-6">
              Join a league or create your own to start building your fantasy team.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => navigate('/')}
                className="btn-primary"
              >
                Create League
              </button>
              <button
                onClick={() => navigate('/join')}
                className="btn-secondary"
              >
                Join League
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyTeamsPage;