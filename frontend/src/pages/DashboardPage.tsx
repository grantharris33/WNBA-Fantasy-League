import React, { useEffect, useState, useCallback } from 'react';
import api from '../lib/api';
import type { CurrentScores } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import StandingsTable from '../components/dashboard/StandingsTable';
import MyLeaguesDashboard from '../components/dashboard/MyLeaguesDashboard';

const DashboardPage: React.FC = () => {
  const [currentScoresData, setCurrentScoresData] = useState<CurrentScores | null>(null);
  const [scoresLoading, setScoresLoading] = useState<boolean>(true);
  const [scoresError, setScoresError] = useState<string | null>(null);

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
    fetchCurrentScores();
  }, [fetchCurrentScores]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      <section className="mb-8">
        <MyLeaguesDashboard />
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