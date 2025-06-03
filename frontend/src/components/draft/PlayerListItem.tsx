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

  const formatPercentage = (value: number | undefined) => {
    if (value === undefined || value === null) return 'N/A';
    return (value * 100).toFixed(1) + '%';
  };

  const formatStat = (value: number | undefined) => {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(1);
  };

  return (
    <li className="flex justify-between items-center p-4 hover:bg-gray-50 border-b last:border-b-0">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="font-semibold text-gray-800 text-lg">{player.full_name}</p>
            <p className="text-sm text-gray-600">
              {player.position || 'N/A'} - {player.team_abbr || 'N/A'}
            </p>
          </div>
          {player.stats_2024 && (
            <div className="text-right">
              <p className="text-sm font-medium text-blue-600">
                {formatStat(player.stats_2024.fantasy_ppg)} FPPG
              </p>
              <p className="text-xs text-gray-500">
                {player.stats_2024.games_played} GP (2024)
              </p>
            </div>
          )}
        </div>

        {player.stats_2024 && (
          <>
            <div className="grid grid-cols-4 gap-3 text-xs text-gray-600 mb-2">
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatStat(player.stats_2024.ppg)}</p>
                <p>PPG</p>
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatStat(player.stats_2024.rpg)}</p>
                <p>RPG</p>
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatStat(player.stats_2024.apg)}</p>
                <p>APG</p>
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatStat(player.stats_2024.mpg)}</p>
                <p>MPG</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs text-gray-600">
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatPercentage(player.stats_2024.fg_percentage)}</p>
                <p>FG%</p>
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatPercentage(player.stats_2024.three_point_percentage)}</p>
                <p>3P%</p>
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-800">{formatStat(player.stats_2024.spg)} / {formatStat(player.stats_2024.bpg)}</p>
                <p>STL/BLK</p>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="flex flex-col gap-2 ml-4">
        <button
          onClick={() => onToggleQueuePlayer(player.id)}
          className={`px-3 py-1 text-sm rounded ${isQueued ? 'bg-yellow-500 hover:bg-yellow-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'} transition-colors`}
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