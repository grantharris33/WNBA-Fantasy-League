import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { TeamScoreData, BonusDetail } from '../../types'; // Adjusted path
import BonusBreakdown from './BonusBreakdown';

interface StandingsTableProps {
  scores: TeamScoreData[];
}

const StandingsTable: React.FC<StandingsTableProps> = ({ scores }) => {
  const navigate = useNavigate();

  // Sort scores by season_points descending and assign rank
  const rankedScores = [...scores]
    .sort((a, b) => b.season_points - a.season_points)
    .map((score, index) => ({ ...score, rank: index + 1 }));

  const handleTeamClick = (teamId: number) => {
    navigate(`/team/${teamId}`);
  };

  const renderBonusDetails = (bonuses: BonusDetail[]) => {
    return <BonusBreakdown bonuses={bonuses} variant="inline" showTitle={false} />;
  };

  if (rankedScores.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 text-center border border-slate-200">
        <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 rounded-full flex items-center justify-center">
          <span className="text-2xl">📊</span>
        </div>
        <p className="text-slate-600">No standings data available currently.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider whitespace-nowrap">
                Rank
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider min-w-0">
                Team Name
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider whitespace-nowrap">
                Owner
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider whitespace-nowrap">
                Season Points
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider whitespace-nowrap">
                Weekly Points
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider whitespace-nowrap">
                Weekly Bonuses
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {rankedScores.map((scoreItem, index) => (
              <tr
                key={scoreItem.team_id}
                className="hover:bg-slate-50 transition-colors cursor-pointer"
                onClick={() => handleTeamClick(scoreItem.team_id)}
              >
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                      index === 0 ? 'bg-yellow-100 text-yellow-800' :
                      index === 1 ? 'bg-slate-100 text-slate-800' :
                      index === 2 ? 'bg-orange-100 text-orange-800' :
                      'bg-[#0c7ff2] bg-opacity-10 text-[#0c7ff2]'
                    }`}>
                      {scoreItem.rank}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 min-w-0">
                  <div className="text-sm font-medium text-slate-900 truncate">{scoreItem.team_name}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-slate-600">{scoreItem.owner_name || 'N/A'}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <div className="text-sm font-semibold text-slate-900">{scoreItem.season_points}</div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    scoreItem.weekly_delta > 0 ? 'bg-green-100 text-green-800' :
                    scoreItem.weekly_delta < 0 ? 'bg-red-100 text-red-800' :
                    'bg-slate-100 text-slate-600'
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