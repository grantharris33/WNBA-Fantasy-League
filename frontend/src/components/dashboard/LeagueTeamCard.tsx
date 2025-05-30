import React from 'react';
import { Link } from 'react-router-dom';
import type { UserTeam, DraftState } from '../../types'; // Added DraftState for props

// Define the structure for draft status info passed as a prop
interface DraftStatusInfo {
  leagueId: number;
  status: DraftState['status'] | 'loading' | 'error';
  error?: string;
}

interface LeagueTeamCardProps {
  team: UserTeam;
  draftStatusInfo?: DraftStatusInfo; // Changed from draftStatus, made optional
}

const LeagueTeamCard: React.FC<LeagueTeamCardProps> = ({ team, draftStatusInfo }) => {
  const leagueName = team.league?.name || `League ID: ${team.league_id}`;

  let draftButtonText = "View Draft";
  let isDraftButtonDisabled = false;
  let draftStatusMessage = "Loading draft status...";

  if (draftStatusInfo) {
    if (draftStatusInfo.status === 'loading') {
      draftButtonText = "Checking Draft...";
      isDraftButtonDisabled = true;
      draftStatusMessage = "Loading draft status...";
    } else if (draftStatusInfo.status === 'error') {
      draftButtonText = "View Draft"; // Or "Draft Status Error"
      isDraftButtonDisabled = false; // Or true, depending on desired UX
      draftStatusMessage = `Error: ${draftStatusInfo.error || 'Could not load draft status.'}`;
    } else {
      // Valid status: 'pending' | 'active' | 'paused' | 'completed'
      draftStatusMessage = `Draft: ${draftStatusInfo.status.charAt(0).toUpperCase() + draftStatusInfo.status.slice(1)}`;
      switch (draftStatusInfo.status) {
        case 'pending':
          draftButtonText = "Draft Not Started";
          isDraftButtonDisabled = true; // Or link to a page showing draft time
          break;
        case 'active':
          draftButtonText = "Enter Draft Room";
          isDraftButtonDisabled = false;
          break;
        case 'paused':
          draftButtonText = "Draft Paused";
          isDraftButtonDisabled = true; // Or link to draft room (read-only)
          break;
        case 'completed':
          draftButtonText = "View Draft Results";
          isDraftButtonDisabled = false;
          break;
        default:
          draftButtonText = "View Draft";
          isDraftButtonDisabled = false;
      }
    }
  } else {
    // Fallback if draftStatusInfo is not yet available
    draftButtonText = "View Draft (Status N/A)";
    isDraftButtonDisabled = false;
    draftStatusMessage = "Draft status unavailable.";
  }

  return (
    <div className="bg-white shadow-lg rounded-lg p-6 flex flex-col justify-between">
      <div>
        <h3 className="text-xl font-semibold mb-2">{leagueName}</h3>
        <p className="text-gray-700 mb-1">Your Team: <span className="font-medium">{team.name}</span></p>
        <p className="text-sm text-gray-500 mb-4">{draftStatusMessage}</p>
      </div>

      <div className="mt-4 flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-2">
        <Link
          to={`/draft/${team.league_id}`}
          className={`w-full sm:w-auto text-center px-4 py-2 rounded-md font-medium
                      ${isDraftButtonDisabled
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-500 text-white hover:bg-blue-600'}`}
          aria-disabled={isDraftButtonDisabled}
          onClick={(e) => isDraftButtonDisabled && e.preventDefault()}
        >
          {draftButtonText}
        </Link>
        <Link
          to={`/team/${team.id}`}
          className="w-full sm:w-auto text-center bg-green-500 text-white hover:bg-green-600 px-4 py-2 rounded-md font-medium"
        >
          Manage Team
        </Link>
      </div>
    </div>
  );
};

export default LeagueTeamCard;