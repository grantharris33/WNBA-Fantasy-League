import React from 'react';
import type { TopPerformer } from '../../types';

interface TopPerformersViewProps {
  topPerformers: TopPerformer[];
}

const TopPerformersView: React.FC<TopPerformersViewProps> = ({ topPerformers }) => {
  const getMedalIcon = (index: number) => {
    switch (index) {
      case 0:
        return '🥇';
      case 1:
        return '🥈';
      case 2:
        return '🥉';
      default:
        return '🏅';
    }
  };

  const getPositionColor = (index: number) => {
    switch (index) {
      case 0:
        return 'bg-gradient-to-r from-yellow-400 to-yellow-600';
      case 1:
        return 'bg-gradient-to-r from-gray-400 to-gray-600';
      case 2:
        return 'bg-gradient-to-r from-amber-600 to-amber-800';
      default:
        return 'bg-gradient-to-r from-blue-500 to-blue-700';
    }
  };

  if (topPerformers.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">⭐</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No Top Performers Yet</h3>
        <p className="text-gray-600">Check back after the current week's games are complete.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Top Performers This Week</h3>
        <p className="text-gray-600">Players with the highest scoring performances</p>
      </div>

      {/* Podium for top 3 */}
      {topPerformers.length >= 3 && (
        <div className="flex justify-center items-end space-x-4 mb-8">
          {/* 2nd Place */}
          <div className="text-center">
            <div className={`w-20 h-16 rounded-t-lg ${getPositionColor(1)} flex items-end justify-center pb-2`}>
              <span className="text-white font-bold text-lg">2</span>
            </div>
            <div className="bg-white p-4 rounded-b-lg shadow-md border-t-0 min-w-[140px]">
              <div className="text-2xl mb-1">🥈</div>
              <div className="font-semibold text-sm text-gray-800">{topPerformers[1].player_name}</div>
              <div className="text-xs text-gray-600">{topPerformers[1].team_abbr}</div>
              <div className="text-lg font-bold text-gray-900">{topPerformers[1].total_points} pts</div>
            </div>
          </div>

          {/* 1st Place */}
          <div className="text-center">
            <div className={`w-24 h-20 rounded-t-lg ${getPositionColor(0)} flex items-end justify-center pb-2`}>
              <span className="text-white font-bold text-xl">1</span>
            </div>
            <div className="bg-white p-4 rounded-b-lg shadow-lg border-t-0 min-w-[160px]">
              <div className="text-3xl mb-1">🥇</div>
              <div className="font-bold text-base text-gray-800">{topPerformers[0].player_name}</div>
              <div className="text-sm text-gray-600">{topPerformers[0].team_abbr}</div>
              <div className="text-xl font-bold text-gray-900">{topPerformers[0].total_points} pts</div>
            </div>
          </div>

          {/* 3rd Place */}
          <div className="text-center">
            <div className={`w-20 h-12 rounded-t-lg ${getPositionColor(2)} flex items-end justify-center pb-2`}>
              <span className="text-white font-bold text-lg">3</span>
            </div>
            <div className="bg-white p-4 rounded-b-lg shadow-md border-t-0 min-w-[140px]">
              <div className="text-2xl mb-1">🥉</div>
              <div className="font-semibold text-sm text-gray-800">{topPerformers[2].player_name}</div>
              <div className="text-xs text-gray-600">{topPerformers[2].team_abbr}</div>
              <div className="text-lg font-bold text-gray-900">{topPerformers[2].total_points} pts</div>
            </div>
          </div>
        </div>
      )}

      {/* Full leaderboard */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h4 className="text-lg font-semibold text-gray-900">Complete Leaderboard</h4>
        </div>

        <div className="divide-y divide-gray-200">
          {topPerformers.map((performer, index) => (
            <div
              key={performer.player_id}
              className={`px-6 py-4 flex items-center justify-between hover:bg-gray-50 ${
                index < 3 ? 'bg-gradient-to-r from-blue-50 to-white' : ''
              }`}
            >
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <span className="text-2xl">{getMedalIcon(index)}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                      index < 3
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {index + 1}
                    </span>
                    <div>
                      <div className="text-lg font-semibold text-gray-900">{performer.player_name}</div>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <span>{performer.team_abbr}</span>
                        {performer.position && (
                          <>
                            <span>•</span>
                            <span className="bg-gray-100 px-2 py-1 rounded text-xs">{performer.position}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{performer.total_points}</div>
                <div className="text-sm text-gray-600">points</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance insights */}
      {topPerformers.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-6">
          <h4 className="text-lg font-semibold text-blue-900 mb-3">Performance Insights</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <div className="text-blue-600 font-semibold">Highest Score</div>
              <div className="text-xl font-bold text-gray-900">{topPerformers[0].total_points} pts</div>
              <div className="text-gray-600">{topPerformers[0].player_name}</div>
            </div>

            <div className="bg-white rounded-lg p-4">
              <div className="text-blue-600 font-semibold">Average (Top 5)</div>
              <div className="text-xl font-bold text-gray-900">
                {topPerformers.length > 0
                  ? (topPerformers.slice(0, 5).reduce((sum, p) => sum + p.total_points, 0) / Math.min(5, topPerformers.length)).toFixed(1)
                  : '0'
                } pts
              </div>
              <div className="text-gray-600">Top performers avg</div>
            </div>

            <div className="bg-white rounded-lg p-4">
              <div className="text-blue-600 font-semibold">Total Players</div>
              <div className="text-xl font-bold text-gray-900">{topPerformers.length}</div>
              <div className="text-gray-600">With recorded stats</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopPerformersView;