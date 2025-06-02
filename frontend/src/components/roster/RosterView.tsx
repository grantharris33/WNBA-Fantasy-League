import React from 'react';
import { StarIcon, UserIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import type { UserTeam, Player } from '../../types';

interface RosterViewProps {
  team: UserTeam;
  onDropPlayer: (playerId: number) => void;
  onSetStarters: () => void;
}

const RosterView: React.FC<RosterViewProps> = ({ team, onDropPlayer, onSetStarters }) => {
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

  const renderPlayerCard = (player: Player, isStarter: boolean) => (
    <div
      key={player.id}
      className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
        isStarter ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            {isStarter ? (
              <StarIconSolid className="h-6 w-6 text-yellow-500" />
            ) : (
              <UserIcon className="h-6 w-6 text-gray-400" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-900">{player.full_name}</h3>
            <p className="text-xs text-gray-500">
              {player.position} • {player.team_abbr}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {isStarter && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              Starter
            </span>
          )}
          <button
            onClick={() => onDropPlayer(player.id)}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Drop
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Starting Lineup */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <StarIcon className="h-5 w-5 text-yellow-500 mr-2" />
            Starting Lineup ({starters.length}/5)
          </h2>
          <button
            onClick={onSetStarters}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Edit Starters
          </button>
        </div>

        {starters.length === 0 ? (
          <div className="text-center py-8">
            <StarIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No starters set</h3>
            <p className="mt-1 text-sm text-gray-500">
              You need to set 5 starters to compete.
            </p>
            <button
              onClick={onSetStarters}
              className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Set Starting Lineup
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {starters.map((player) => renderPlayerCard(player, true))}
          </div>
        )}

        {starters.length > 0 && starters.length < 5 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <StarIcon className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Incomplete Starting Lineup
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    You need {5 - starters.length} more starter{5 - starters.length !== 1 ? 's' : ''} to complete your lineup.
                    Must include ≥2 Guards and ≥1 Forward/Center.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bench */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
          <UserIcon className="h-5 w-5 text-gray-500 mr-2" />
          Bench ({bench.length})
        </h2>

        {bench.length === 0 ? (
          <div className="text-center py-8">
            <UserIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No bench players</h3>
            <p className="mt-1 text-sm text-gray-500">
              Add players from free agents to build depth.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bench.map((player) => renderPlayerCard(player, false))}
          </div>
        )}
      </div>

      {/* Roster Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Roster Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{(team.roster_slots?.length || team.roster?.length || 0)}</div>
            <div className="text-sm text-gray-500">Total Players</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{starters.length}</div>
            <div className="text-sm text-gray-500">Starters</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{bench.length}</div>
            <div className="text-sm text-gray-500">Bench</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{10 - (team.roster_slots?.length || team.roster?.length || 0)}</div>
            <div className="text-sm text-gray-500">Open Spots</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RosterView;