import React, { useState, useEffect } from 'react';
import { XMarkIcon, StarIcon, UserIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import type { UserTeam, Player } from '../../types';

interface SetStartersModalProps {
  team: UserTeam;
  onSetStarters: (starterPlayerIds: number[]) => void;
  onClose: () => void;
}

const SetStartersModal: React.FC<SetStartersModalProps> = ({ team, onSetStarters, onClose }) => {
  const [selectedStarters, setSelectedStarters] = useState<Player[]>([]);
  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [error, setError] = useState<string | null>(null);

    useEffect(() => {
    const starters: Player[] = [];
    const available: Player[] = [];

    // Use roster_slots if available (new API), otherwise fall back to roster (old API)
    if (team.roster_slots) {
      team.roster_slots.forEach((slot) => {
        if (slot.player) {
          if (slot.is_starter) {
            starters.push(slot.player);
          } else {
            available.push(slot.player);
          }
        }
      });
    } else if (team.roster) {
      // Fallback for backward compatibility - assume first 5 are starters
      const currentStarters = team.roster.slice(0, 5);
      const remaining = team.roster.slice(5);
      starters.push(...currentStarters);
      available.push(...remaining);
    }

    setSelectedStarters(starters);
    setAvailablePlayers(available);
  }, [team.roster_slots, team.roster]);

  const validateStartingLineup = (starters: Player[]): string | null => {
    if (starters.length !== 5) {
      return 'Starting lineup must have exactly 5 players';
    }

    const positions = starters.map(p => p.position).filter(Boolean);
    const guardCount = positions.filter(pos => pos?.includes('G')).length;
    const forwardCenterCount = positions.filter(pos => pos?.includes('F') || pos?.includes('C')).length;

    if (guardCount < 2) {
      return 'Starting lineup must include at least 2 players with Guard (G) position';
    }

    if (forwardCenterCount < 1) {
      return 'Starting lineup must include at least 1 player with Forward (F) or Center (C) position';
    }

    return null;
  };

  const handlePlayerToggle = (player: Player, isCurrentlyStarter: boolean) => {
    if (isCurrentlyStarter) {
      // Remove from starters, add to available
      setSelectedStarters(prev => prev.filter(p => p.id !== player.id));
      setAvailablePlayers(prev => [...prev, player]);
    } else {
      // Add to starters if under limit, remove from available
      if (selectedStarters.length < 5) {
        setSelectedStarters(prev => [...prev, player]);
        setAvailablePlayers(prev => prev.filter(p => p.id !== player.id));
      }
    }
    setError(null);
  };

  const handleSubmit = () => {
    const validationError = validateStartingLineup(selectedStarters);
    if (validationError) {
      setError(validationError);
      return;
    }

    const starterIds = selectedStarters.map(p => p.id);
    onSetStarters(starterIds);
  };

  const renderPlayerCard = (player: Player, isStarter: boolean, canToggle: boolean = true) => (
    <div
      key={player.id}
      className={`border rounded-lg p-3 cursor-pointer transition-all ${
        isStarter
          ? 'border-yellow-400 bg-yellow-50 hover:bg-yellow-100'
          : 'border-gray-200 bg-white hover:bg-gray-50'
      } ${!canToggle && !isStarter ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={() => canToggle && handlePlayerToggle(player, isStarter)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="flex-shrink-0">
            {isStarter ? (
              <StarIconSolid className="h-5 w-5 text-yellow-500" />
            ) : (
              <UserIcon className="h-5 w-5 text-gray-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {player.full_name}
            </p>
            <p className="text-xs text-gray-500">
              {player.position} • {player.team_abbr}
            </p>
          </div>
        </div>
        {isStarter && (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Starter
          </span>
        )}
      </div>
    </div>
  );

  const getPositionCounts = () => {
    const positions = selectedStarters.map(p => p.position).filter(Boolean);
    const guards = positions.filter(pos => pos?.includes('G')).length;
    const forwards = positions.filter(pos => pos?.includes('F')).length;
    const centers = positions.filter(pos => pos?.includes('C')).length;

    return { guards, forwards, centers };
  };

  const { guards, forwards, centers } = getPositionCounts();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
                <StarIcon className="h-6 w-6 text-yellow-500 mr-2" />
                Set Starting Lineup
              </h3>
              <button
                onClick={onClose}
                className="bg-white rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-4 pb-4 sm:px-6 sm:pb-6">
            {/* Position Requirements */}
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <h4 className="text-sm font-medium text-blue-900 mb-2">Position Requirements:</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className={`text-center ${guards >= 2 ? 'text-green-700' : 'text-red-700'}`}>
                  <div className="font-medium">Guards: {guards}/2+</div>
                  <div className="text-xs">Must have ≥2</div>
                </div>
                <div className={`text-center ${forwards >= 1 || centers >= 1 ? 'text-green-700' : 'text-red-700'}`}>
                  <div className="font-medium">Forwards: {forwards}</div>
                  <div className="text-xs">F positions</div>
                </div>
                <div className={`text-center ${forwards >= 1 || centers >= 1 ? 'text-green-700' : 'text-red-700'}`}>
                  <div className="font-medium">Centers: {centers}</div>
                  <div className="text-xs">C positions</div>
                </div>
              </div>
              <div className="mt-2 text-xs text-blue-700">
                Note: Players with F-C or G-F positions count for both position types.
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Invalid Starting Lineup
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Current Starters */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                  <StarIconSolid className="h-5 w-5 text-yellow-500 mr-2" />
                  Starting Lineup ({selectedStarters.length}/5)
                </h4>
                <div className="space-y-2 min-h-64">
                  {selectedStarters.map((player) => renderPlayerCard(player, true))}
                  {selectedStarters.length < 5 && (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center text-gray-500">
                      <StarIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm">Click a player from the bench to add to starters</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Available Players */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                  <UserIcon className="h-5 w-5 text-gray-500 mr-2" />
                  Available Players ({availablePlayers.length})
                </h4>
                <div className="space-y-2 min-h-64">
                  {availablePlayers.map((player) =>
                    renderPlayerCard(player, false, selectedStarters.length < 5)
                  )}
                  {availablePlayers.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <UserIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm">All players are in starting lineup</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={selectedStarters.length !== 5}
              className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm ${
                selectedStarters.length === 5
                  ? 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                  : 'bg-gray-400 cursor-not-allowed'
              }`}
            >
              Save Starting Lineup
            </button>
            <button
              type="button"
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetStartersModal;