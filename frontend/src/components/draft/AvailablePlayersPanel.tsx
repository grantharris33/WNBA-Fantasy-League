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
}

const AvailablePlayersPanel: React.FC<AvailablePlayersPanelProps> = ({
  allPlayers,
  draftState,
  userTeamId,
  onPickPlayer,
  queuedPlayerIds,
  onToggleQueuePlayer,
}) => {
  const [nameFilter, setNameFilter] = useState('');
  const [positionFilter, setPositionFilter] = useState('');

  const handleFilterChange = useCallback((filters: { name: string; position: string }) => {
    setNameFilter(filters.name.toLowerCase());
    setPositionFilter(filters.position);
  }, []);

  // Determine players already picked from draftState.picks
  const pickedPlayerIds = useMemo(() => {
    if (!draftState) return new Set<number>();
    return new Set(draftState.picks.map(pick => pick.player_id));
  }, [draftState]);

  // Filtered and *actually* available players
  const trulyAvailablePlayers = useMemo(() => {
    return allPlayers.filter(player => {
      if (pickedPlayerIds.has(player.id)) return false; // Exclude picked players
      const nameMatch = player.full_name.toLowerCase().includes(nameFilter);
      const positionMatch = positionFilter ? player.position === positionFilter : true;
      return nameMatch && positionMatch;
    });
  }, [allPlayers, pickedPlayerIds, nameFilter, positionFilter]);

  // Available positions for filtering should be derived from truly available players
  const availablePositionsForFilter = useMemo(() => {
    const positions = new Set(trulyAvailablePlayers.map(p => p.position).filter(Boolean) as string[]);
    return Array.from(positions).sort();
  }, [trulyAvailablePlayers]);

  if (!draftState) {
    return <div className="p-4 border rounded shadow bg-white text-center">Loading player data...</div>;
  }

  const isMyTurn = userTeamId === draftState.current_team_id;

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-2xl font-bold mb-4">Available Players ({trulyAvailablePlayers.length})</h2>
      <PlayerFilterControls
        onFilterChange={handleFilterChange}
        availablePositions={availablePositionsForFilter}
      />
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