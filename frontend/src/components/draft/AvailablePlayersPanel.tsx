import React, { useState, useMemo, useCallback } from 'react';
import type { Player, DraftState } from '../../types/draft';
import PlayerFilterControls from './PlayerFilterControls';
import PlayerListItem from './PlayerListItem';

interface AvailablePlayersPanelProps {
  allPlayers: Player[]; // Changed from `players` to `allPlayers` representing initial fetch
  draftState: DraftState | null;
  userTeamId?: number | null;
  onPickPlayer: (playerId: number) => void;
  queuedPlayerIds: Set<number>;
  onToggleQueuePlayer: (playerId: number) => void;
  isLoadingPlayerStats?: boolean;
}

const AvailablePlayersPanel: React.FC<AvailablePlayersPanelProps> = ({
  allPlayers,
  draftState,
  userTeamId,
  onPickPlayer,
  queuedPlayerIds,
  onToggleQueuePlayer,
  isLoadingPlayerStats,
}) => {
  const [nameFilter, setNameFilter] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'fantasy_ppg' | 'ppg' | 'position'>('fantasy_ppg');

  const handleFilterChange = useCallback((filters: { name: string; position: string }) => {
    setNameFilter(filters.name.toLowerCase());
    setPositionFilter(filters.position);
  }, []);

  // Determine players already picked from draftState.picks
  const pickedPlayerIds = useMemo(() => {
    if (!draftState) return new Set<number>();
    return new Set(draftState.picks.map(pick => pick.player_id));
  }, [draftState]);

  // Filtered, sorted, and *actually* available players
  const trulyAvailablePlayers = useMemo(() => {
    const filtered = allPlayers.filter(player => {
      if (pickedPlayerIds.has(player.id)) return false; // Exclude picked players
      const nameMatch = player.full_name.toLowerCase().includes(nameFilter);
      const positionMatch = positionFilter ? player.position === positionFilter : true;
      return nameMatch && positionMatch;
    });

    // Sort players based on selected criteria
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'fantasy_ppg': {
          const aFantasy = a.stats_2024?.fantasy_ppg || 0;
          const bFantasy = b.stats_2024?.fantasy_ppg || 0;
          return bFantasy - aFantasy; // Descending order
        }
        case 'ppg': {
          const aPpg = a.stats_2024?.ppg || 0;
          const bPpg = b.stats_2024?.ppg || 0;
          return bPpg - aPpg; // Descending order
        }
        case 'position': {
          const aPos = a.position || 'ZZ'; // Put null positions at end
          const bPos = b.position || 'ZZ';
          return aPos.localeCompare(bPos);
        }
        case 'name':
        default:
          return a.full_name.localeCompare(b.full_name);
      }
    });
  }, [allPlayers, pickedPlayerIds, nameFilter, positionFilter, sortBy]);

  // Available positions for filtering should be derived from truly available players
  const availablePositionsForFilter = useMemo(() => {
    const positions = new Set(trulyAvailablePlayers.map(p => p.position).filter(Boolean) as string[]);
    return Array.from(positions).sort();
  }, [trulyAvailablePlayers]);

  if (!draftState) {
    return <div className="p-4 border rounded shadow bg-white text-center">Loading player data...</div>;
  }

  const isMyTurn = userTeamId === draftState.current_team_id;

  // Count players with stats vs without
  const playersWithStats = trulyAvailablePlayers.filter(p => p.stats_2024).length;
  const totalPlayers = trulyAvailablePlayers.length;

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-2xl font-bold mb-4">
        Available Players ({totalPlayers})
        {totalPlayers > 0 && (
          <span className="text-sm font-normal text-gray-600 ml-2">
            ({playersWithStats} with 2024 stats)
            {isLoadingPlayerStats && <span className="text-blue-600 ml-1">Loading stats...</span>}
          </span>
        )}
      </h2>

      <div className="mb-4 space-y-3">
        <PlayerFilterControls
          onFilterChange={handleFilterChange}
          availablePositions={availablePositionsForFilter}
        />

        <div className="flex items-center gap-2">
          <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">
            Sort by:
          </label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="fantasy_ppg">Fantasy PPG (2024)</option>
            <option value="ppg">Points Per Game (2024)</option>
            <option value="position">Position</option>
            <option value="name">Name</option>
          </select>
        </div>
      </div>

      {trulyAvailablePlayers.length === 0 ? (
        <p className="text-gray-600 text-center py-4">
          {allPlayers.length > 0 ? 'No players match your current filters or all available players have been drafted.' : 'No players available.'}
        </p>
      ) : (
        <ul className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto border rounded">
          {trulyAvailablePlayers.map(player => (
            <PlayerListItem
              key={player.id}
              player={player}
              isMyTurn={isMyTurn}
              draftStatus={draftState.status}
              onPickPlayer={onPickPlayer}
              onToggleQueuePlayer={onToggleQueuePlayer}
              isQueued={queuedPlayerIds.has(player.id)}
            />
          ))}
        </ul>
      )}
    </div>
  );
};

export default AvailablePlayersPanel;