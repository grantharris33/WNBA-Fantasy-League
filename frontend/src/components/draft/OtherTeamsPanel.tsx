import React, { useState } from 'react';
import type { DraftPick } from '../../types/draft';
import type { UserTeam } from '../../types';

interface OtherTeamsPanelProps {
  allTeams: UserTeam[];
  allPicks: DraftPick[];
  currentUserTeamId?: number;
}

const OtherTeamsPanel: React.FC<OtherTeamsPanelProps> = ({
  allTeams,
  allPicks,
  currentUserTeamId
}) => {
  const [expandedTeams, setExpandedTeams] = useState<Set<number>>(new Set());

  const toggleTeamExpansion = (teamId: number) => {
    const newExpanded = new Set(expandedTeams);
    if (newExpanded.has(teamId)) {
      newExpanded.delete(teamId);
    } else {
      newExpanded.add(teamId);
    }
    setExpandedTeams(newExpanded);
  };

  // Filter out the current user's team
  const otherTeams = allTeams.filter(team => team.id !== currentUserTeamId);

  // Group picks by team
  const picksByTeam = React.useMemo(() => {
    const grouped: { [key: number]: DraftPick[] } = {};
    allPicks.forEach(pick => {
      if (!grouped[pick.team_id]) grouped[pick.team_id] = [];
      grouped[pick.team_id].push(pick);
    });
    return grouped;
  }, [allPicks]);

  const getTeamRosterByPosition = (teamId: number) => {
    const teamPicks = picksByTeam[teamId] || [];
    const roster = { G: 0, F: 0, C: 0, Total: teamPicks.length };

    teamPicks.forEach(pick => {
      if (pick.player_position === 'G') roster.G++;
      else if (pick.player_position === 'F') roster.F++;
      else if (pick.player_position === 'C') roster.C++;
    });

    return roster;
  };

  if (otherTeams.length === 0) {
    return (
      <div className="p-4 border rounded shadow bg-white">
        <h2 className="text-xl font-semibold mb-3">Other Teams</h2>
        <p className="text-gray-500 italic text-center">No other teams in this league.</p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-xl font-semibold mb-3">Other Teams</h2>
      <div className="space-y-2">
        {otherTeams.map(team => {
          const teamPicks = picksByTeam[team.id] || [];
          const roster = getTeamRosterByPosition(team.id);
          const isExpanded = expandedTeams.has(team.id);

          return (
            <div key={team.id} className="border rounded-lg">
              <button
                onClick={() => toggleTeamExpansion(team.id)}
                className="w-full p-3 text-left hover:bg-gray-50 flex justify-between items-center transition-colors"
              >
                <div>
                  <div className="font-medium text-gray-900">{team.name}</div>
                  <div className="text-sm text-gray-600">
                    {roster.Total} picks • G:{roster.G} F:{roster.F} C:{roster.C}
                  </div>
                </div>
                <div className="text-gray-400">
                  {isExpanded ? '▼' : '▶'}
                </div>
              </button>

              {isExpanded && (
                <div className="px-3 pb-3 border-t bg-gray-50">
                  {teamPicks.length === 0 ? (
                    <p className="text-gray-500 italic py-2 text-center text-sm">No picks yet</p>
                  ) : (
                    <div className="space-y-2 mt-2">
                      {teamPicks
                        .sort((a, b) => a.pick_number - b.pick_number)
                        .map(pick => (
                          <div key={pick.id} className="flex justify-between items-center text-sm">
                            <span className="font-medium">{pick.player_name}</span>
                            <div className="flex gap-2 text-gray-600">
                              <span className="bg-gray-200 px-2 py-1 rounded text-xs">
                                {pick.player_position || 'N/A'}
                              </span>
                              <span className="text-xs">#{pick.pick_number}</span>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OtherTeamsPanel;