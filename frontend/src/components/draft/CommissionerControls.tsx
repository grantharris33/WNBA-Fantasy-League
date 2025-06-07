import React, { useState } from 'react';
import { toast } from 'react-toastify';
import api from '../../lib/api';
import type { DraftState } from '../../types/draft';

interface CommissionerControlsProps {
  draftState: DraftState | null;
  currentUserId: number | undefined;
  leagueCommissionerId: number | undefined; // Fetched from league details
  draftId: number | undefined;
  leagueSettings?: { draft_timer_seconds?: number };
  // onAction: (action: 'pause' | 'resume') => void; // Callback after successful API call
}

const CommissionerControls: React.FC<CommissionerControlsProps> = ({
  draftState,
  currentUserId,
  leagueCommissionerId,
  draftId,
  leagueSettings,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showTimerSettings, setShowTimerSettings] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(leagueSettings?.draft_timer_seconds || 60);

  if (!draftState || !draftId || !currentUserId || currentUserId !== leagueCommissionerId) {
    return null; // Not commissioner or draft not loaded
  }

  const canPause = draftState.status === 'active' || draftState.status === 'pending';
  const canResume = draftState.status === 'paused';

  const handleDraftAction = async (action: 'pause' | 'resume') => {
    if (!draftId) {
      toast.error('Draft ID not found for commissioner action.');
      return;
    }
    setIsLoading(true);
    try {
      if (action === 'pause') {
        await api.draft.pauseDraft(draftId);
      } else if (action === 'resume') {
        await api.draft.resumeDraft(draftId);
      }
      // Success toast will be triggered by DraftPage useEffect watching state change from WebSocket
      // toast.success(`Draft ${action} request sent successfully.`); // This might be too early
      console.log(`Draft ${action} request successful.`);
      // onAction?.(action);
    } catch (err) {
      console.error(`Error during draft ${action}:`, err);
      toast.error(err instanceof Error ? err.message : `Unknown error during ${action}.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimerUpdate = async () => {
    if (!draftId) return;

    try {
      setIsLoading(true);
      await api.draft.updateTimer(draftId, timerSeconds);
      toast.success(`Timer updated to ${timerSeconds} seconds`);
      setShowTimerSettings(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update timer');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-3 my-4 bg-red-50 border border-red-200 rounded-md shadow">
      <h3 className="text-lg font-semibold text-red-700 mb-2">Commissioner Controls</h3>
      <div className="flex flex-wrap gap-3">
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

        {/* Timer Settings Button */}
        <button
          onClick={() => setShowTimerSettings(!showTimerSettings)}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:bg-gray-400 transition-colors"
        >
          Timer Settings
        </button>

        {!canPause && !canResume && draftState.status !== 'completed' && (
            <p className="text-sm text-gray-600">Draft is {draftState.status}. No actions available.</p>
        )}
         {draftState.status === 'completed' && (
            <p className="text-sm text-gray-600">Draft is completed. No further actions.</p>
        )}
      </div>

      {/* Timer Settings Panel */}
      {showTimerSettings && (
        <div className="mt-4 p-3 bg-white border border-gray-200 rounded-md">
          <h4 className="text-md font-medium text-gray-700 mb-2">Draft Timer Settings</h4>
          <div className="flex items-center gap-3">
            <label htmlFor="timer-seconds" className="text-sm text-gray-600">
              Seconds per pick:
            </label>
            <input
              id="timer-seconds"
              type="number"
              min="10"
              max="300"
              value={timerSeconds}
              onChange={(e) => setTimerSeconds(parseInt(e.target.value) || 60)}
              className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleTimerUpdate}
              disabled={isLoading || timerSeconds < 10 || timerSeconds > 300}
              className="px-3 py-1 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded disabled:bg-gray-400 transition-colors"
            >
              {isLoading ? 'Updating...' : 'Update'}
            </button>
            <button
              onClick={() => setShowTimerSettings(false)}
              className="px-3 py-1 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded transition-colors"
            >
              Cancel
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Timer must be between 10 and 300 seconds. Changes apply to future picks.
          </p>
        </div>
      )}
    </div>
  );
};

export default CommissionerControls;