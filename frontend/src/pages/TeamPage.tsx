import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import type { UserTeam } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import RosterView from '../components/roster/RosterView';
import FreeAgentsView from '../components/roster/FreeAgentsView';
import SetStartersModal from '../components/roster/SetStartersModal';

const TeamPage: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();

  const [team, setTeam] = useState<UserTeam | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'roster' | 'free-agents'>('roster');
  const [showSetStartersModal, setShowSetStartersModal] = useState(false);

  useEffect(() => {
    if (teamId) {
      fetchTeamData();
    }
  }, [teamId]);

  const fetchTeamData = async () => {
    if (!teamId) return;

    setLoading(true);
    setError(null);

    try {
      const teamData = await api.teams.getById(parseInt(teamId, 10));
      setTeam(teamData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load team data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddPlayer = async (playerId: number, setAsStarter: boolean = false) => {
    if (!team) return;

    try {
      const updatedTeam = await api.teams.addPlayer(team.id, {
        player_id: playerId,
        set_as_starter: setAsStarter,
      });
      setTeam(updatedTeam);
      toast.success('Player added successfully');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add player');
    }
  };

  const handleDropPlayer = async (playerId: number) => {
    if (!team) return;

    try {
      const updatedTeam = await api.teams.dropPlayer(team.id, {
        player_id: playerId,
      });
      setTeam(updatedTeam);
      toast.success('Player dropped successfully');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to drop player');
    }
  };

  const handleSetStarters = async (starterPlayerIds: number[]) => {
    if (!team) return;

    try {
      const updatedTeam = await api.teams.setStarters(team.id, {
        starter_player_ids: starterPlayerIds,
      });
      setTeam(updatedTeam);
      setShowSetStartersModal(false);
      toast.success('Starting lineup updated successfully');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update starting lineup');
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!team) return <ErrorMessage message="Team not found" />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{team.name}</h1>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            Moves remaining this week: {3 - team.moves_this_week}
          </span>
          <button
            onClick={() => setShowSetStartersModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Set Starters
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Team Info */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Season Points</h3>
            <p className="text-2xl font-bold text-gray-900">{team.season_points}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Roster Size</h3>
            <p className="text-2xl font-bold text-gray-900">{(team.roster_slots?.length || team.roster?.length || 0)}/10</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Weekly Moves</h3>
            <p className="text-2xl font-bold text-gray-900">{team.moves_this_week}/3</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('roster')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'roster'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            My Roster
          </button>
          <button
            onClick={() => setActiveTab('free-agents')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'free-agents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Free Agents
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'roster' && (
        <RosterView
          team={team}
          onDropPlayer={handleDropPlayer}
          onSetStarters={() => setShowSetStartersModal(true)}
        />
      )}

      {activeTab === 'free-agents' && (
        <FreeAgentsView
          leagueId={team.league_id!}
          onAddPlayer={handleAddPlayer}
          movesRemaining={3 - team.moves_this_week}
        />
      )}

      {/* Set Starters Modal */}
      {showSetStartersModal && (
        <SetStartersModal
          team={team}
          onSetStarters={handleSetStarters}
          onClose={() => setShowSetStartersModal(false)}
        />
      )}
    </div>
  );
};

export default TeamPage;