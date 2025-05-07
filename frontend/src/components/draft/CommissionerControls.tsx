import React, { useState } from 'react';
import { toast } from 'react-toastify';
import type { DraftState } from '../../types/draft';

interface CommissionerControlsProps {
  draftState: DraftState | null;
  currentUserId: number | undefined;
  leagueCommissionerId: number | undefined; // Fetched from league details
  draftId: number | undefined;
  apiBaseUrl: string;
  authToken: string | null;
  // onAction: (action: 'pause' | 'resume') => void; // Callback after successful API call
}

const CommissionerControls: React.FC<CommissionerControlsProps> = ({
  draftState,
  currentUserId,
  leagueCommissionerId,
  draftId,
  apiBaseUrl,
  authToken,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  if (!draftState || !draftId || !currentUserId || currentUserId !== leagueCommissionerId) {
    return null; // Not commissioner or draft not loaded
  }

  const canPause = draftState.status === 'active' || draftState.status === 'pending';
  const canResume = draftState.status === 'paused';

  const handleDraftAction = async (action: 'pause' | 'resume') => {
    if (!authToken) {
      toast.error('Authentication token not found for commissioner action.');
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/draft/${draftId}/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Failed to ${action} draft` }));
        const errorMsg = errorData.detail || `Could not ${action} draft.`;
        toast.error(errorMsg);
        throw new Error(errorMsg); // Still throw to indicate failure if needed elsewhere
      }
      // Success toast will be triggered by DraftPage useEffect watching state change from WebSocket
      // toast.success(`Draft ${action} request sent successfully.`); // This might be too early
      console.log(`Draft ${action} request successful.`);
      // onAction?.(action);
    } catch (err) {
      console.error(`Error during draft ${action}:`, err);
      // Error already toasted if it was an API error response. This catches network errors etc.
      if (!(err instanceof Error && err.message.includes('Could not'))) { // Avoid double toast for API errors
        toast.error(err instanceof Error ? err.message : `Unknown error during ${action}.`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-3 my-4 bg-red-50 border border-red-200 rounded-md shadow">
      <h3 className="text-lg font-semibold text-red-700 mb-2">Commissioner Controls</h3>
      <div className="flex gap-3">
        {canPause && (
          <button
            onClick={() => handleDraftAction('pause')}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md disabled:bg-gray-400 transition-colors"
          >
            {isLoading ? 'Pausing...' : 'Pause Draft'}
          </button>
        )}
        {canResume && (
          <button
            onClick={() => handleDraftAction('resume')}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md disabled:bg-gray-400 transition-colors"
          >
            {isLoading ? 'Resuming...' : 'Resume Draft'}
          </button>
        )}
        {!canPause && !canResume && draftState.status !== 'completed' && (
            <p className="text-sm text-gray-600">Draft is {draftState.status}. No actions available.</p>
        )}
         {draftState.status === 'completed' && (
            <p className="text-sm text-gray-600">Draft is completed. No further actions.</p>
        )}
      </div>
    </div>
  );
};

export default CommissionerControls;