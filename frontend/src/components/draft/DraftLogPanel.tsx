import React from 'react';
import type { DraftPick } from '../../types/draft'; // Assuming DraftPick type is defined

interface DraftLogPanelProps {
  picks: DraftPick[];
}

const DraftLogPanel: React.FC<DraftLogPanelProps> = ({ picks }) => {
  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-xl font-semibold mb-3">Draft Log ({picks.length} picks)</h2>
      {picks.length === 0 ? (
        <p className="text-gray-500 italic py-4 text-center">No picks made yet.</p>
      ) : (
        <ul className="max-h-96 lg:max-h-[calc(100vh-300px)] overflow-y-auto divide-y divide-gray-200 border rounded">
          {[...picks].reverse().map((pick, index) => (
            <li key={pick.id || index} className="p-3 text-sm hover:bg-gray-50">
              <div className="flex justify-between items-center">
                <span className="font-medium">
                  R{pick.round}, Pick {pick.pick_number}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(pick.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className="mt-1">
                <strong>{pick.team_name || `Team ID: ${pick.team_id}`}</strong> selected{' '}
                <strong>{pick.player_name || `Player ID: ${pick.player_id}`}</strong>
                {pick.player_position && ` (${pick.player_position})`}
              </div>
              {pick.is_auto && (
                <div className="text-xs text-orange-500 mt-1">Auto-picked</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DraftLogPanel;