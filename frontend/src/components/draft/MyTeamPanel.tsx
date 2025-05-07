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

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-xl font-semibold mb-3">My Team ({teamName || 'Team'})</h2>
      {myTeamPicks.length === 0 ? (
        <p className="text-gray-500 italic py-4 text-center">Your team hasn't made any picks yet.</p>
      ) : (
        <div className="space-y-3">
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