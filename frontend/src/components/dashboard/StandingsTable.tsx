import React from 'react';
import type { TeamScoreData, BonusDetail } from '../../types'; // Adjusted path

interface StandingsTableProps {
  scores: TeamScoreData[];
}

const StandingsTable: React.FC<StandingsTableProps> = ({ scores }) => {
  // Sort scores by season_points descending and assign rank
  const rankedScores = [...scores]
    .sort((a, b) => b.season_points - a.season_points)
    .map((score, index) => ({ ...score, rank: index + 1 }));

  const renderBonusDetails = (bonuses: BonusDetail[]) => {
    if (!bonuses || bonuses.length === 0) return <span className="text-gray-400">-</span>;
    return (
      <ul className="list-disc list-inside text-xs space-y-1">
        {bonuses.map((bonus, idx) => (
          <li key={idx} className="text-gray-600">
            <span className="font-medium">{bonus.category}:</span> {bonus.points > 0 ? '+': ''}{bonus.points} pts
            <span className="text-gray-500"> ({bonus.player_name})</span>
          </li>
        ))}
      </ul>
    );
  };

  if (rankedScores.length === 0) {
    return (
      <div className="card p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <span className="text-2xl">📊</span>
        </div>
        <p className="text-gray-600">No standings data available currently.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                Rank
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider min-w-0">
                Team Name
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                Owner
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                Season Points
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                Weekly Points
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                Weekly Bonuses
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rankedScores.map((scoreItem, index) => (
              <tr key={scoreItem.team_id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                      index === 0 ? 'bg-yellow-100 text-yellow-800' :
                      index === 1 ? 'bg-gray-100 text-gray-800' :
                      index === 2 ? 'bg-orange-100 text-orange-800' :
                      'bg-blue-50 text-blue-700'
                    }`}>
                      {scoreItem.rank}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">{scoreItem.team_name}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-600">{scoreItem.owner_name || 'N/A'}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <div className="text-sm font-semibold text-gray-900">{scoreItem.season_points}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    scoreItem.weekly_delta > 0 ? 'bg-green-100 text-green-800' :
                    scoreItem.weekly_delta < 0 ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {scoreItem.weekly_delta > 0 ? '+' : ''}{scoreItem.weekly_delta}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <div className="max-w-xs">
                    {renderBonusDetails(scoreItem.bonuses)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StandingsTable;