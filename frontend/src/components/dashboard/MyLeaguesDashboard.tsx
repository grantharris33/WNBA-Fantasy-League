import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { UsersIcon, CogIcon } from '@heroicons/react/24/outline';
import api from '../../lib/api';
import type { LeagueWithRole, LeagueOut, UserTeam } from '../../types';
import type { DraftState } from '../../types/draft';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import CreateLeagueModal from '../common/CreateLeagueModal';
import WelcomeCard from './WelcomeCard';

interface LeagueWithDraft extends LeagueWithRole {
  draftState?: DraftState | null;
  teamCount?: number;
  userTeam?: UserTeam | null;
}

const MyLeaguesDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState<LeagueWithDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchMyLeagues();
  }, []);

  const fetchMyLeagues = async () => {
    setLoading(true);
    setError(null);
    try {
      const [userLeagues, userTeams] = await Promise.all([
        api.leagues.getMine(),
        api.users.getMyTeams()
      ]);

      // Fetch draft state and team count for each league
      const leaguesWithDraft = await Promise.all(
        userLeagues.map(async (leagueWithRole) => {
          try {
            const [draftState, teams] = await Promise.all([
              api.leagues.getDraftState(leagueWithRole.league.id).catch(() => null),
              api.leagues.getTeams(leagueWithRole.league.id).catch(() => [])
            ]);

            // Find user's team in this league
            const userTeam = userTeams.find(team => team.league_id === leagueWithRole.league.id);

            return {
              ...leagueWithRole,
              draftState,
              teamCount: teams.length,
              userTeam: userTeam || null
            };
          } catch {
            // No draft exists for this league, but still get team count and user team
            try {
              const teams = await api.leagues.getTeams(leagueWithRole.league.id);
              const userTeam = userTeams.find(team => team.league_id === leagueWithRole.league.id);
              return {
                ...leagueWithRole,
                draftState: null,
                teamCount: teams.length,
                userTeam: userTeam || null
              };
            } catch {
              const userTeam = userTeams.find(team => team.league_id === leagueWithRole.league.id);
              return {
                ...leagueWithRole,
                draftState: null,
                teamCount: 0,
                userTeam: userTeam || null
              };
            }
          }
        })
      );

      setLeagues(leaguesWithDraft);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch leagues');
    } finally {
      setLoading(false);
    }
  };

  const handleLeagueCreated = (league: LeagueOut) => {
    // Add the new league to the list
    const newLeagueWithRole: LeagueWithDraft = {
      league,
      role: 'commissioner',
    };
    setLeagues(prev => [newLeagueWithRole, ...prev]);
    setShowCreateModal(false);
  };

  const handleLeaveLeague = async (leagueId: number, leagueName: string) => {
    if (!confirm(`Are you sure you want to leave "${leagueName}"?`)) {
      return;
    }

    try {
      // Find the user's team in this league
      const userTeams = await api.users.getMyTeams();
      const userTeam = userTeams.find(team => team.league_id === leagueId);

      if (userTeam) {
        await api.leagues.leaveTeam(leagueId, userTeam.id);
        setLeagues(prev => prev.filter(item => item.league.id !== leagueId));
        toast.success(`Left "${leagueName}" successfully`);
      } else {
        toast.error('Could not find your team in this league');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to leave league');
    }
  };

  const handleCopyInviteCode = async (inviteCode: string) => {
    try {
      await navigator.clipboard.writeText(inviteCode);
      toast.success('Invite code copied to clipboard!');
    } catch {
      toast.error('Failed to copy invite code');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div>
      <WelcomeCard hasTeams={leagues.length > 0} />
      
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
        <h2 className="text-2xl font-bold text-gray-900">My Leagues</h2>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/join')}
            className="btn-secondary"
          >
            Join League
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            Create League
          </button>
        </div>
      </div>

      {leagues.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {leagues.map(({ league, role, draftState, teamCount, userTeam }) => (
            <div key={league.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{league.name}</h3>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`badge ${
                        role === 'commissioner'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {role === 'commissioner' ? 'Commissioner' : 'Member'}
                    </span>
                    <span
                      className={`badge ${
                        league.is_active
                          ? 'badge-success'
                          : 'badge-secondary'
                      }`}
                    >
                      {league.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {draftState && (
                      <span
                        className={`badge ${
                          draftState.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : draftState.status === 'paused'
                            ? 'bg-yellow-100 text-yellow-800'
                            : draftState.status === 'completed'
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        Draft: {draftState.status}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* User Team Info */}
              {userTeam && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-blue-900">{userTeam.name}</h4>
                      <div className="flex items-center gap-4 text-xs text-blue-700 mt-1">
                        <span>{userTeam.season_points.toFixed(1)} pts</span>
                        <span>{userTeam.moves_this_week}/3 moves</span>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/team/${userTeam.id}`)}
                      className="flex items-center px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
                    >
                      <UsersIcon className="h-4 w-4 mr-1" />
                      Manage Team
                    </button>
                  </div>
                </div>
              )}

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Teams:</span>
                  <span className="font-medium text-gray-900">{teamCount ?? 0}/{league.max_teams}</span>
                </div>
                <div className="flex justify-between">
                  <span>Draft Date:</span>
                  <span className="font-medium text-gray-900">
                    {league.draft_date
                      ? new Date(league.draft_date).toLocaleDateString()
                      : 'Not scheduled'
                    }
                  </span>
                </div>
                {draftState && (
                  <div className="flex justify-between">
                    <span>Draft Round:</span>
                    <span className="font-medium text-gray-900">
                      {draftState.status === 'completed' ? 'Complete' : `${draftState.current_round}/10`}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="font-medium text-gray-900">
                    {league.created_at
                      ? new Date(league.created_at).toLocaleDateString()
                      : 'Unknown'
                    }
                  </span>
                </div>
              </div>

              {/* Invite Code for Commissioners */}
              {role === 'commissioner' && league.invite_code && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
                  <label className="block text-xs font-medium text-gray-700 mb-2">
                    Invite Code
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 text-sm font-mono bg-white px-3 py-2 rounded border text-gray-900">
                      {league.invite_code}
                    </code>
                    <button
                      onClick={() => handleCopyInviteCode(league.invite_code!)}
                      className="px-3 py-2 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => navigate(`/league/${league.id}`)}
                  className="flex-1 btn-primary text-sm"
                >
                  View
                </button>

                {draftState && ['active', 'paused'].includes(draftState.status) && (
                  <button
                    onClick={() => navigate(`/draft/${league.id}`)}
                    className="flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    Draft Room
                  </button>
                )}

                {role === 'commissioner' ? (
                  <button
                    onClick={() => navigate(`/league/${league.id}/manage`)}
                    className="flex-1 px-3 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors flex items-center justify-center"
                  >
                    <CogIcon className="h-4 w-4 mr-1" />
                    Manage
                  </button>
                ) : (
                  <button
                    onClick={() => handleLeaveLeague(league.id, league.name)}
                    className="flex-1 btn-destructive text-sm"
                  >
                    Leave
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
              <span className="text-2xl">🏀</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No leagues yet
            </h3>
            <p className="text-gray-600 mb-6">
              Get started by creating your own league or joining an existing one with an invite code.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => setShowCreateModal(true)}
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

      <CreateLeagueModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onLeagueCreated={handleLeagueCreated}
      />
    </div>
  );
};

export default MyLeaguesDashboard;