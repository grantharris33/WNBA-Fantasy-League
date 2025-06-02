import React, { useState } from 'react';
import type { ScoreTrend } from '../../types';

interface ScoreTrendsChartProps {
  scoreTrends: ScoreTrend[];
}

const ScoreTrendsChart: React.FC<ScoreTrendsChartProps> = ({ scoreTrends }) => {
  const [selectedTeams, setSelectedTeams] = useState<Set<number>>(new Set());

  if (scoreTrends.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📈</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No Score Trends Available</h3>
        <p className="text-gray-600">Score trends will appear after multiple weeks of play.</p>
      </div>
    );
  }

  // Filter trends that have actual data
  const validTrends = scoreTrends.filter(trend => trend.weekly_scores.length > 0);

  if (validTrends.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📊</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Not Enough Data</h3>
        <p className="text-gray-600">Need at least one week of scores to show trends.</p>
      </div>
    );
  }

  // Get all weeks across all teams
  const allWeeks = Array.from(new Set(validTrends.flatMap(trend => trend.weeks))).sort((a, b) => a - b);

  // Get min/max scores for scaling
  const allScores = validTrends.flatMap(trend => trend.weekly_scores);
  const minScore = Math.min(...allScores);
  const maxScore = Math.max(...allScores);
  const scoreRange = maxScore - minScore || 1; // Avoid division by zero

  const colors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
  ];

  const toggleTeam = (teamId: number) => {
    const newSelected = new Set(selectedTeams);
    if (newSelected.has(teamId)) {
      newSelected.delete(teamId);
    } else {
      newSelected.add(teamId);
    }
    setSelectedTeams(newSelected);
  };

  const selectAllTeams = () => {
    setSelectedTeams(new Set(validTrends.map(trend => trend.team_id)));
  };

  const clearSelection = () => {
    setSelectedTeams(new Set());
  };

  // Show selected teams or first 5 if none selected
  const displayTrends = selectedTeams.size > 0
    ? validTrends.filter(trend => selectedTeams.has(trend.team_id))
    : validTrends.slice(0, 5);

  const renderChart = () => {
    const chartWidth = 800;
    const chartHeight = 400;
    const padding = 60;
    const innerWidth = chartWidth - (padding * 2);
    const innerHeight = chartHeight - (padding * 2);

    const xStep = innerWidth / Math.max(allWeeks.length - 1, 1);

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm overflow-x-auto">
        <svg width={chartWidth} height={chartHeight} className="border border-gray-200 rounded">
          {/* Grid lines */}
          {allWeeks.map((week, index) => (
            <line
              key={`grid-x-${week}`}
              x1={padding + (index * xStep)}
              y1={padding}
              x2={padding + (index * xStep)}
              y2={chartHeight - padding}
              stroke="#E5E7EB"
              strokeWidth="1"
              strokeDasharray="2,2"
            />
          ))}

          {/* Y-axis grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={`grid-y-${ratio}`}
              x1={padding}
              y1={padding + (ratio * innerHeight)}
              x2={chartWidth - padding}
              y2={padding + (ratio * innerHeight)}
              stroke="#E5E7EB"
              strokeWidth="1"
              strokeDasharray="2,2"
            />
          ))}

          {/* Trend lines */}
          {displayTrends.map((trend, trendIndex) => {
            const color = colors[trendIndex % colors.length];

            // Create path for this team's scores
            const pathData = trend.weeks.map((week, index) => {
              const x = padding + (allWeeks.indexOf(week) * xStep);
              const normalizedScore = (trend.weekly_scores[index] - minScore) / scoreRange;
              const y = chartHeight - padding - (normalizedScore * innerHeight);
              return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
            }).join(' ');

            return (
              <g key={trend.team_id}>
                {/* Line */}
                <path
                  d={pathData}
                  fill="none"
                  stroke={color}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Points */}
                {trend.weeks.map((week, index) => {
                  const x = padding + (allWeeks.indexOf(week) * xStep);
                  const normalizedScore = (trend.weekly_scores[index] - minScore) / scoreRange;
                  const y = chartHeight - padding - (normalizedScore * innerHeight);

                  return (
                    <circle
                      key={`${trend.team_id}-${week}`}
                      cx={x}
                      cy={y}
                      r="5"
                      fill={color}
                      stroke="white"
                      strokeWidth="2"
                    />
                  );
                })}
              </g>
            );
          })}

          {/* X-axis labels */}
          {allWeeks.map((week, index) => (
            <text
              key={`label-x-${week}`}
              x={padding + (index * xStep)}
              y={chartHeight - 10}
              textAnchor="middle"
              className="text-sm fill-gray-600"
            >
              Week {week}
            </text>
          ))}

          {/* Y-axis labels */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const score = minScore + (ratio * scoreRange);
            return (
              <text
                key={`label-y-${ratio}`}
                x={10}
                y={padding + ((1 - ratio) * innerHeight) + 5}
                textAnchor="start"
                className="text-sm fill-gray-600"
              >
                {score.toFixed(1)}
              </text>
            );
          })}
        </svg>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Score Trends Over Time</h3>
        <p className="text-gray-600">Track how team performance changes week by week</p>
      </div>

      {/* Team Selection */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h4 className="text-lg font-semibold text-gray-900">Select Teams to Display</h4>
          <div className="space-x-2">
            <button
              onClick={selectAllTeams}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Select All
            </button>
            <button
              onClick={clearSelection}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Clear
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {validTrends.map((trend, index) => (
            <button
              key={trend.team_id}
              onClick={() => toggleTeam(trend.team_id)}
              className={`p-3 rounded-lg text-left transition-colors ${
                selectedTeams.has(trend.team_id) || (selectedTeams.size === 0 && index < 5)
                  ? 'bg-blue-100 border-2 border-blue-500 text-blue-900'
                  : 'bg-white border-2 border-gray-200 text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="font-medium text-sm">{trend.team_name}</span>
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {trend.weekly_scores.length} weeks
              </div>
            </button>
          ))}
        </div>

        {selectedTeams.size === 0 && validTrends.length > 5 && (
          <p className="text-sm text-gray-600 mt-2">
            Showing first 5 teams. Select specific teams to customize the view.
          </p>
        )}
      </div>

      {/* Chart */}
      {renderChart()}

      {/* Legend */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Legend</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {displayTrends.map((trend, index) => {
            const color = colors[index % colors.length];
            const latestScore = trend.weekly_scores[trend.weekly_scores.length - 1];
            const previousScore = trend.weekly_scores.length > 1
              ? trend.weekly_scores[trend.weekly_scores.length - 2]
              : latestScore;
            const change = latestScore - previousScore;

            return (
              <div key={trend.team_id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <div className="flex-1">
                  <div className="font-medium text-sm text-gray-900">{trend.team_name}</div>
                  <div className="text-xs text-gray-600">
                    Latest: {latestScore.toFixed(1)} pts
                    {change !== 0 && (
                      <span className={`ml-1 ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ({change > 0 ? '+' : ''}{change.toFixed(1)})
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ScoreTrendsChart;