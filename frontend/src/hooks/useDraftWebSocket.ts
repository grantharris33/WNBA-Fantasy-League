import { useEffect, useRef, useState } from 'react';
import type { DraftState } from '../types/draft';

const WS_URL_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface UseDraftWebSocketOptions {
  leagueId: string | null;
  token: string | null;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (event: Event) => void;
}

export const useDraftWebSocket = ({
  leagueId,
  token,
  onOpen,
  onClose,
  onError,
}: UseDraftWebSocketOptions) => {
  const [draftState, setDraftState] = useState<DraftState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const webSocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const isConnectingRef = useRef(false);

  // LOGGING FIX #1: Track state persistence across reconnections
  const lastKnownStateRef = useRef<DraftState | null>(null);
  const connectionCountRef = useRef(0);

  useEffect(() => {
    if (!leagueId || !token) {
      console.log('[WebSocket] Cleaning up - no leagueId or token');
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      reconnectAttemptsRef.current = 0;
      isConnectingRef.current = false;
      return;
    }

    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current || (webSocketRef.current && webSocketRef.current.readyState === WebSocket.CONNECTING)) {
      console.log('[WebSocket] Connection attempt blocked - already connecting');
      return;
    }

    const connectWebSocket = () => {
      // Close existing connection if any
      if (webSocketRef.current && webSocketRef.current.readyState !== WebSocket.CLOSED) {
        console.log('[WebSocket] Closing existing connection before new attempt');
        webSocketRef.current.close();
      }

      connectionCountRef.current += 1;
      isConnectingRef.current = true;
      const wsUrl = `${WS_URL_BASE}/api/v1/draft/ws/${leagueId}?token=${token}`;
      console.log(`[WebSocket] Attempting connection #${connectionCountRef.current} to: ${wsUrl}`);

      const ws = new WebSocket(wsUrl);
      webSocketRef.current = ws;

      ws.onopen = () => {
        console.log(`[WebSocket] Connected successfully (#${connectionCountRef.current})`);
        console.log(`[WebSocket] Current draft state before connection:`, lastKnownStateRef.current ? 'HAS_STATE' : 'NO_STATE');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0; // Reset counter on successful connection
        isConnectingRef.current = false;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data as string);
          console.log(`[WebSocket] Message received (connection #${connectionCountRef.current}):`, message);

          // Validate message structure
          if (!message || !message.event) {
            console.warn('[WebSocket] Invalid message structure:', message);
            return;
          }

          // LOGGING FIX #2: Enhanced message handling with state tracking
          const previousState = lastKnownStateRef.current;
          console.log(`[WebSocket] Processing ${message.event} event. Previous state:`, previousState ? 'HAS_STATE' : 'NO_STATE');

          // Handle ping/pong messages from server
          if (message.type === 'ping') {
            console.log(`[WebSocket] Received ping from server, sending pong`);
            ws.send(JSON.stringify({ type: 'pong' }));
            return;
          }

          // Backend sends messages with "event" field, not "type"
          // Use functional updates to prevent race conditions and preserve existing state
          if (message.event === 'draft_started' || message.event === 'draft_resumed' || message.event === 'draft_paused') {
            if (message.data && typeof message.data === 'object') {
              setDraftState((prevState) => {
                console.log(`[WebSocket] Updating draft state via ${message.event}. Previous:`, prevState ? 'HAS_STATE' : 'NO_STATE', 'New:', message.data ? 'HAS_DATA' : 'NO_DATA');
                lastKnownStateRef.current = message.data;
                return message.data;
              });
            } else {
              console.warn(`[WebSocket] ${message.event} event missing valid data:`, message);
            }
          } else if (message.event === 'pick_made') {
            if (message.data?.draft_state && typeof message.data.draft_state === 'object') {
              console.log(`[WebSocket] PICK_MADE - About to update state. Current state exists:`, !!lastKnownStateRef.current);
              setDraftState((prevState) => {
                console.log(`[WebSocket] PICK_MADE - Setting new draft state. Previous picks:`, prevState?.picks?.length || 0, 'New picks:', message.data.draft_state?.picks?.length || 0);
                const newState = message.data.draft_state;
                lastKnownStateRef.current = newState;
                console.log(`[WebSocket] PICK_MADE - State updated, stored in lastKnownStateRef:`, !!lastKnownStateRef.current);
                return newState;
              });
            } else {
              console.error('[WebSocket] pick_made event missing draft_state:', message);
            }
          } else if (message.event === 'draft_completed') {
            setDraftState(prevState => {
              if (prevState) {
                const newState = { ...prevState, status: 'completed' as const };
                console.log('[WebSocket] Draft completed - updating status');
                lastKnownStateRef.current = newState;
                return newState;
              }
              console.warn('[WebSocket] draft_completed but no previous state');
              return prevState;
            });
          } else if (message.event === 'timer_sync') {
            // Handle timer sync events to keep client timer in sync with backend
            if (message.data && typeof message.data === 'object') {
              setDraftState(prevState => {
                if (prevState && prevState.id === message.data.draft_id) {
                  const updatedState = {
                    ...prevState,
                    seconds_remaining: message.data.seconds_remaining,
                    current_team_id: message.data.current_team_id,
                    status: message.data.status
                  };
                  console.log(`[WebSocket] Timer sync - updating timer to ${message.data.seconds_remaining}s`);
                  lastKnownStateRef.current = updatedState;
                  return updatedState;
                }
                return prevState;
              });
            } else {
              console.warn('[WebSocket] timer_sync event missing valid data:', message);
            }
          } else if (message.event === 'timer_updated') {
            if (message.data?.draft_state && typeof message.data.draft_state === 'object') {
              setDraftState(prevState => {
                // Only update if we have existing state to prevent overwriting with incomplete data
                if (prevState) {
                  const newState = { ...prevState, ...message.data.draft_state };
                  lastKnownStateRef.current = newState;
                  return newState;
                }
                console.log('[WebSocket] Timer update with no previous state - using provided state');
                lastKnownStateRef.current = message.data.draft_state;
                return message.data.draft_state;
              });
            } else {
              console.warn('[WebSocket] timer_updated event missing valid draft_state:', message);
            }
          } else {
            console.log('[WebSocket] Unhandled event:', message.event);
          }
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error, 'Raw data:', event.data);
          // Don't update state on parsing errors to prevent corruption
        }
      };

      ws.onerror = (event) => {
        console.error(`[WebSocket] Error on connection #${connectionCountRef.current}:`, event);
        setIsConnected(false);
        isConnectingRef.current = false;
        onError?.(event);
      };

            ws.onclose = (event) => {
        console.log(`[WebSocket] Disconnected (#${connectionCountRef.current}) - Code: ${event.code}, Reason: ${event.reason}`);
        console.log(`[WebSocket] State at disconnect - Has state:`, !!lastKnownStateRef.current, 'Picks count:', lastKnownStateRef.current?.picks?.length || 0);

        setIsConnected(false);
        // CRITICAL: Preserve current draft state and lastKnownState during disconnect
        // DO NOT clear draftState here - let it remain for the component to use
        console.log(`[WebSocket] Preserving state during disconnect. Draft state will remain available.`);
        webSocketRef.current = null;
        isConnectingRef.current = false;
        onClose?.();

        // Attempt to reconnect with exponential backoff if we haven't exceeded max attempts
        if (leagueId && token && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000); // Cap at 30 seconds

          console.log(`[WebSocket] Scheduling reconnection ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${delay}ms. Will preserve state:`, lastKnownStateRef.current ? 'YES' : 'NO');

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`[WebSocket] Executing reconnection attempt ${reconnectAttemptsRef.current}`);
            connectWebSocket();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('[WebSocket] Max reconnection attempts reached. Please refresh the page.');
        }
      };
    };

    // Initial connection
    console.log(`[WebSocket] Initiating first connection for league ${leagueId}`);
    connectWebSocket();

    return () => {
      console.log('[WebSocket] Cleanup called');
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      isConnectingRef.current = false;

      if (webSocketRef.current && (webSocketRef.current.readyState === WebSocket.OPEN || webSocketRef.current.readyState === WebSocket.CONNECTING)) {
        webSocketRef.current.close();
      }
    };
  // Only leagueId and token should trigger reconnection
  }, [leagueId, token]);

  // LOGGING FIX #3: Expose additional debugging info
  useEffect(() => {
    console.log(`[WebSocket Hook] State changed - Connected: ${isConnected}, HasState: ${draftState ? 'YES' : 'NO'}, StateId: ${draftState?.id || 'N/A'}`);
  }, [draftState, isConnected]);

  // Return both current state and last known state for fallback
  return {
    draftState,
    isConnected,
    // Debugging info
    connectionCount: connectionCountRef.current,
    lastKnownState: lastKnownStateRef.current
  };
};