import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useDraftWebSocket } from '../hooks/useDraftWebSocket';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import type { DraftState, Player } from '../types/draft';
import type { UserTeam, LeagueOut } from '../types';
import DraftStatusBanner from '../components/draft/DraftStatusBanner';
import DraftTimer from '../components/draft/DraftTimer';
import AvailablePlayersPanel from '../components/draft/AvailablePlayersPanel';
import ConfirmationModal from '../components/common/ConfirmationModal';
import DraftLogPanel from '../components/draft/DraftLogPanel';
import PlayerQueuePanel from '../components/draft/PlayerQueuePanel';
import MyTeamPanel from '../components/draft/MyTeamPanel';
import CommissionerControls from '../components/draft/CommissionerControls';

// Use LeagueOut directly instead of custom LeagueDetails
type LeagueDetails = LeagueOut;

const API_BASE_URL = 'http://localhost:8000/api/v1';
const LOCAL_STORAGE_QUEUE_KEY_PREFIX = 'wnbaFantasyPlayerQueue_';

const DraftPage: React.FC = () => {
  const { leagueId: leagueIdFromParams } = useParams<{ leagueId: string }>();
  const { token, user, isAuthenticated } = useAuth(); // Get token and user from AuthContext

  const [initialDraftState, setInitialDraftState] = useState<DraftState | null>(null);
  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [userTeams, setUserTeams] = useState<UserTeam[]>([]);
  const [leagueDetails, setLeagueDetails] = useState<LeagueDetails | null>(null); // Added for commissioner ID
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const leagueId = leagueIdFromParams || null;
  const localStorageQueueKey = leagueId ? `${LOCAL_STORAGE_QUEUE_KEY_PREFIX}${leagueId}` : '';

  const [queuedPlayerIds, setQueuedPlayerIds] = useState<Set<number>>(() => {
    if (!localStorageQueueKey) return new Set<number>();
    const storedQueue = localStorage.getItem(localStorageQueueKey);
    return storedQueue ? new Set(JSON.parse(storedQueue)) : new Set<number>();
  });

  // State for pick confirmation modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [playerToPick, setPlayerToPick] = useState<Player | null>(null);
  const [pickError, setPickError] = useState<string | null>(null); // For errors during pick submission

  // Stabilize callback functions to prevent WebSocket reconnections
  const handleWebSocketError = useCallback((event: Event) => {
    console.error('WebSocket error in DraftPage:', event);
    // Don't clear draft state on WebSocket errors
  }, []);

  const handleWebSocketClose = useCallback(() => {
    console.log('WebSocket closed in DraftPage - maintaining current draft state');
    // Preserve current state during disconnections
  }, []);

  // WebSocket connection managed by the hook
  const { draftState: wsDraftState, isConnected, connectionCount, lastKnownState } = useDraftWebSocket({
    leagueId,
    token,
    onError: handleWebSocketError,
    onClose: handleWebSocketClose
  });

      // DEFENSIVE STATE PRESERVATION: Use persistent ref to never lose state
  const persistentDraftStateRef = useRef<DraftState | null>(null);

  const currentDraftState = (() => {
    // Priority: WebSocket state > Initial API state > WebSocket's last known state > our persistent state
    let selectedState: DraftState | null = null;

    if (wsDraftState) {
      console.log(`[DraftPage] Using WEBSOCKET state (picks: ${wsDraftState.picks?.length || 0})`);
      selectedState = wsDraftState;
    } else if (initialDraftState) {
      console.log(`[DraftPage] Using INITIAL_API state (picks: ${initialDraftState.picks?.length || 0})`);
      selectedState = initialDraftState;
    } else if (lastKnownState) {
      console.log(`[DraftPage] Using WS_FALLBACK state (picks: ${lastKnownState.picks?.length || 0})`);
      selectedState = lastKnownState;
    } else if (persistentDraftStateRef.current) {
      console.log(`[DraftPage] Using PERSISTENT_FALLBACK state (picks: ${persistentDraftStateRef.current.picks?.length || 0})`);
      selectedState = persistentDraftStateRef.current;
    }

    // Always update our persistent ref with the latest good state
    if (selectedState) {
      persistentDraftStateRef.current = selectedState;
      return selectedState;
    }

    console.error('[DraftPage] NO STATE AVAILABLE - this will cause blank page');
    return null;
  })();

  // LOGGING FIX #3: Track state changes and component renders
  useEffect(() => {
    console.log(`[DraftPage] State update - WS: ${wsDraftState ? 'HAS' : 'NO'}, Initial: ${initialDraftState ? 'HAS' : 'NO'}, LastKnown: ${lastKnownState ? 'HAS' : 'NO'}, Current: ${currentDraftState ? 'HAS' : 'NO'}, Connected: ${isConnected}, Connection#: ${connectionCount}`);

    if (!currentDraftState && isConnected) {
      console.error(`[DraftPage] BLANK PAGE CONDITION DETECTED! Connected but no current state. WS state: ${!!wsDraftState}, Initial: ${!!initialDraftState}, LastKnown: ${!!lastKnownState}`);
    }
  }, [wsDraftState, initialDraftState, lastKnownState, currentDraftState, isConnected, connectionCount]);

  // The draft_id should come from the current draft state
  const draftId = currentDraftState?.id;

  // Ref to store previous draft state for comparison to trigger toasts
  const prevDraftStateRef = useRef<DraftState | null>(null);

  // Effect to save queue to localStorage whenever it changes
  useEffect(() => {
    if (localStorageQueueKey) {
      localStorage.setItem(localStorageQueueKey, JSON.stringify(Array.from(queuedPlayerIds)));
    }
  }, [queuedPlayerIds, localStorageQueueKey]);

  // Effect for WebSocket event-based toasts and UI updates
  useEffect(() => {
    if (currentDraftState && prevDraftStateRef.current) {
      // Pick Made Toast and Player Removal
      if (currentDraftState.picks.length > prevDraftStateRef.current.picks.length) {
        const newPick = currentDraftState.picks[currentDraftState.picks.length - 1];
        toast.success(`${newPick.team_name} picked ${newPick.player_name}!`);

        // Remove picked player from available players list
        setAvailablePlayers(prev => prev.filter(player => player.id !== newPick.player_id));

        // Remove from queue if the picked player was queued
        setQueuedPlayerIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(newPick.player_id);
          return newSet;
        });
      }
      // Draft Paused Toast
      if (currentDraftState.status === 'paused' && prevDraftStateRef.current.status !== 'paused') {
        toast.warn('Draft Paused by Commissioner.');
      }
      // Draft Resumed Toast
      if (currentDraftState.status === 'active' && prevDraftStateRef.current.status === 'paused') {
        toast.info('Draft Resumed.');
      }
      // Draft Completed Toast
      if (currentDraftState.status === 'completed' && prevDraftStateRef.current.status !== 'completed') {
        toast.info('The Draft has been completed!');
      }
    }
    // Update previous state ref *after* comparisons
    prevDraftStateRef.current = currentDraftState;
  }, [currentDraftState]);

  // Add a ref to track if we've already attempted initial fetch
  const hasAttemptedInitialFetch = useRef(false);

  // CRITICAL FIX #3: Detect and recover from blank page conditions
  const blankPageRecoveryAttempts = useRef(0);
  const maxBlankPageRecoveryAttempts = 3;

  useEffect(() => {
    // If we're connected but have no state after a reasonable time, force recovery
    if (isConnected && !currentDraftState && blankPageRecoveryAttempts.current < maxBlankPageRecoveryAttempts) {
      const timer = setTimeout(() => {
        if (isConnected && !currentDraftState) {
          blankPageRecoveryAttempts.current += 1;
          console.log(`[DraftPage] BLANK PAGE RECOVERY ATTEMPT #${blankPageRecoveryAttempts.current}: Connected but no state, forcing API refresh`);

          // Force a fresh API call to get draft state
          if (leagueId) {
            api.leagues.getDraftState(parseInt(leagueId))
              .then((draftStateData) => {
                console.log('[DraftPage] Recovery: Got fresh draft state from API', draftStateData);
                setInitialDraftState(draftStateData);
              })
              .catch((err) => {
                console.error('[DraftPage] Recovery: Failed to fetch fresh draft state', err);
              });
          }
        }
      }, 2000); // Wait 2 seconds before attempting recovery

      return () => clearTimeout(timer);
    }
  }, [isConnected, currentDraftState, leagueId]);

  useEffect(() => {
    if (!leagueId || !isAuthenticated) {
      setIsLoading(false);
      if (!isAuthenticated) setError('User not authenticated.');
      return;
    }

    // Prevent multiple simultaneous fetches
    if (hasAttemptedInitialFetch.current) {
      return;
    }

    hasAttemptedInitialFetch.current = true;

    const fetchData = async () => {
      // Don't set loading if we already have current draft state to prevent blank page
      const hasExistingState = initialDraftState !== null || wsDraftState !== null;
      if (!hasExistingState) {
        setIsLoading(true);
      }
      setError(null);
      setPickError(null); // Reset pick error on full fetch

      try {
        // Fetch League Details (for commissioner_id)
        const leagueData: LeagueDetails = await api.leagues.getById(parseInt(leagueId));
        setLeagueDetails(leagueData);

        // 1. Fetch initial draft state for the league - always fetch to have fallback
        const draftStateData: DraftState = await api.leagues.getDraftState(parseInt(leagueId));
        setInitialDraftState(draftStateData);

        // 2. Fetch available players
        const playersData = await api.roster.getFreeAgents(parseInt(leagueId));
        setAvailablePlayers(playersData.items || playersData); // Adjust based on actual API response structure

        // 3. Fetch user's teams in this league
        const allUserTeams: UserTeam[] = await api.users.getMyTeams();
        setUserTeams(allUserTeams.filter(team => team.league_id?.toString() === leagueId));

      } catch (err) {
        console.error('Error fetching draft page data:', err);
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        setError(errorMessage);
        toast.error(`Data fetch error: ${errorMessage}. Please try refreshing the page.`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [leagueId, isAuthenticated]);

  const handleTimerExpire = () => {
    console.log("Draft timer expired! Backend should handle auto-pick.");
    toast.warn("Time is up for the current pick!");
  };

  const openPickConfirmationModal = (playerId: number) => {
    const player = availablePlayers.find(p => p.id === playerId) ||
                   Array.from(queuedPlayerIds).map(id => availablePlayers.find(p => p.id === id)).find(p => p?.id === playerId);
    if (player) {
      setPlayerToPick(player);
      setIsModalOpen(true);
      setPickError(null); // Clear previous pick errors
    }
  };

  const handleConfirmPick = async () => {
    if (!playerToPick || !draftId || !currentDraftState || currentDraftState.status !== 'active') {
      const errorMsg = 'Cannot make a pick: Draft is not active, player not selected, or draft ID is missing.';
      setPickError(errorMsg);
      toast.error(errorMsg);
      setIsModalOpen(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/draft/${draftId}/pick`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ player_id: playerToPick.id }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Pick failed with status: ' + response.status }));
        throw new Error(errorData.detail || 'Failed to make pick.');
      }
      // Success: WebSocket `pick_made` event should handle UI updates for draft log & available players.
      // No need to manually update availablePlayers here if WS is reliable.
      console.log(`Player ${playerToPick.full_name} picked successfully.`);
      // Remove from queue if drafted
      setQueuedPlayerIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(playerToPick.id);
        return newSet;
      });
      // Toast notification for success can be added in Task 14-J

    } catch (err) {
      console.error('Error making pick:', err);
      setPickError(err instanceof Error ? err.message : 'An unknown error occurred making pick.');
      // Error will be displayed near modal or via toast (Task 14-J)
    } finally {
      setIsModalOpen(false);
      setPlayerToPick(null);
    }
  };

  // Placeholder for queue toggle (Task 14-G)
  const handleToggleQueuePlayer = useCallback((playerId: number) => {
    setQueuedPlayerIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(playerId)) {
        newSet.delete(playerId);
      } else {
        newSet.add(playerId);
      }
      // console.log('Updated queue:', newSet);
      // localStorage persistence will be in Task 14-G
      return newSet;
    });
  }, []);

  // CRITICAL DEBUGGING: Log why we might show loading/error states
  const debugInfo = {
    isLoading,
    hasCurrentDraftState: !!currentDraftState,
    isConnected,
    hasError: !!error,
    connectionCount,
    hasWsState: !!wsDraftState,
    hasInitialState: !!initialDraftState,
    hasLastKnownState: !!lastKnownState
  };

  // Only show loading if we truly have no state AND are not connected
  if (isLoading && !currentDraftState && !isConnected) {
    console.log('[DraftPage] Showing loading state:', debugInfo);
    return <div className="p-4 text-center">Loading draft room...</div>;
  }

  // Show error only if we have no fallback state
  if (error && !currentDraftState) {
    console.log('[DraftPage] Showing error state:', debugInfo);
    return (
      <div className="p-4 text-center">
        <div className="text-red-600 mb-4">Error: {error}</div>
        {isConnected && <div className="text-blue-600 mb-2">WebSocket connected - waiting for data...</div>}
        <div className="text-xs text-gray-500 mt-2">Debug: {JSON.stringify(debugInfo)}</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Reload Page
        </button>
      </div>
    );
  }

  // Show waiting message only if we have no state at all
  if (!currentDraftState && !isConnected) {
    console.log('[DraftPage] Showing disconnected no-state condition:', debugInfo);
    return (
      <div className="p-4 text-center">
        <div className="mb-4">Draft information not available. Waiting for connection or initial data...</div>
        <div className="text-xs text-gray-500 mt-2">Debug: {JSON.stringify(debugInfo)}</div>
        <button
          onClick={() => {
            setError(null);
            window.location.reload();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Reload Page
        </button>
      </div>
    );
  }

  // Show connection status if connected but no data yet
  if (!currentDraftState && isConnected) {
    console.log('[DraftPage] Showing connected no-state condition (THIS IS THE BLANK PAGE ISSUE):', debugInfo);
    return (
      <div className="p-4 text-center">
        <div className="mb-4">Connected to draft. Waiting for data...</div>
        <div className="text-sm text-gray-600">If this persists, try reloading the page.</div>
        <div className="text-xs text-gray-500 mt-2">Debug: {JSON.stringify(debugInfo)}</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Reload Page
        </button>
      </div>
    );
  }

  // Last resort - should rarely hit this
  if (!currentDraftState) {
    console.error('[DraftPage] CRITICAL: No state available despite all fallbacks:', debugInfo);
    return (
      <div className="p-4 text-center">
        <div className="mb-4">No draft data loaded.</div>
        <div className="text-xs text-gray-500 mt-2">Debug: {JSON.stringify(debugInfo)}</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Reload Page
        </button>
      </div>
    );
  }

  const userTeamInThisDraft = userTeams.length > 0 ? userTeams[0] : null; // Simplification: assumes one team per user per league
  const isMyTurnForQueuePick = userTeamInThisDraft?.id === currentDraftState.current_team_id;

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <header className="bg-gray-800 text-white p-3 sticky top-0 z-50 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-lg md:text-xl font-bold">Draft Room - League {leagueId} (Draft ID: {draftId || 'N/A'})</h1>
            {user && <div className="text-xs md:text-sm">User: {user.email} (ID: {user.id})</div>}
        </div>
      </header>

      <DraftStatusBanner draftState={currentDraftState} userTeamId={userTeamInThisDraft?.id} />

      {user?.id && leagueDetails?.commissioner_id === user.id && (
        <CommissionerControls
            draftState={currentDraftState}
            currentUserId={user.id}
            leagueCommissionerId={leagueDetails.commissioner_id}
            draftId={draftId}
            apiBaseUrl={API_BASE_URL}
            authToken={token}
            leagueSettings={leagueDetails.settings}
        />
      )}

      <main className="container mx-auto p-4 flex-grow grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Left column for available players and potentially user queue */}
          <DraftTimer
            secondsRemainingFromState={currentDraftState.seconds_remaining}
            draftStatus={currentDraftState.status}
            onTimerExpire={handleTimerExpire}
          />
          {pickError && <div className="p-3 bg-red-100 text-red-700 border border-red-300 rounded">Pick Error: {pickError}</div>}
          <AvailablePlayersPanel
            allPlayers={availablePlayers}
            draftState={currentDraftState}
            userTeamId={userTeamInThisDraft?.id}
            onPickPlayer={openPickConfirmationModal}
            queuedPlayerIds={queuedPlayerIds}
            onToggleQueuePlayer={handleToggleQueuePlayer}
          />
        </div>

        <div className="lg:col-span-1 space-y-6">
          {/* Right column for draft log and my team */}
          <PlayerQueuePanel
            queuedPlayerIds={queuedPlayerIds}
            allPlayers={availablePlayers} // Pass all available players to find details
            onToggleQueuePlayer={handleToggleQueuePlayer}
            onPickFromQueue={openPickConfirmationModal} // Reuse pick confirmation
            isMyTurn={isMyTurnForQueuePick}
            draftStatus={currentDraftState.status}
          />
          <DraftLogPanel picks={currentDraftState.picks} />

          {userTeamInThisDraft && currentDraftState && (
            <MyTeamPanel
              myTeamId={userTeamInThisDraft.id}
              teamName={userTeamInThisDraft.name}
              allPicks={currentDraftState.picks}
            />
          )}
          {/* Placeholder if no team, or if team panel handles this internally */}
          {!userTeamInThisDraft && isAuthenticated && !isLoading && (
             <div className="p-4 border rounded shadow bg-white">
               <h2 className="text-xl font-semibold mb-3">My Team</h2>
               <p className="text-gray-500 italic">You do not appear to have a team in this league's draft.</p>
             </div>
          )}
        </div>
      </main>

      {/* Footer or other global elements if any */}
      {/* TODO: Task 14-G: PlayerQueuePanel (Client-Side) - Could be a floating panel or separate section */}
      {/* TODO: Task 14-I: CommissionerControls - Could be near admin actions area or status banner */}

      {playerToPick && (
        <ConfirmationModal
          isOpen={isModalOpen}
          title={`Confirm Pick: ${playerToPick.full_name}`}
          message={`Are you sure you want to draft ${playerToPick.full_name} (${playerToPick.position || 'N/A'})?`}
          onConfirm={handleConfirmPick}
          onCancel={() => {
            setIsModalOpen(false);
            setPlayerToPick(null);
            setPickError(null);
          }}
          confirmButtonText="Draft Player"
        />
      )}
    </div>
  );
};

export default DraftPage;