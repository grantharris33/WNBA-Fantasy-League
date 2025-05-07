import React from 'react';
import type { Player } from '../../types/draft';

interface PlayerListItemProps {
  player: Player;
  isMyTurn: boolean;
  draftStatus: 'pending' | 'active' | 'paused' | 'completed';
  onPickPlayer: (playerId: number) => void;
  onToggleQueuePlayer: (playerId: number) => void;
  isQueued: boolean;
}

const PlayerListItem: React.FC<PlayerListItemProps> = ({
  player,
  isMyTurn,
  draftStatus,
  onPickPlayer,
  onToggleQueuePlayer,
  isQueued,
}) => {
  const canPick = isMyTurn && draftStatus === 'active';

  return (
    <li className="flex justify-between items-center p-3 hover:bg-gray-100 border-b last:border-b-0">
      <div>
        <p className="font-semibold text-gray-800">{player.full_name}</p>
        <p className="text-sm text-gray-600">
          {player.position || 'N/A'} - {player.team_abbr || 'N/A'}
        </p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onToggleQueuePlayer(player.id)}
          className={`px-3 py-1 text-sm rounded ${isQueued ? 'bg-yellow-500 hover:bg-yellow-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-700' } transition-colors`}
          title={isQueued ? 'Remove from queue' : 'Add to queue'}
        >
          {isQueued ? 'Unqueue' : 'Queue'}
        </button>
        <button
          onClick={() => onPickPlayer(player.id)}
          disabled={!canPick}
          className={`px-4 py-1 text-sm font-medium rounded text-white transition-colors
            ${canPick ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-400 cursor-not-allowed'}`}
          title={canPick ? 'Draft this player' : (isMyTurn ? 'Draft is paused or completed' : 'Not your turn')}
        >
          Pick
        </button>
      </div>
    </li>
  );
};

export default PlayerListItem;