import React, { useState } from 'react';
import { WaiverPlayer } from '../../types';
import WaiverClaimModal from './WaiverClaimModal';

interface WaiverPlayerListProps {
  players: WaiverPlayer[];
  teamId: number;
  onClaimSubmitted: () => void;
}

const WaiverPlayerList: React.FC<WaiverPlayerListProps> = ({
  players,
  teamId,
  onClaimSubmitted
}) => {
  const [selectedPlayer, setSelectedPlayer] = useState<WaiverPlayer | null>(null);
  const [showClaimModal, setShowClaimModal] = useState(false);

  const handleClaimPlayer = (player: WaiverPlayer) => {
    setSelectedPlayer(player);
    setShowClaimModal(true);
  };

  const handleClaimSubmitted = () => {
    setShowClaimModal(false);
    setSelectedPlayer(null);
    onClaimSubmitted();
  };

  const formatWaiverExpiration = (expirationDate: string) => {
    const now = new Date();
    const expiry = new Date(expirationDate);
    const diffMs = expiry.getTime() - now.getTime();
    
    if (diffMs <= 0) {
      return 'Expired';
    }
    
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 24) {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ${diffHours % 24}h`;
    } else if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m`;
    } else {
      return `${diffMinutes}m`;
    }
  };

  if (players.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No players currently on waivers</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Player
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Position
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Team
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Waiver Expires
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {players.map((player) => (
              <tr key={player.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {player.full_name}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {player.position || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {player.team_abbr || 'FA'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {player.waiver_expires_at ? (
                    <span className="text-red-600 font-medium">
                      {formatWaiverExpiration(player.waiver_expires_at)}
                    </span>
                  ) : (
                    'N/A'
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    onClick={() => handleClaimPlayer(player)}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded-md text-sm font-medium transition-colors"
                  >
                    Claim
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showClaimModal && selectedPlayer && (
        <WaiverClaimModal
          player={selectedPlayer}
          teamId={teamId}
          onClose={() => setShowClaimModal(false)}
          onClaimSubmitted={handleClaimSubmitted}
        />
      )}
    </>
  );
};

export default WaiverPlayerList;