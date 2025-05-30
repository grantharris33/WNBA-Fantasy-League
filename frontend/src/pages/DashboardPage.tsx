import React, { useEffect, useState, useCallback } from 'react';
import api from '../lib/api';
import type { UserTeam, CurrentScores, DraftState } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import LeagueTeamCard from '../components/dashboard/LeagueTeamCard';
import StandingsTable from '../components/dashboard/StandingsTable';
// Placeholder imports for components to be created
// import LeagueTeamCard from '../components/dashboard/LeagueTeamCard';
// import StandingsTable from '../components/dashboard/StandingsTable';

interface LeagueDraftStatus {
  leagueId: number;
  status: DraftState['status'] | 'loading' | 'error';
  error?: string;
}

const DashboardPage: React.FC = () => {
  const [userTeams, setUserTeams] = useState<UserTeam[]>([]);
  const [userTeamsLoading, setUserTeamsLoading] = useState<boolean>(true);
  const [userTeamsError, setUserTeamsError] = useState<string | null>(null);

  const [currentScoresData, setCurrentScoresData] = useState<CurrentScores | null>(null);
  const [scoresLoading, setScoresLoading] = useState<boolean>(true);
  const [scoresError, setScoresError] = useState<string | null>(null);

  const [draftStatuses, setDraftStatuses] = useState<Record<number, LeagueDraftStatus>>({});

  const fetchUserTeams = useCallback(async () => {
    setUserTeamsLoading(true);
    setUserTeamsError(null);
    try {
      const teams = await api.users.getMyTeams() as UserTeam[];
      setUserTeams(teams);
    } catch (error) {
      setUserTeamsError(error instanceof Error ? error.message : 'Failed to fetch user teams.');
      setUserTeams([]);
    }
    setUserTeamsLoading(false);
  }, []);

  const fetchCurrentScores = useCallback(async () => {
    setScoresLoading(true);
    setScoresError(null);
    try {
      const scores = await api.scores.getCurrent() as CurrentScores;
      setCurrentScoresData(scores);
    } catch (error) {
      setScoresError(error instanceof Error ? error.message : 'Failed to fetch current scores.');
    }
    setScoresLoading(false);
  }, []);

  useEffect(() => {
    fetchUserTeams();
    fetchCurrentScores();
  }, [fetchUserTeams, fetchCurrentScores]);

  useEffect(() => {
    if (userTeams.length > 0) {
      userTeams.forEach(team => {
        if (!draftStatuses[team.league_id] || draftStatuses[team.league_id].status === 'error') {
          setDraftStatuses(prev => ({ ...prev, [team.league_id]: { leagueId: team.league_id, status: 'loading' } }));
          api.leagues.getDraftState(team.league_id)
            .then(data => {
              setDraftStatuses(prev => ({ ...prev, [team.league_id]: { leagueId: team.league_id, status: data.status } }));
            })
            .catch(err => {
              setDraftStatuses(prev => ({
                ...prev,
                [team.league_id]: {
                  leagueId: team.league_id,
                  status: 'error',
                  error: err instanceof Error ? err.message : 'Failed to load draft status'
                }
              }));
            });
        }
      });
    }
  }, [userTeams, draftStatuses]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">My Leagues & Teams</h2>
        {userTeamsLoading && <LoadingSpinner />}
        {userTeamsError && <ErrorMessage message={userTeamsError} />}
        {!userTeamsLoading && !userTeamsError && (
          userTeams.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {userTeams.map(team => (
                <LeagueTeamCard
                  key={team.id}
                  team={team}
                  draftStatusInfo={draftStatuses[team.league_id]}
                />
              ))}
            </div>
          ) : (
            <p className="text-gray-600">You haven't joined any leagues yet. Why not create or join one?</p>
          )
        )}
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-4">Current Standings</h2>
        {scoresLoading && <LoadingSpinner />}
        {scoresError && <ErrorMessage message={scoresError} />}
        {!scoresLoading && !scoresError && currentScoresData && currentScoresData.scores && (
          <StandingsTable scores={currentScoresData.scores} />
        )}
        {!scoresLoading && !scoresError &&
         (!currentScoresData || !currentScoresData.scores || currentScoresData.scores.length === 0) && (
            <p className="text-gray-600">No scores available at the moment, or standings are empty.</p>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;