import React from 'react';
import type { LeagueChampion } from '../../types';

interface LeagueChampionViewProps {
  champion: LeagueChampion | null;
}

const LeagueChampionView: React.FC<LeagueChampionViewProps> = ({ champion }) => {
  if (!champion) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🏆</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Season In Progress</h3>
        <p className="text-gray-600">The league champion will be crowned when the season ends.</p>
        <p className="text-gray-500 text-sm mt-2">Keep playing to see who takes the crown!</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Champion Announcement */}
      <div className="text-center bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 text-white py-12 px-8 rounded-xl shadow-lg">
        <div className="space-y-4">
          <div className="text-6xl animate-bounce">👑</div>
          <h2 className="text-4xl font-bold">League Champion!</h2>
          <div className="text-2xl font-semibold">{champion.team_name}</div>
          {champion.owner_name && (
            <div className="text-lg opacity-90">Owned by {champion.owner_name}</div>
          )}
        </div>
      </div>

      {/* Championship Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 text-center border-t-4 border-yellow-500">
          <div className="text-3xl mb-2">🏆</div>
          <div className="text-2xl font-bold text-gray-900">{champion.final_score}</div>
          <div className="text-gray-600">Final Score</div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 text-center border-t-4 border-blue-500">
          <div className="text-3xl mb-2">📊</div>
          <div className="text-2xl font-bold text-gray-900">{champion.weeks_won}</div>
          <div className="text-gray-600">Weeks Won</div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 text-center border-t-4 border-green-500">
          <div className="text-3xl mb-2">⭐</div>
          <div className="text-2xl font-bold text-gray-900">
            {champion.weeks_won > 0 ? ((champion.weeks_won / 10) * 100).toFixed(0) : '0'}%
          </div>
          <div className="text-gray-600">Win Rate</div>
        </div>
      </div>

      {/* Achievement Badges */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Championship Achievements</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Season Champion Badge */}
          <div className="flex items-center space-x-4 p-4 bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg border border-yellow-200">
            <div className="text-3xl">🏆</div>
            <div>
              <div className="font-semibold text-yellow-800">Season Champion</div>
              <div className="text-sm text-yellow-700">Highest total score for the season</div>
            </div>
          </div>

          {/* High Scorer Badge */}
          {champion.final_score >= 100 && (
            <div className="flex items-center space-x-4 p-4 bg-gradient-to-r from-red-50 to-red-100 rounded-lg border border-red-200">
              <div className="text-3xl">🔥</div>
              <div>
                <div className="font-semibold text-red-800">High Scorer</div>
                <div className="text-sm text-red-700">Scored 100+ points this season</div>
              </div>
            </div>
          )}

          {/* Consistent Performer Badge */}
          {champion.weeks_won >= 3 && (
            <div className="flex items-center space-x-4 p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
              <div className="text-3xl">💪</div>
              <div>
                <div className="font-semibold text-blue-800">Consistent Performer</div>
                <div className="text-sm text-blue-700">Won multiple weeks this season</div>
              </div>
            </div>
          )}

          {/* Dominant Champion Badge */}
          {champion.weeks_won >= 5 && (
            <div className="flex items-center space-x-4 p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg border border-purple-200">
              <div className="text-3xl">👑</div>
              <div>
                <div className="font-semibold text-purple-800">Dominant Champion</div>
                <div className="text-sm text-purple-700">Won 5+ weeks this season</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Championship Summary */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Championship Summary</h3>
        <div className="space-y-3 text-gray-700">
          <p>
            🎉 <strong>{champion.team_name}</strong> has been crowned the league champion with a total of{' '}
            <strong>{champion.final_score} points</strong> scored throughout the season.
          </p>

          {champion.weeks_won > 0 && (
            <p>
              📈 They demonstrated exceptional consistency by winning{' '}
              <strong>{champion.weeks_won} weeks</strong> during the regular season.
            </p>
          )}

          {champion.owner_name && (
            <p>
              👏 Congratulations to <strong>{champion.owner_name}</strong> for their outstanding fantasy management skills!
            </p>
          )}

          <p className="text-sm text-gray-600 mt-4">
            🏆 This championship represents the culmination of strategic drafting, smart waiver pickups,
            and optimal lineup management throughout the entire season.
          </p>
        </div>
      </div>

      {/* Celebration Animation */}
      <div className="text-center py-8">
        <div className="inline-flex space-x-2 text-4xl">
          <span className="animate-bounce" style={{ animationDelay: '0ms' }}>🎉</span>
          <span className="animate-bounce" style={{ animationDelay: '150ms' }}>🏆</span>
          <span className="animate-bounce" style={{ animationDelay: '300ms' }}>🎉</span>
        </div>
        <p className="text-gray-600 text-lg mt-4 font-medium">
          Season Complete!
        </p>
      </div>
    </div>
  );
};

export default LeagueChampionView;