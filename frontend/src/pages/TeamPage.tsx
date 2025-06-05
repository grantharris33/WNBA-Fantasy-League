import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  ChartBarIcon,
  UsersIcon,
  UserPlusIcon,
  ExclamationTriangleIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import api from '../lib/api';
import type { UserTeam, TeamScoreData, BonusDetail } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import RosterView from '../components/roster/RosterView';
import FreeAgentsView from '../components/roster/FreeAgentsView';
import SetStartersModal from '../components/roster/SetStartersModal';
import BonusBreakdown from '../components/dashboard/BonusBreakdown';
import TeamManagementLayout from '../components/layout/TeamManagementLayout';

const TeamPage: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();

  const [team, setTeam] = useState<UserTeam | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'roster' | 'free-agents' | 'bonuses'>('roster');
  const [showSetStartersModal, setShowSetStartersModal] = useState(false);
  const [teamBonuses, setTeamBonuses] = useState<BonusDetail[]>([]);
  const [bonusesLoading, setBonusesLoading] = useState(false);

  useEffect(() => {
    if (teamId) {
      fetchTeamData();
      fetchTeamBonuses();
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

  const fetchTeamBonuses = async () => {
    if (!teamId) return;

    setBonusesLoading(true);

    try {
      // Get current scores to find bonuses for this team
      const scores: TeamScoreData[] = await api.scores.getCurrent();
      const teamScore = scores.find(score => score.team_id === parseInt(teamId, 10));

      if (teamScore && teamScore.bonuses) {
        setTeamBonuses(teamScore.bonuses);
      } else {
        setTeamBonuses([]);
      }
    } catch (err) {
      console.error('Failed to load team bonuses:', err);
      setTeamBonuses([]);
    } finally {
      setBonusesLoading(false);
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

  const handlePlayerClick = (playerId: number) => {
    navigate(`/player/${playerId}`);
  };

  if (loading) return (
    <TeamManagementLayout teamName="Loading...">
      <LoadingSpinner />
    </TeamManagementLayout>
  );

  if (error) return (
    <TeamManagementLayout teamName="Error">
      <ErrorMessage message={error} />
    </TeamManagementLayout>
  );

  if (!team) return (
    <TeamManagementLayout teamName="Not Found">
      <ErrorMessage message="Team not found" />
    </TeamManagementLayout>
  );

  const movesRemaining = 3 - team.moves_this_week;
  const rosterSize = team.roster_slots?.length || team.roster?.length || 0;
  const maxRosterSize = 10;

  return (
    <TeamManagementLayout teamName={team.name}>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-slate-500">Season Points</h3>
              <p className="text-2xl font-bold text-slate-900">{team.season_points.toFixed(1)}</p>
            </div>
            <ChartBarIcon className="h-8 w-8 text-[#0c7ff2]" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-slate-500">Roster Size</h3>
              <p className="text-2xl font-bold text-slate-900">{rosterSize}/{maxRosterSize}</p>
            </div>
            <UsersIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-slate-500">Starter Moves Remaining</h3>
              <p className={`text-2xl font-bold ${movesRemaining > 0 ? 'text-slate-900' : 'text-red-500'}`}>
                {movesRemaining}/3
              </p>
            </div>
            <UserPlusIcon className={`h-8 w-8 ${movesRemaining > 0 ? 'text-orange-500' : 'text-slate-400'}`} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-slate-500">Open Spots</h3>
              <p className="text-2xl font-bold text-slate-900">{maxRosterSize - rosterSize}</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
              <span className="text-slate-600 text-sm font-medium">{maxRosterSize - rosterSize}</span>
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
                No starter moves remaining this week
              </h3>
              <div className="mt-1 text-sm text-red-700">
                <p>You've used all 3 starter moves for this week. You can still add/drop bench players, but can't set new starters until next week.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('roster')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'roster'
                ? 'border-[#0c7ff2] text-[#0c7ff2]'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
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
                ? 'border-[#0c7ff2] text-[#0c7ff2]'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center">
              <UserPlusIcon className="h-5 w-5 mr-2" />
              Free Agents
            </div>
          </button>
          <button
            onClick={() => setActiveTab('bonuses')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'bonuses'
                ? 'border-[#0c7ff2] text-[#0c7ff2]'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center">
              <StarIcon className="h-5 w-5 mr-2" />
              Weekly Bonuses
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
          teamBonuses={teamBonuses}
          onPlayerClick={handlePlayerClick}
        />
      )}

      {activeTab === 'free-agents' && (
        <FreeAgentsView
          leagueId={team.league_id!}
          onAddPlayer={handleAddPlayer}
          movesRemaining={movesRemaining}
        />
      )}

      {activeTab === 'bonuses' && (
        <div className="space-y-6">
          {bonusesLoading ? (
            <LoadingSpinner />
          ) : (
            <BonusBreakdown
              bonuses={teamBonuses}
              teamName={team.name}
              variant="detailed"
              showTitle={true}
            />
          )}
        </div>
      )}

      {/* Set Starters Modal */}
      {showSetStartersModal && team && (
        <SetStartersModal
          team={team}
          onClose={() => setShowSetStartersModal(false)}
          onSetStarters={handleSetStarters}
        />
      )}
    </TeamManagementLayout>
  );
};

export default TeamPage;