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
      <ul className="list-disc list-inside text-xs">
        {bonuses.map((bonus, idx) => (
          <li key={idx}>{bonus.reason}: {bonus.points > 0 ? '+': ''}{bonus.points} pts</li>
        ))}
      </ul>
    );
  };

  if (rankedScores.length === 0) {
    return <p className="text-gray-600">No standings data available currently.</p>;
  }

  return (
    <div className="overflow-x-auto bg-white shadow-md rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Team Name</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Season Points</th>
            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Weekly Δ</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Weekly Bonuses</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rankedScores.map((scoreItem) => (
            <tr key={scoreItem.team_id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{scoreItem.rank}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{scoreItem.team_name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{scoreItem.owner_name || 'N/A'}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 text-right font-semibold">{scoreItem.season_points}</td>
              <td
                className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium
                            ${scoreItem.weekly_change > 0 ? 'text-green-600' : scoreItem.weekly_change < 0 ? 'text-red-600' : 'text-gray-500'}`}
              >
                {scoreItem.weekly_change > 0 ? '+' : ''}{scoreItem.weekly_change}
              </td>
              <td className="px-6 py-4 text-sm text-gray-500">{renderBonusDetails(scoreItem.weekly_bonuses)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StandingsTable;