import React from 'react';
import type { UserTeam, Player, BonusDetail } from '../../types';

interface RosterViewProps {
  team: UserTeam;
  onDropPlayer: (playerId: number) => void;
  onSetStarters: () => void;
  movesRemaining: number; // Currently unused but kept for future use
  teamBonuses?: BonusDetail[];
  onPlayerClick?: (playerId: number) => void;
}

const RosterView: React.FC<RosterViewProps> = ({
    team,
  onDropPlayer,
  onSetStarters,
  movesRemaining,
  teamBonuses,
  onPlayerClick
}) => {
  // These variables are kept for future feature implementation
  console.debug('Moves remaining:', movesRemaining, 'Team bonuses:', teamBonuses);
  // Separate starters and bench players
  const starters: Player[] = [];
  const bench: Player[] = [];

  // Use roster_slots if available (new API), otherwise fall back to roster (old API)
  if (team.roster_slots) {
    team.roster_slots.forEach((slot) => {
      if (slot.player) {
        if (slot.is_starter) {
          starters.push(slot.player);
        } else {
          bench.push(slot.player);
        }
      }
    });
  } else if (team.roster) {
    // Fallback for backward compatibility - assume first 5 are starters
    team.roster.forEach((player, index) => {
      if (index < 5) {
        starters.push(player);
      } else {
        bench.push(player);
      }
    });
  }

  const handlePlayerRowClick = (player: Player) => {
    if (onPlayerClick) {
      onPlayerClick(player.id);
    }
  };

  // This should open the "Set Starters" modal, not drop the player
  const handleToggleStarter = () => {
    // For now, we'll open the Set Starters modal instead of directly changing
    // This maintains the existing API contract
    onSetStarters();
  };

  const renderPlayerRow = (player: Player, isStarter: boolean) => (
    <tr key={player.id} className="hover:bg-slate-50 transition-colors cursor-pointer">
      <td className="px-4 py-3" onClick={() => handlePlayerRowClick(player)}>
        <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full w-10 h-10 border border-slate-200" style={{backgroundImage: `url("https://via.placeholder.com/40x40")`}}></div>
      </td>
      <td className="px-4 py-3 text-slate-800 text-sm font-medium cursor-pointer" onClick={() => handlePlayerRowClick(player)}>
        {player.full_name}
      </td>
      <td className="px-4 py-3 text-slate-700 text-sm cursor-pointer" onClick={() => handlePlayerRowClick(player)}>
        {player.position}
      </td>
      <td className="px-4 py-3 text-slate-500 text-sm cursor-pointer" onClick={() => handlePlayerRowClick(player)}>
        {player.team_abbr}
      </td>
      <td className="px-4 py-3 cursor-pointer" onClick={() => handlePlayerRowClick(player)}>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>
      </td>
      <td className="px-4 py-3 text-slate-700 text-sm font-medium cursor-pointer" onClick={() => handlePlayerRowClick(player)}>
        22
      </td>
      <td className="px-4 py-3">
        <div className="flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleToggleStarter();
            }}
            className={`text-xs font-medium flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              isStarter
                ? 'text-orange-600 hover:text-orange-800 hover:bg-orange-50'
                : 'text-green-600 hover:text-green-800 hover:bg-green-50'
            }`}
            title={isStarter ? 'Move to bench' : 'Set as starter'}
          >
            <span className="material-icons text-sm">{isStarter ? 'arrow_downward' : 'arrow_upward'}</span>
            {isStarter ? 'Bench' : 'Start'}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDropPlayer(player.id);
            }}
            className="text-xs font-medium flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:text-red-800 hover:bg-red-50 transition-colors"
            title="Drop player from team"
          >
            <span className="material-icons text-sm">person_remove</span>
            Drop
          </button>
        </div>
      </td>
    </tr>
  );

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg">
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <div>
          <h1 className="text-slate-900 text-3xl font-bold">Set Lineup</h1>
          <p className="text-slate-500 text-base">Week 1: June 1 - June 7</p>
        </div>
        <button
          onClick={onSetStarters}
          className="flex items-center justify-center gap-2 rounded-lg h-10 px-5 bg-[#0c7ff2] text-white text-sm font-semibold hover:bg-[#0a68c4] transition-colors shadow-sm"
        >
          <span className="material-icons text-lg">save</span>
          Set Starters
        </button>
      </div>

      <div className="mb-8">
        <h3 className="text-slate-800 text-xl font-semibold mb-4">Starting Lineup</h3>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider w-16">Player</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Position</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Team</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Fantasy Points Last Week</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider w-32">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {starters.length > 0 ? (
                starters.map((player) => renderPlayerRow(player, true))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-sm">
                    No starters set. Click "Set Starters" to configure your starting lineup.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="text-slate-800 text-xl font-semibold mb-4">Bench</h3>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider w-16">Player</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Position</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Team</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider">Points</th>
                <th className="px-4 py-3 text-left text-slate-600 text-xs font-semibold uppercase tracking-wider w-32">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {bench.length > 0 ? (
                bench.map((player) => renderPlayerRow(player, false))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500 text-sm">
                    No bench players available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default RosterView;