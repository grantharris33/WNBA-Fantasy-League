import React from 'react';
import type { Player } from '../../types/draft';

interface PlayerQueuePanelProps {
  queuedPlayerIds: Set<number>;
  allPlayers: Player[]; // To look up player details from IDs
  onToggleQueuePlayer: (playerId: number) => void;
  onPickFromQueue: (playerId: number) => void; // For quickly picking the top player
  isMyTurn: boolean;
  draftStatus: 'pending' | 'active' | 'paused' | 'completed';
}

const PlayerQueuePanel: React.FC<PlayerQueuePanelProps> = ({
  queuedPlayerIds,
  allPlayers,
  onToggleQueuePlayer,
  onPickFromQueue,
  isMyTurn,
  draftStatus,
}) => {
  const queuedPlayers = React.useMemo(() => {
    return Array.from(queuedPlayerIds)
      .map(id => allPlayers.find(p => p.id === id))
      .filter(Boolean) as Player[]; // Filter out undefined if a player ID in queue is somehow not in allPlayers
  }, [queuedPlayerIds, allPlayers]);

  const canPick = isMyTurn && draftStatus === 'active';

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-xl font-semibold mb-3">My Player Queue ({queuedPlayers.length})</h2>
      {queuedPlayers.length === 0 ? (
        <p className="text-gray-500 italic py-4 text-center">Your queue is empty. Add players from the list.</p>
      ) : (
        <ul className="divide-y divide-gray-200 max-h-96 overflow-y-auto border rounded">
          {queuedPlayers.map(player => (
            <li key={player.id} className="flex justify-between items-center p-3 hover:bg-gray-50">
              <div>
                <p className="font-medium text-gray-800">{player.full_name}</p>
                <p className="text-xs text-gray-500">
                  {player.position || 'N/A'} - {player.team_abbr || 'N/A'}
                </p>
              </div>
              <div className="flex gap-2 items-center">
                {/* Quick Pick button - only if it's this player's turn */}
                {canPick && (
                    <button
                        onClick={() => onPickFromQueue(player.id)}
                        className="px-2 py-1 text-xs font-medium rounded text-white bg-green-500 hover:bg-green-600 transition-colors"
                        title="Quickly draft this player"
                    >
                        Pick
                    </button>
                )}
                <button
                  onClick={() => onToggleQueuePlayer(player.id)}
                  className="px-2 py-1 text-xs text-red-600 hover:text-red-800 rounded border border-red-300 hover:bg-red-100 transition-colors"
                  title="Remove from queue"
                >
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PlayerQueuePanel;