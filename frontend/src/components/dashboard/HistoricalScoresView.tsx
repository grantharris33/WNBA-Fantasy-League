import React, { useState } from 'react';
import type { WeeklyScores, PlayerScoreBreakdown } from '../../types';

interface HistoricalScoresViewProps {
  historicalScores: WeeklyScores[];
}

const HistoricalScoresView: React.FC<HistoricalScoresViewProps> = ({ historicalScores }) => {
  const [expandedWeeks, setExpandedWeeks] = useState<Set<number>>(new Set());
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set());

  const toggleWeek = (week: number) => {
    const newExpanded = new Set(expandedWeeks);
    if (newExpanded.has(week)) {
      newExpanded.delete(week);
    } else {
      newExpanded.add(week);
    }
    setExpandedWeeks(newExpanded);
  };

  const toggleTeamBreakdown = (teamId: number, week: number) => {
    const key = `${teamId}-${week}`;
    const newExpanded = new Set(expandedTeams);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedTeams(newExpanded);
  };

  const renderPlayerBreakdown = (breakdown: PlayerScoreBreakdown[]) => {
    if (breakdown.length === 0) {
      return <p className="text-gray-500 text-sm">No player data available</p>;
    }

    return (
      <div className="mt-3 space-y-2">
        <h5 className="text-sm font-medium text-gray-700">Player Performance:</h5>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {breakdown.map((player) => (
            <div key={player.player_id} className="flex justify-between items-center bg-gray-50 px-3 py-2 rounded">
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-800">{player.player_name}</span>
                {player.position && (
                  <span className="ml-2 text-xs text-gray-500">({player.position})</span>
                )}
                {player.is_starter && (
                  <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-1 rounded">Starter</span>
                )}
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-800">{player.points_scored} pts</div>
                <div className="text-xs text-gray-500">{player.games_played} games</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (historicalScores.length === 0) {
    return <p className="text-gray-600">No historical scores available.</p>;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Historical Weekly Scores</h3>

      {historicalScores
        .sort((a, b) => b.week - a.week) // Most recent weeks first
        .map((weekData) => (
        <div key={weekData.week} className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleWeek(weekData.week)}
            className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex justify-between items-center transition-colors"
          >
            <div className="flex items-center space-x-3">
              <h4 className="text-lg font-medium text-gray-900">Week {weekData.week}</h4>
              <span className="text-sm text-gray-500">({weekData.scores.length} teams)</span>
            </div>
            <div className="flex items-center space-x-2">
              {weekData.scores.length > 0 && (
                <span className="text-sm text-gray-600">
                  Leader: {weekData.scores[0]?.team_name} ({weekData.scores[0]?.season_total} pts)
                </span>
              )}
              <svg
                className={`w-5 h-5 text-gray-400 transform transition-transform ${
                  expandedWeeks.has(weekData.week) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>

          {expandedWeeks.has(weekData.week) && (
            <div className="px-6 py-4 bg-white">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Team</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Weekly Score</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Season Total</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Players</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {weekData.scores.map((teamScore) => {
                      const teamKey = `${teamScore.team_id}-${weekData.week}`;
                      const isExpanded = expandedTeams.has(teamKey);

                      return (
                        <React.Fragment key={teamScore.team_id}>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                                  teamScore.rank === 1
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : teamScore.rank <= 3
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {teamScore.rank}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{teamScore.team_name}</div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap text-right">
                              <div className="text-sm font-semibold text-gray-900">{teamScore.weekly_score}</div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap text-right">
                              <div className="text-sm font-semibold text-gray-900">{teamScore.season_total}</div>
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap text-center">
                              <button
                                onClick={() => toggleTeamBreakdown(teamScore.team_id, weekData.week)}
                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                              >
                                {isExpanded ? 'Hide' : 'Show'} ({teamScore.player_breakdown.length})
                              </button>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr>
                              <td colSpan={5} className="px-4 py-3 bg-gray-50">
                                {renderPlayerBreakdown(teamScore.player_breakdown)}
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default HistoricalScoresView;