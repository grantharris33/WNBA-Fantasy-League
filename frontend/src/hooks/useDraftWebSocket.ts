import { useEffect, useRef, useState } from 'react';
import type { DraftState } from '../types/draft';

const WS_URL_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/draft/ws';

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

  useEffect(() => {
    if (!leagueId || !token) {
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
      return;
    }

    const wsUrl = `${WS_URL_BASE}/${leagueId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    webSocketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      onOpen?.();
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data as string);
        console.log('WebSocket message received:', message);

        // Backend sends messages with "event" field, not "type"
        // Initial full state often comes with 'draft_started' or similar
        // Subsequent messages update parts of it or are specific events
        if (message.event === 'draft_started' || message.event === 'draft_resumed' || message.event === 'draft_paused') {
          setDraftState(message.data);
        } else if (message.event === 'pick_made') {
          setDraftState(message.data.draft_state);
          // Potentially also emit the pick itself for toast notifications, etc.
        } else if (message.event === 'draft_completed') {
          if (draftState) {
            setDraftState({ ...draftState, status: 'completed' });
          }
          // Handle other completion logic
        }
        // Add more specific message type handling as needed
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setIsConnected(false);
      onError?.(event);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setDraftState(null); // Clear state on disconnect
      webSocketRef.current = null;
      onClose?.();
    };

    return () => {
      if (webSocketRef.current && (webSocketRef.current.readyState === WebSocket.OPEN || webSocketRef.current.readyState === WebSocket.CONNECTING)) {
        webSocketRef.current.close();
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leagueId, token, onOpen, onClose, onError]);

  // const sendPick = (playerId: number) => {
  //   if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
  //     // The backend expects a POST request for picks, not a WebSocket message.
  //     // This function might be better placed in an API service class.
  //     // Story-14 (3. Backend Interaction) confirms POST for pick.
  //     console.warn('sendPick over WebSocket is not standard for this backend. Use API call.');
  //     // Example: webSocketRef.current.send(JSON.stringify({ type: 'make_pick', payload: { playerId } }));
  //   } else {
  //     console.error('WebSocket not connected. Cannot send pick.');
  //   }
  // };

  // Return sendPick later if it's adapted for other WS messages or if some actions are sent via WS
  return { draftState, isConnected };
};