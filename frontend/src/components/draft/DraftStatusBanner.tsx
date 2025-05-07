import React from 'react';
import type { DraftState } from '../../types/draft';

interface DraftStatusBannerProps {
  draftState: DraftState | null;
  userTeamId?: number | null; // To highlight if it's the user's turn
  // We might need to map team_id to team_name if not readily available in draftState.current_team_name
}

const DraftStatusBanner: React.FC<DraftStatusBannerProps> = ({ draftState, userTeamId }) => {
  if (!draftState) {
    return (
      <div className="p-4 bg-gray-100 border-b border-gray-300 text-center">
        Loading draft status...
      </div>
    );
  }

  const { current_round, status, current_team_id, picks } = draftState;

  // Overall pick number is the count of picks made + 1 for the current pick.
  const overallPickNumber = picks.length + 1;

  const teamOnClock = `Team ID: ${current_team_id}`;
  const isMyTurn = userTeamId === current_team_id && status === 'active';

  let statusText = status.toUpperCase();
  if (status === 'active') statusText = "LIVE";
  if (status === 'completed') statusText = "DRAFT COMPLETED";
  if (status === 'pending') statusText = "DRAFT PENDING";
  if (status === 'paused') statusText = "DRAFT PAUSED";

  return (
    <div className={`p-4 border-b border-gray-300 text-center ${isMyTurn ? 'bg-yellow-200' : 'bg-gray-100'}`}>
      <div className="flex flex-col sm:flex-row sm:justify-around items-center gap-2 sm:gap-4">
        <div className="text-center">
          <span className="block text-xs sm:text-sm text-gray-600">Status</span>
          <span className={`block text-lg sm:text-xl font-bold ${isMyTurn ? 'text-yellow-700' : 'text-gray-800'}`}>{statusText}</span>
        </div>
        <div className="text-center">
          <span className="block text-xs sm:text-sm text-gray-600">Round</span>
          <span className={`block text-lg sm:text-xl font-bold ${isMyTurn ? 'text-yellow-700' : 'text-gray-800'}`}>{current_round}</span>
        </div>
        <div className="text-center">
          <span className="block text-xs sm:text-sm text-gray-600">Overall Pick</span>
          <span className={`block text-lg sm:text-xl font-bold ${isMyTurn ? 'text-yellow-700' : 'text-gray-800'}`}>{overallPickNumber}</span>
        </div>
        <div className="text-center">
          <span className="block text-xs sm:text-sm text-gray-600">Team on Clock</span>
          <span className={`block sm:text-lg font-semibold ${isMyTurn ? 'text-yellow-700 animate-pulse' : 'text-gray-800'}`}>
            {teamOnClock} {isMyTurn && "(YOUR PICK!)"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DraftStatusBanner;