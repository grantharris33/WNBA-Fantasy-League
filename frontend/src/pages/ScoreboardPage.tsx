import React, { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import type {
  CurrentScores,
  WeeklyScores,
  TopPerformer,
  ScoreTrend,
  LeagueChampion
} from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Breadcrumb from '../components/common/Breadcrumb';
import StandingsTable from '../components/dashboard/StandingsTable';
import DashboardLayout from '../components/layout/DashboardLayout';
// import HistoricalScoresView from '../components/dashboard/HistoricalScoresView';
// import TopPerformersView from '../components/dashboard/TopPerformersView';
// import ScoreTrendsChart from '../components/dashboard/ScoreTrendsChart';
// import LeagueChampionView from '../components/dashboard/LeagueChampionView';

const ScoreboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'standings' | 'history' | 'performers' | 'trends' | 'champion'>('standings');

  // Current Standings State
  const [currentScores, setCurrentScores] = useState<CurrentScores>([]);
  const [scoresLoading, setScoresLoading] = useState<boolean>(true);
  const [scoresError, setScoresError] = useState<string | null>(null);

  // Historical Scores State
  const [historicalScores, setHistoricalScores] = useState<WeeklyScores[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Top Performers State
  const [topPerformers, setTopPerformers] = useState<TopPerformer[]>([]);
  const [performersLoading, setPerformersLoading] = useState<boolean>(false);
  const [performersError, setPerformersError] = useState<string | null>(null);

  // Score Trends State
  const [scoreTrends, setScoreTrends] = useState<ScoreTrend[]>([]);
  const [trendsLoading, setTrendsLoading] = useState<boolean>(false);
  const [trendsError, setTrendsError] = useState<string | null>(null);

  // League Champion State
  const [leagueChampion, setLeagueChampion] = useState<LeagueChampion | null>(null);
  const [championLoading, setChampionLoading] = useState<boolean>(false);
  const [championError, setChampionError] = useState<string | null>(null);

  const breadcrumbItems = [
    { label: 'Dashboard', href: '/' },
    { label: 'Scoreboard', current: true },
  ];

  // Fetch current standings
  const fetchCurrentScores = useCallback(async () => {
    setScoresLoading(true);
    setScoresError(null);
    try {
      const scores = await api.scores.getCurrent();
      setCurrentScores(scores);
    } catch (error) {
      setScoresError(error instanceof Error ? error.message : 'Failed to fetch current scores.');
    }
    setScoresLoading(false);
  }, []);

  // Fetch historical scores
  const fetchHistoricalScores = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const history = await api.scores.getHistory();
      setHistoricalScores(history);
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : 'Failed to fetch historical scores.');
    }
    setHistoryLoading(false);
  }, []);

  // Fetch top performers
  const fetchTopPerformers = useCallback(async () => {
    setPerformersLoading(true);
    setPerformersError(null);
    try {
      const performers = await api.scores.getTopPerformers();
      setTopPerformers(performers);
    } catch (error) {
      setPerformersError(error instanceof Error ? error.message : 'Failed to fetch top performers.');
    }
    setPerformersLoading(false);
  }, []);

  // Fetch score trends
  const fetchScoreTrends = useCallback(async () => {
    setTrendsLoading(true);
    setTrendsError(null);
    try {
      const trends = await api.scores.getTrends();
      setScoreTrends(trends);
    } catch (error) {
      setTrendsError(error instanceof Error ? error.message : 'Failed to fetch score trends.');
    }
    setTrendsLoading(false);
  }, []);

  // Fetch league champion
  const fetchLeagueChampion = useCallback(async () => {
    setChampionLoading(true);
    setChampionError(null);
    try {
      const champion = await api.scores.getChampion();
      setLeagueChampion(champion);
    } catch (error) {
      setChampionError(error instanceof Error ? error.message : 'Failed to fetch league champion.');
    }
    setChampionLoading(false);
  }, []);

  // Load initial data
  useEffect(() => {
    fetchCurrentScores();
  }, [fetchCurrentScores]);

  // Load data when tab changes
  useEffect(() => {
    switch (activeTab) {
      case 'history':
        if (historicalScores.length === 0) {
          fetchHistoricalScores();
        }
        break;
      case 'performers':
        if (topPerformers.length === 0) {
          fetchTopPerformers();
        }
        break;
      case 'trends':
        if (scoreTrends.length === 0) {
          fetchScoreTrends();
        }
        break;
      case 'champion':
        if (!leagueChampion) {
          fetchLeagueChampion();
        }
        break;
    }
  }, [activeTab, historicalScores.length, topPerformers.length, scoreTrends.length, leagueChampion, fetchHistoricalScores, fetchTopPerformers, fetchScoreTrends, fetchLeagueChampion]);

  const tabs = [
    { id: 'standings' as const, label: 'Current Standings', icon: '🏆' },
    { id: 'history' as const, label: 'Previous Weeks', icon: '📊' },
    { id: 'performers' as const, label: 'Top Performers', icon: '⭐' },
    { id: 'trends' as const, label: 'Score Trends', icon: '📈' },
    { id: 'champion' as const, label: 'League Champion', icon: '👑' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'standings':
        if (scoresLoading) return <LoadingSpinner />;
        if (scoresError) return <ErrorMessage message={scoresError} />;
        if (!currentScores || currentScores.length === 0) {
          return <p className="text-gray-600">No scores available at the moment.</p>;
        }
        return <StandingsTable scores={currentScores} />;

      case 'history':
        if (historyLoading) return <LoadingSpinner />;
        if (historyError) return <ErrorMessage message={historyError} />;
        return <div className="text-center py-8 text-gray-600">Historical scores view coming soon...</div>;

      case 'performers':
        if (performersLoading) return <LoadingSpinner />;
        if (performersError) return <ErrorMessage message={performersError} />;
        return <div className="text-center py-8 text-gray-600">Top performers view coming soon...</div>;

      case 'trends':
        if (trendsLoading) return <LoadingSpinner />;
        if (trendsError) return <ErrorMessage message={trendsError} />;
        return <div className="text-center py-8 text-gray-600">Score trends chart coming soon...</div>;

      case 'champion':
        if (championLoading) return <LoadingSpinner />;
        if (championError) return <ErrorMessage message={championError} />;
        return <div className="text-center py-8 text-gray-600">League champion view coming soon...</div>;

      default:
        return <div>Unknown tab</div>;
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <Breadcrumb items={breadcrumbItems} />

                 <div className="mb-8">
           <h1 className="text-3xl font-bold text-slate-900 mb-2">League Scoreboard</h1>
           <p className="text-slate-600">Track team standings, performance, and season progress</p>
         </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          {renderTabContent()}
        </div>

        {/* Refresh Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => {
              fetchCurrentScores();
              if (activeTab === 'history') fetchHistoricalScores();
              if (activeTab === 'performers') fetchTopPerformers();
              if (activeTab === 'trends') fetchScoreTrends();
              if (activeTab === 'champion') fetchLeagueChampion();
            }}
                         className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-[#0c7ff2] text-white text-sm font-semibold hover:bg-[#0a68c4] transition-colors shadow-sm"
          >
            Refresh Data
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ScoreboardPage;