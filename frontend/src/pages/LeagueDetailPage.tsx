import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import type { LeagueOut, UserTeam, CurrentScores } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import StandingsTable from '../components/dashboard/StandingsTable';

const LeagueDetailPage: React.FC = () => {
  const { leagueId } = useParams<{ leagueId: string }>();
  const navigate = useNavigate();
  const [league, setLeague] = useState<LeagueOut | null>(null);
  const [teams, setTeams] = useState<UserTeam[]>([]);
  const [scores, setScores] = useState<CurrentScores>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLeagueData = useCallback(async () => {
    if (!leagueId) return;

    setLoading(true);
    setError(null);
    try {
      const [leagueData, teamsData, scoresData] = await Promise.all([
        api.leagues.getById(parseInt(leagueId)),
        api.leagues.getTeams(parseInt(leagueId)),
        api.scores.getCurrent()
      ]);

      setLeague(leagueData);
      setTeams(teamsData);

      // Filter scores to only show teams from this league
      const leagueTeamIds = teamsData.map(team => team.id);
      const filteredScores = scoresData.filter(score =>
        leagueTeamIds.includes(score.team_id)
      );
      setScores(filteredScores);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch league data');
    } finally {
      setLoading(false);
    }
  }, [leagueId]);

  useEffect(() => {
    fetchLeagueData();
  }, [fetchLeagueData]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner message="Loading league details..." />
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

  if (!league) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">League Not Found</h1>
        <p className="text-gray-600 mb-6">The league you're looking for doesn't exist or you don't have access to it.</p>
        <button
          onClick={() => navigate('/')}
          className="btn-primary"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const totalPoints = scores.reduce((sum, score) => sum + score.season_points, 0);
  const averagePoints = scores.length > 0 ? totalPoints / scores.length : 0;
  const topTeam = scores.length > 0 ? scores[0] : null;

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
          <h1 className="text-3xl font-bold text-gray-900">{league.name}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
            <span>{teams.length}/{league.max_teams} Teams</span>
            {league.draft_date && (
              <span>Draft: {new Date(league.draft_date).toLocaleDateString()}</span>
            )}
            <span className={`badge ${league.is_active ? 'badge-success' : 'badge-secondary'}`}>
              {league.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => navigate(`/league/${league.id}/manage`)}
            className="btn-secondary"
          >
            League Settings
          </button>
          <button
            onClick={() => navigate(`/draft/${league.id}`)}
            className="btn-primary"
          >
            Draft Room
          </button>
        </div>
      </div>

      {/* League Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-blue-600">{teams.length}</div>
          <div className="text-sm text-gray-600">Active Teams</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-green-600">
            {averagePoints.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Average Points</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-purple-600">
            {topTeam ? topTeam.season_points.toFixed(1) : '0.0'}
          </div>
          <div className="text-sm text-gray-600">League Leader</div>
          {topTeam && (
            <div className="text-xs text-gray-500 mt-1">{topTeam.team_name}</div>
          )}
        </div>
      </div>

      {/* League Standings */}
      <section>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <span className="text-3xl">🏆</span>
            League Standings
          </h2>
          <p className="text-gray-600">Current rankings for {league.name}</p>
        </div>

        {scores.length > 0 ? (
          <StandingsTable scores={scores} />
        ) : (
          <div className="card p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Standings Available</h3>
            <p className="text-gray-600">
              Teams haven't started accumulating points yet. Check back after some games have been played.
            </p>
          </div>
        )}
      </section>

      {/* Teams List */}
      <section>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Teams</h2>
          <p className="text-gray-600">All teams in {league.name}</p>
        </div>

        {teams.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map(team => {
              const teamScore = scores.find(score => score.team_id === team.id);
              const rank = teamScore ? scores.findIndex(score => score.team_id === team.id) + 1 : null;

              return (
                <div key={team.id} className="card p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{team.name}</h3>
                      <div className="text-sm text-gray-600">
                        Owner ID: {team.owner_id}
                      </div>
                    </div>
                    {rank && (
                      <div className="text-sm bg-gray-100 px-2 py-1 rounded">
                        #{rank}
                      </div>
                    )}
                  </div>

                  {teamScore && (
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Season Points:</span>
                        <span className="font-medium">{teamScore.season_points.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Weekly Delta:</span>
                        <span className="font-medium">{teamScore.weekly_delta.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Moves Used:</span>
                        <span className="font-medium">{team.moves_this_week}/3</span>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => navigate(`/team/${team.id}`)}
                    className="mt-3 w-full btn-secondary text-sm"
                  >
                    View Team
                  </button>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">👥</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Teams Yet</h3>
            <p className="text-gray-600">
              This league doesn't have any teams yet. Invite players to join!
            </p>
            {league.invite_code && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border">
                <label className="block text-xs font-medium text-blue-700 mb-2">
                  Share this invite code:
                </label>
                <code className="bg-white px-3 py-2 rounded border text-blue-900 font-mono">
                  {league.invite_code}
                </code>
                <button
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(league.invite_code!);
                      toast.success('Invite code copied!');
                    } catch {
                      toast.error('Failed to copy invite code');
                    }
                  }}
                  className="ml-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                >
                  Copy
                </button>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default LeagueDetailPage;