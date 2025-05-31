import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../../lib/api';
import type { LeagueWithRole, LeagueOut } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import CreateLeagueModal from '../common/CreateLeagueModal';

const MyLeaguesDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState<LeagueWithRole[]>([]);
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
      const userLeagues = await api.leagues.getMine();
      setLeagues(userLeagues);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch leagues');
    } finally {
      setLoading(false);
    }
  };

  const handleLeagueCreated = (league: LeagueOut) => {
    // Add the new league to the list
    const newLeagueWithRole: LeagueWithRole = {
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
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">My Leagues</h2>
        <div className="space-x-3">
          <button
            onClick={() => navigate('/join')}
            className="px-4 py-2 border border-blue-600 text-blue-600 rounded hover:bg-blue-50"
          >
            Join League
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Create League
          </button>
        </div>
      </div>

      {leagues.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {leagues.map(({ league, role }) => (
            <div key={league.id} className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{league.name}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        role === 'commissioner'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {role === 'commissioner' ? 'Commissioner' : 'Member'}
                    </span>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        league.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {league.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Teams:</span>
                  <span className="font-medium">0/{league.max_teams}</span>
                </div>
                <div className="flex justify-between">
                  <span>Draft Date:</span>
                  <span className="font-medium">
                    {league.draft_date
                      ? new Date(league.draft_date).toLocaleDateString()
                      : 'Not scheduled'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="font-medium">
                    {league.created_at
                      ? new Date(league.created_at).toLocaleDateString()
                      : 'Unknown'
                    }
                  </span>
                </div>
              </div>

              {/* Invite Code for Commissioners */}
              {role === 'commissioner' && league.invite_code && (
                <div className="mb-4 p-3 bg-gray-50 rounded">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Invite Code
                  </label>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 text-sm font-mono bg-white px-2 py-1 rounded border">
                      {league.invite_code}
                    </code>
                    <button
                      onClick={() => handleCopyInviteCode(league.invite_code!)}
                      className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex space-x-2">
                <button
                  onClick={() => navigate(`/league/${league.id}`)}
                  className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  View
                </button>

                {role === 'commissioner' ? (
                  <button
                    onClick={() => navigate(`/league/${league.id}/manage`)}
                    className="flex-1 px-3 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700"
                  >
                    Manage
                  </button>
                ) : (
                  <button
                    onClick={() => handleLeaveLeague(league.id, league.name)}
                    className="flex-1 px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700"
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
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No leagues yet
            </h3>
            <p className="text-gray-600 mb-6">
              Get started by creating your own league or joining an existing one with an invite code.
            </p>
            <div className="space-x-3">
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Create League
              </button>
              <button
                onClick={() => navigate('/join')}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
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