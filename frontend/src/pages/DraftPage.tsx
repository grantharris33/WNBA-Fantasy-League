import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useDraftWebSocket } from '../hooks/useDraftWebSocket';
import type { DraftState, Player, UserTeam, League, DraftPick } from '../types/draft';
import DraftStatusBanner from '../components/draft/DraftStatusBanner';
import DraftTimer from '../components/draft/DraftTimer';
import AvailablePlayersPanel from '../components/draft/AvailablePlayersPanel';
import ConfirmationModal from '../components/common/ConfirmationModal';
import DraftLogPanel from '../components/draft/DraftLogPanel';
import PlayerQueuePanel from '../components/draft/PlayerQueuePanel';
import MyTeamPanel from '../components/draft/MyTeamPanel';
import CommissionerControls from '../components/draft/CommissionerControls';
// import { useAuth } from '../contexts/AuthContext'; // Assuming AuthContext exists

// Placeholder for AuthContext hook until its actual implementation is known
const useAuth = () => {
  // Replace with actual AuthContext logic
  // For now, returning a mock token and user for development
  const mockToken = localStorage.getItem('authToken'); // Or some other mock
  const mockUser = { id: 1, email: 'user@example.com' }; // Mock user with id
  return { token: mockToken, user: mockUser, isAuthenticated: !!mockToken };
};

// Define a basic League type for now, assuming it has commissioner_id
// This should align with backend's LeagueOut schema eventually
interface LeagueDetails extends League {
    commissioner_id?: number; // Assuming this will be added to backend LeagueOut
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
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

  // WebSocket connection managed by the hook
  const { draftState: wsDraftState, isConnected } = useDraftWebSocket({
    leagueId,
    token,
  });

  // Derived draft state (prefer WebSocket state if connected and available)
  const currentDraftState = wsDraftState || initialDraftState;
  // The draft_id should come from the initial draft state fetched for the league.
  const draftId = currentDraftState?.id;

  // Ref to store previous draft state for comparison to trigger toasts
  const prevDraftStateRef = useRef<DraftState | null>(null);

  // Effect to save queue to localStorage whenever it changes
  useEffect(() => {
    if (localStorageQueueKey) {
      localStorage.setItem(localStorageQueueKey, JSON.stringify(Array.from(queuedPlayerIds)));
    }
  }, [queuedPlayerIds, localStorageQueueKey]);

  // Effect for WebSocket event-based toasts
  useEffect(() => {
    if (currentDraftState && prevDraftStateRef.current) {
      // Pick Made Toast
      if (currentDraftState.picks.length > prevDraftStateRef.current.picks.length) {
        const newPick = currentDraftState.picks[currentDraftState.picks.length - 1];
        toast.success(`${newPick.team_name} picked ${newPick.player_name}!`);
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

  useEffect(() => {
    if (!leagueId || !isAuthenticated) {
      setIsLoading(false);
      if (!isAuthenticated) setError('User not authenticated.');
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      setPickError(null); // Reset pick error on full fetch
      try {
        // Fetch League Details (for commissioner_id)
        const leagueDetailsResponse = await fetch(`${API_BASE_URL}/leagues/${leagueId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!leagueDetailsResponse.ok) {
          toast.error(`Failed to fetch league details: ${leagueDetailsResponse.statusText}`);
          throw new Error(`Failed to fetch league details (LID: ${leagueId}): ${leagueDetailsResponse.statusText}`);
        }
        const leagueData: LeagueDetails = await leagueDetailsResponse.json();
        setLeagueDetails(leagueData);
        // TODO: The backend LeagueOut schema needs to include commissioner_id
        // if (!leagueData.commissioner_id) console.warn('Commissioner ID not found in league details!');

        // 1. Fetch initial draft state for the league
        // Assuming an endpoint like /leagues/{leagueId}/draft/state or similar
        // Story-14 indicates GET /api/v1/draft/{draft_id}/state.
        // We need to resolve leagueId to draft_id first, or the backend API needs adjustment.
        // For now, let's assume a direct fetch of draft state using leagueId as a proxy, which might need adjustment.
        // A more robust solution would be an endpoint GET /leagues/{leagueId}/draft-details returning the active draft_id.
        // Let's try to fetch using an assumed endpoint that gives draft state by leagueId.
        // Or, if the backend has a convention, like draft_id is numerically same as league_id for single draft per league.

        // Tentative: Assuming the draft ID needs to be fetched or is known. Let's use leagueId as a placeholder for draftId for now
        // for the initial fetch, or adjust if a specific endpoint is confirmed.
        // The WebSocket connects with leagueId, but API calls for state/pick use draft_id.
        // This part is tricky without backend clarification from Story-9.
        // Let's assume we first get league details which may contain the active draft_id.

        // Step 1: Fetch league details to get draft_id (hypothetical)
        // For now, we directly call /draft/{draft_id}/state assuming draft_id = leagueId, this is likely wrong.
        // A more realistic approach would be: GET /leagues/{leagueId} -> get active_draft_id
        // then GET /draft/{active_draft_id}/state

        // For now, let's proceed with a placeholder that GET /draft/{leagueId}/state works
        // This will likely need to be changed based on actual backend API for getting initial draft state via league_id

        const fetchedDraftId = leagueId; // Placeholder assumption, effectively using leagueId as draftId for the initial fetch URL

        if (fetchedDraftId) {
          const draftStateResponse = await fetch(`${API_BASE_URL}/draft/${fetchedDraftId}/state`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!draftStateResponse.ok) {
            toast.error(`Failed to fetch draft state: ${draftStateResponse.statusText}`);
            throw new Error(`Failed to fetch draft state (LID: ${leagueId}): ${draftStateResponse.statusText} (status: ${draftStateResponse.status})`);
          }
          const draftStateData: DraftState = await draftStateResponse.json();
          setInitialDraftState(draftStateData);
        } else {
          throw new Error('Could not determine draft ID for the league.');
        }

        // 2. Fetch available players
        const playersResponse = await fetch(`${API_BASE_URL}/leagues/${leagueId}/free-agents`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!playersResponse.ok) {
          toast.error('Failed to fetch available players.');
          throw new Error('Failed to fetch available players');
        }
        const playersData = await playersResponse.json(); // Assuming it returns Player[] or { items: Player[] }
        setAvailablePlayers(playersData.items || playersData); // Adjust based on actual API response structure

        // 3. Fetch user's teams in this league
        const userTeamsResponse = await fetch(`${API_BASE_URL}/users/me/teams`, { // This endpoint might need ?league_id=leagueId filter
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!userTeamsResponse.ok) {
          toast.error('Failed to fetch user teams.');
          throw new Error('Failed to fetch user teams');
        }
        const allUserTeams: UserTeam[] = await userTeamsResponse.json();
        setUserTeams(allUserTeams.filter(team => team.league_id.toString() === leagueId));

      } catch (err) {
        console.error('Error fetching draft page data:', err);
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        setError(errorMessage);
        // toast.error(`Data fetch error: ${errorMessage}`); // Already handled by general error display
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [leagueId, token, isAuthenticated]);

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

  if (isLoading) return <div className="p-4 text-center">Loading draft room...</div>;
  if (error) return <div className="p-4 text-center text-red-600">Error: {error}</div>;
  if (!currentDraftState && !isConnected) return <div className="p-4 text-center">Draft information not available. Waiting for connection or initial data...</div>;
  if (!currentDraftState && isConnected) return <div className="p-4 text-center">Connected to draft. Waiting for data...</div>;
  if (!currentDraftState) return <div className="p-4 text-center">No draft data loaded.</div>; // Should ideally be covered by previous conditions

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