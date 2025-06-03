import React from 'react';
import type { DraftPick, Player } from '../../types/draft';

interface MyTeamPanelProps {
  myTeamId: number | undefined; // ID of the user's team in this league
  teamName: string | undefined;
  allPicks: DraftPick[];
  // allPlayers: Player[]; // Potentially needed if picks don't contain full player details
}

const MyTeamPanel: React.FC<MyTeamPanelProps> = ({ myTeamId, teamName, allPicks }) => {
  const myTeamPicks = React.useMemo(() => {
    if (!myTeamId) return []; // Return empty if no team ID, hook called unconditionally
    return allPicks.filter(pick => pick.team_id === myTeamId);
  }, [allPicks, myTeamId]);

  if (!myTeamId) {
    // Optionally, show a message if the user is in the league but has no team assigned to them for this draft
    // For now, returning null if no specific team context for this user.
    return null;
  }

  // Simple roster structure for display
  const roster: { [key: string]: Player[] } = {
    G: [],
    F: [],
    C: [],
    UTIL: [], // For players whose positions don't fit G/F/C or if position is null
  };

  myTeamPicks.forEach(pick => {
    const playerDetails: Partial<Player> = { // Constructing a Player-like object from pick details
      id: pick.player_id,
      full_name: pick.player_name,
      position: pick.player_position,
      // team_abbr can be added if available on pick or fetched separately
    };

    if (playerDetails.position === 'G') roster.G.push(playerDetails as Player);
    else if (playerDetails.position === 'F') roster.F.push(playerDetails as Player);
    else if (playerDetails.position === 'C') roster.C.push(playerDetails as Player);
    else roster.UTIL.push(playerDetails as Player);
  });

  // Position requirements (typical fantasy basketball roster requirements)
  const requirements = {
    G: { min: 2, current: roster.G.length, label: 'Guards (≥2)' },
    F: { min: 1, current: roster.F.length, label: 'Forwards (≥1)' },
    C: { min: 1, current: roster.C.length, label: 'Centers (≥1)' },
    Total: { min: 10, current: myTeamPicks.length, label: 'Total Roster (10)' }
  };

  const getRequirementStatus = (req: { min: number; current: number }) => {
    if (req.current >= req.min) return 'text-green-600 bg-green-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-xl font-semibold mb-3">My Team ({teamName || 'Team'})</h2>

      {/* Position Requirements Section */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Roster Requirements</h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {Object.entries(requirements).map(([pos, req]) => (
            <div key={pos} className={`p-2 rounded ${getRequirementStatus(req)}`}>
              <div className="font-medium">{req.label}</div>
              <div className="text-lg font-bold">
                {req.current}/{req.min}
                {req.current >= req.min && ' ✓'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current Roster */}
      {myTeamPicks.length === 0 ? (
        <p className="text-gray-500 italic py-4 text-center">Your team hasn't made any picks yet.</p>
      ) : (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Current Roster ({myTeamPicks.length} players)</h3>
          {(Object.keys(roster) as Array<keyof typeof roster>).map(posCategory => {
            if (roster[posCategory].length > 0) {
              return (
                <div key={posCategory}>
                  <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">{posCategory} ({roster[posCategory].length})</h4>
                  <ul className="space-y-1">
                    {roster[posCategory].map(player => (
                      <li key={player.id} className="text-gray-700 text-sm p-1 bg-gray-50 rounded">
                        {player.full_name}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            }
            return null;
          })}
        </div>
      )}
    </div>
  );
};

export default MyTeamPanel;