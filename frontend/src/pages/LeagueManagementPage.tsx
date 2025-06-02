import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import type { LeagueOut, UserTeam, LeagueUpdate } from '../types';
import type { DraftState } from '../types/draft';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Breadcrumb from '../components/common/Breadcrumb';

const LeagueManagementPage: React.FC = () => {
  const { leagueId } = useParams<{ leagueId: string }>();
  const navigate = useNavigate();

  const [league, setLeague] = useState<LeagueOut | null>(null);
  const [teams, setTeams] = useState<UserTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<LeagueUpdate>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [draftState, setDraftState] = useState<DraftState | null>(null);
  const [isStartingDraft, setIsStartingDraft] = useState(false);
  const [isPausingDraft, setIsPausingDraft] = useState(false);
  const [isResumingDraft, setIsResumingDraft] = useState(false);

  const breadcrumbItems = [
    { label: 'Dashboard', href: '/' },
    { label: league?.name || 'League Management', current: true },
  ];

  useEffect(() => {
    if (leagueId) {
      fetchLeagueData();
    }
  }, [leagueId]);

  const fetchLeagueData = async () => {
    if (!leagueId) return;

    setLoading(true);
    setError(null);

    try {
      const [leagueData, teamsData] = await Promise.all([
        api.leagues.getById(parseInt(leagueId, 10)),
        api.leagues.getTeams(parseInt(leagueId, 10)),
      ]);

      setLeague(leagueData);
      setTeams(teamsData);
      setEditForm({
        name: leagueData.name,
        max_teams: leagueData.max_teams,
        draft_date: leagueData.draft_date || undefined,
        settings: leagueData.settings,
      });

      // Try to fetch draft state if exists
      try {
        const draftData = await api.leagues.getDraftState(parseInt(leagueId, 10));
        setDraftState(draftData);
      } catch {
        // Draft doesn't exist yet, that's fine
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load league data');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyInviteCode = async () => {
    if (league?.invite_code) {
      try {
        await navigator.clipboard.writeText(league.invite_code);
        toast.success('Invite code copied to clipboard!');
      } catch {
        toast.error('Failed to copy invite code');
      }
    }
  };

  const handleGenerateNewInviteCode = async () => {
    if (!league) return;

    try {
      const response = await api.leagues.generateInviteCode(league.id);
      setLeague(prev => prev ? { ...prev, invite_code: response.invite_code } : null);
      toast.success('New invite code generated!');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to generate new invite code');
    }
  };

  const handleUpdateLeague = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!league) return;

    try {
      const updatedLeague = await api.leagues.update(league.id, editForm);
      setLeague(updatedLeague);
      setIsEditing(false);
      toast.success('League updated successfully!');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update league');
    }
  };

  const handleKickTeam = async (teamId: number, teamName: string) => {
    if (!league) return;

    if (!confirm(`Are you sure you want to remove "${teamName}" from the league?`)) {
      return;
    }

    try {
      await api.leagues.leaveTeam(league.id, teamId);
      setTeams(prev => prev.filter(team => team.id !== teamId));
      toast.success(`${teamName} has been removed from the league`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to remove team');
    }
  };

  const handleDeleteLeague = async () => {
    if (!league) return;

    try {
      await api.leagues.delete(league.id);
      toast.success('League deleted successfully');
      navigate('/');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to delete league');
    }
  };

  const handleStartDraft = async () => {
    if (!league) return;

    setIsStartingDraft(true);
    try {
      await api.leagues.startDraft(league.id);
      // Fetch the updated draft state
      const draftData = await api.leagues.getDraftState(league.id);
      setDraftState(draftData);
      toast.success('Draft started successfully!');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to start draft');
    } finally {
      setIsStartingDraft(false);
    }
  };

  const handlePauseDraft = async () => {
    if (!league || !draftState) return;

    setIsPausingDraft(true);
    try {
      await api.leagues.pauseDraft(draftState.id);
      // Fetch the updated draft state
      const draftData = await api.leagues.getDraftState(league.id);
      setDraftState(draftData);
      toast.success('Draft paused successfully!');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to pause draft');
    } finally {
      setIsPausingDraft(false);
    }
  };

  const handleResumeDraft = async () => {
    if (!league || !draftState) return;

    setIsResumingDraft(true);
    try {
      await api.leagues.resumeDraft(draftState.id);
      // Fetch the updated draft state
      const draftData = await api.leagues.getDraftState(league.id);
      setDraftState(draftData);
      toast.success('Draft resumed successfully!');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to resume draft');
    } finally {
      setIsResumingDraft(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error} />
        <button
          onClick={() => navigate('/')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!league) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message="League not found" />
        <button
          onClick={() => navigate('/')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

      return (
      <div className="container mx-auto px-4 py-8">
        <Breadcrumb items={breadcrumbItems} />
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">League Management</h1>
          <p className="text-gray-600">Manage your league settings, teams, and configurations</p>
        </div>

      {/* League Info Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-semibold">League Information</h2>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {isEditing ? 'Cancel' : 'Edit'}
          </button>
        </div>

        {isEditing ? (
          <form onSubmit={handleUpdateLeague} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                League Name
              </label>
              <input
                type="text"
                value={editForm.name || ''}
                onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Maximum Teams
              </label>
              <select
                value={editForm.max_teams || 8}
                onChange={(e) => setEditForm(prev => ({ ...prev, max_teams: parseInt(e.target.value, 10) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[4, 6, 8, 10, 12].map(num => (
                  <option key={num} value={num}>{num} teams</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Draft Date
              </label>
              <input
                type="datetime-local"
                value={editForm.draft_date || ''}
                onChange={(e) => setEditForm(prev => ({ ...prev, draft_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Save Changes
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">League Name</p>
              <p className="font-medium">{league.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Teams</p>
              <p className="font-medium">{teams.length}/{league.max_teams}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Draft Date</p>
              <p className="font-medium">
                {league.draft_date
                  ? new Date(league.draft_date).toLocaleString()
                  : 'Not scheduled'
                }
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="font-medium">{league.is_active ? 'Active' : 'Inactive'}</p>
            </div>
          </div>
        )}
      </div>

      {/* Invite Code Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Invite Code</h2>
        <div className="flex items-center space-x-3">
          <code className="flex-1 bg-gray-100 px-3 py-2 rounded text-lg font-mono">
            {league.invite_code}
          </code>
          <button
            onClick={handleCopyInviteCode}
            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Copy
          </button>
          <button
            onClick={handleGenerateNewInviteCode}
            className="px-3 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
          >
            Generate New
          </button>
        </div>
      </div>

      {/* Teams Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Teams ({teams.length}/{league.max_teams})</h2>
        {teams.length > 0 ? (
          <div className="space-y-3">
            {teams.map(team => (
              <div key={team.id} className="flex items-center justify-between p-3 border border-gray-200 rounded">
                <div>
                  <p className="font-medium">{team.name}</p>
                  <p className="text-sm text-gray-600">Owner ID: {team.owner_id}</p>
                </div>
                <button
                  onClick={() => handleKickTeam(team.id, team.name)}
                  className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No teams have joined yet.</p>
        )}
      </div>

      {/* Draft Controls Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Draft Management</h2>
        <div className="space-y-4">
          {!draftState ? (
            <div>
              <p className="text-gray-600 mb-4">
                The draft has not been started yet. Make sure you have at least 2 teams before starting.
              </p>
              <button
                onClick={handleStartDraft}
                disabled={teams.length < 2 || isStartingDraft}
                className={`px-4 py-2 rounded font-medium ${
                  teams.length < 2
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {isStartingDraft ? 'Starting...' : 'Start Draft'}
              </button>
              {teams.length < 2 && (
                <p className="text-sm text-red-600 mt-2">Need at least 2 teams to start the draft</p>
              )}
            </div>
          ) : (
            <div>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="font-medium capitalize">{draftState.status}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Current Round</p>
                  <p className="font-medium">{draftState.current_round}/10</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Picks</p>
                  <p className="font-medium">{draftState.picks.length}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Time Remaining</p>
                  <p className="font-medium">{draftState.seconds_remaining}s</p>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => navigate(`/draft/${league.id}`)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Go to Draft Room
                </button>

                {draftState.status === 'active' && (
                  <button
                    onClick={handlePauseDraft}
                    disabled={isPausingDraft}
                    className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                  >
                    {isPausingDraft ? 'Pausing...' : 'Pause Draft'}
                  </button>
                )}

                {draftState.status === 'paused' && (
                  <button
                    onClick={handleResumeDraft}
                    disabled={isResumingDraft}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    {isResumingDraft ? 'Resuming...' : 'Resume Draft'}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white shadow rounded-lg p-6 border-l-4 border-red-500">
        <h2 className="text-xl font-semibold text-red-700 mb-4">Danger Zone</h2>
        <p className="text-gray-600 mb-4">
          Once you delete a league, there is no going back. Please be certain.
        </p>
        {showDeleteConfirm ? (
          <div className="space-y-3">
            <p className="text-red-700 font-medium">
              Are you sure you want to delete "{league.name}"? This action cannot be undone.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleDeleteLeague}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Yes, Delete League
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Delete League
          </button>
        )}
      </div>
    </div>
  );
};

export default LeagueManagementPage;