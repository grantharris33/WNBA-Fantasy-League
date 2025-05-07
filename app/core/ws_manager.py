from typing import Dict, List, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Map of league_id -> set of active WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, league_id: int):
        """
        Connect a WebSocket to a specific league's draft channel.

        Args:
            websocket: The WebSocket connection to register
            league_id: The league ID to associate this connection with
        """
        await websocket.accept()

        # Create league entry if it doesn't exist
        if league_id not in self.active_connections:
            self.active_connections[league_id] = set()

        self.active_connections[league_id].add(websocket)

    def disconnect(self, websocket: WebSocket, league_id: int):
        """
        Disconnect a WebSocket from a league's draft channel.

        Args:
            websocket: The WebSocket connection to unregister
            league_id: The league ID this connection was associated with
        """
        # Remove connection from league
        if league_id in self.active_connections:
            if websocket in self.active_connections[league_id]:
                self.active_connections[league_id].remove(websocket)

            # Clean up empty league entries
            if not self.active_connections[league_id]:
                del self.active_connections[league_id]

    async def broadcast_to_league(self, league_id: int, message: dict):
        """
        Broadcast a message to all connections for a specific league.

        Args:
            league_id: The league ID to broadcast to
            message: The message to broadcast (will be JSON-serialized)
        """
        if league_id not in self.active_connections:
            return

        # Track failed connections to clean up
        disconnected = set()

        for connection in self.active_connections[league_id]:
            try:
                await connection.send_json(message)
            except Exception:
                # If sending fails, mark for disconnection
                disconnected.add(connection)

        # Clean up any failed connections
        for connection in disconnected:
            self.active_connections[league_id].remove(connection)

        # Clean up empty league entries
        if not self.active_connections[league_id]:
            del self.active_connections[league_id]


# Global connection manager instance
manager = ConnectionManager()
