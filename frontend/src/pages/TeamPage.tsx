import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  ChartBarIcon,
  UsersIcon,
  UserPlusIcon,
  ArrowLeftIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
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

    // Check if user has moves remaining
    if (team.moves_this_week >= 3) {
      toast.error('No moves remaining this week. You can make up to 3 moves per week.');
      return;
    }

    try {
      const updatedTeam = await api.teams.addPlayer(team.id, {
        player_id: playerId,
        set_as_starter: setAsStarter,
      });

      // Check if player was auto-set as starter
      const currentStarters = team.roster_slots?.filter(slot => slot.is_starter).length || 0;
      const newStarters = updatedTeam.roster_slots?.filter(slot => slot.is_starter).length || 0;

      setTeam(updatedTeam);

      if (setAsStarter) {
        toast.success('Player added as starter!');
      } else if (newStarters > currentStarters) {
        toast.success('Player added to roster and automatically set as starter!', {
          autoClose: 5000,
        });
      } else {
        toast.success('Player added to roster');
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add player');
    }
  };

  const handleDropPlayer = async (playerId: number) => {
    if (!team) return;

    // Check if user has moves remaining
    if (team.moves_this_week >= 3) {
      toast.error('No moves remaining this week. You can make up to 3 moves per week.');
      return;
    }

    try {
      const updatedTeam = await api.teams.dropPlayer(team.id, {
        player_id: playerId,
      });
      setTeam(updatedTeam);
      toast.success('Player dropped from roster');
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

  const movesRemaining = 3 - team.moves_this_week;
  const rosterSize = team.roster_slots?.length || team.roster?.length || 0;
  const maxRosterSize = 10;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mr-4"
            >
              <ArrowLeftIcon className="h-5 w-5 mr-1" />
              Back to Dashboard
            </button>
          </div>

          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{team.name}</h1>
              <p className="text-gray-600">Manage your roster and set your starting lineup</p>
            </div>

            <div className="mt-4 md:mt-0 flex items-center space-x-4">
              <button
                onClick={() => setShowSetStartersModal(true)}
                className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
              >
                <UsersIcon className="h-5 w-5 mr-2" />
                Set Starters
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500">Season Points</h3>
                <p className="text-2xl font-bold text-gray-900">{team.season_points.toFixed(1)}</p>
              </div>
              <ChartBarIcon className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500">Roster Size</h3>
                <p className="text-2xl font-bold text-gray-900">{rosterSize}/{maxRosterSize}</p>
              </div>
              <UsersIcon className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500">Moves Remaining</h3>
                <p className={`text-2xl font-bold ${movesRemaining > 0 ? 'text-gray-900' : 'text-red-500'}`}>
                  {movesRemaining}/3
                </p>
              </div>
              <UserPlusIcon className={`h-8 w-8 ${movesRemaining > 0 ? 'text-orange-500' : 'text-gray-400'}`} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500">Open Spots</h3>
                <p className="text-2xl font-bold text-gray-900">{maxRosterSize - rosterSize}</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                <span className="text-gray-600 text-sm font-medium">{maxRosterSize - rosterSize}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Move Limit Warning */}
        {movesRemaining <= 0 && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  No moves remaining this week
                </h3>
                <div className="mt-1 text-sm text-red-700">
                  <p>You've used all 3 moves for this week. You can add or drop players again next week.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('roster')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'roster'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <UsersIcon className="h-5 w-5 mr-2" />
                My Roster
              </div>
            </button>
            <button
              onClick={() => setActiveTab('free-agents')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'free-agents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <UserPlusIcon className="h-5 w-5 mr-2" />
                Free Agents
              </div>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'roster' && (
          <RosterView
            team={team}
            onDropPlayer={handleDropPlayer}
            onSetStarters={() => setShowSetStartersModal(true)}
            movesRemaining={movesRemaining}
          />
        )}

        {activeTab === 'free-agents' && (
          <FreeAgentsView
            leagueId={team.league_id!}
            onAddPlayer={handleAddPlayer}
            movesRemaining={movesRemaining}
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
    </div>
  );
};

export default TeamPage;