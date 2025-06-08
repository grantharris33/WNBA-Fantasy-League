from typing import Dict, List, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Map of league_id -> set of active WebSocket connections (for draft)
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map of game_id -> set of active WebSocket connections (for live games)
        self.live_game_connections: Dict[str, Set[WebSocket]] = {}
        # Map of team_id -> set of active WebSocket connections (for live fantasy scores)
        self.live_team_connections: Dict[int, Set[WebSocket]] = {}
        # Map of user_id -> set of active WebSocket connections (for notifications)
        self.notification_connections: Dict[int, Set[WebSocket]] = {}

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
        print(
            f"[WebSocketManager] Connected to league {league_id}. Total connections: {len(self.active_connections[league_id])}"
        )

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
                print(f"[WebSocketManager] Disconnected from league {league_id}. No connections remaining.")
            else:
                print(
                    f"[WebSocketManager] Disconnected from league {league_id}. Remaining connections: {len(self.active_connections[league_id])}"
                )

    async def broadcast_to_league(self, league_id: int, message: dict):
        """
        Broadcast a message to all connections for a specific league.

        Args:
            league_id: The league ID to broadcast to
            message: The message to broadcast (will be JSON-serialized)
        """
        if league_id not in self.active_connections:
            print(f"[WebSocketManager] No connections for league {league_id} to broadcast to")
            return

        connection_count = len(self.active_connections[league_id])
        print(
            f"[WebSocketManager] Broadcasting {message.get('event', 'unknown')} to {connection_count} connections in league {league_id}"
        )

        # Track failed connections to clean up
        disconnected = set()
        successful_broadcasts = 0

        for connection in self.active_connections[league_id]:
            try:
                await connection.send_json(message)
                successful_broadcasts += 1
            except Exception as e:
                print(f"[WebSocketManager] Failed to send to connection: {e}")
                # If sending fails, mark for disconnection
                disconnected.add(connection)

        # Clean up any failed connections
        for connection in disconnected:
            self.active_connections[league_id].remove(connection)

        # Clean up empty league entries
        if not self.active_connections[league_id]:
            del self.active_connections[league_id]

        print(
            f"[WebSocketManager] Broadcast complete. Successful: {successful_broadcasts}, Failed: {len(disconnected)}"
        )

    async def connect_live_game(self, websocket: WebSocket, game_id: str):
        """
        Connect a WebSocket to a specific live game channel.

        Args:
            websocket: The WebSocket connection to register
            game_id: The game ID to associate this connection with
        """
        await websocket.accept()

        # Create game entry if it doesn't exist
        if game_id not in self.live_game_connections:
            self.live_game_connections[game_id] = set()

        self.live_game_connections[game_id].add(websocket)
        print(
            f"[WebSocketManager] Connected to live game {game_id}. Total connections: {len(self.live_game_connections[game_id])}"
        )

    def disconnect_live_game(self, websocket: WebSocket, game_id: str):
        """
        Disconnect a WebSocket from a live game channel.

        Args:
            websocket: The WebSocket connection to unregister
            game_id: The game ID this connection was associated with
        """
        if game_id in self.live_game_connections:
            if websocket in self.live_game_connections[game_id]:
                self.live_game_connections[game_id].remove(websocket)

            # Clean up empty game entries
            if not self.live_game_connections[game_id]:
                del self.live_game_connections[game_id]
                print(f"[WebSocketManager] Disconnected from live game {game_id}. No connections remaining.")
            else:
                print(
                    f"[WebSocketManager] Disconnected from live game {game_id}. Remaining connections: {len(self.live_game_connections[game_id])}"
                )

    async def broadcast_live_game_update(self, game_id: str, message: dict):
        """
        Broadcast a live game update to all connections for a specific game.

        Args:
            game_id: The game ID to broadcast to
            message: The message to broadcast (will be JSON-serialized)
        """
        if game_id not in self.live_game_connections:
            print(f"[WebSocketManager] No connections for live game {game_id} to broadcast to")
            return

        connection_count = len(self.live_game_connections[game_id])
        print(f"[WebSocketManager] Broadcasting live game update to {connection_count} connections for game {game_id}")

        # Track failed connections to clean up
        disconnected = set()
        successful_broadcasts = 0

        for connection in self.live_game_connections[game_id]:
            try:
                await connection.send_json(message)
                successful_broadcasts += 1
            except Exception as e:
                print(f"[WebSocketManager] Failed to send live game update: {e}")
                disconnected.add(connection)

        # Clean up any failed connections
        for connection in disconnected:
            self.live_game_connections[game_id].remove(connection)

        # Clean up empty game entries
        if not self.live_game_connections[game_id]:
            del self.live_game_connections[game_id]

        print(
            f"[WebSocketManager] Live game broadcast complete. Successful: {successful_broadcasts}, Failed: {len(disconnected)}"
        )

    async def connect_live_team(self, websocket: WebSocket, team_id: int):
        """
        Connect a WebSocket to a specific team's live fantasy score updates.

        Args:
            websocket: The WebSocket connection to register
            team_id: The team ID to associate this connection with
        """
        await websocket.accept()

        # Create team entry if it doesn't exist
        if team_id not in self.live_team_connections:
            self.live_team_connections[team_id] = set()

        self.live_team_connections[team_id].add(websocket)
        print(
            f"[WebSocketManager] Connected to live team {team_id}. Total connections: {len(self.live_team_connections[team_id])}"
        )

    def disconnect_live_team(self, websocket: WebSocket, team_id: int):
        """
        Disconnect a WebSocket from a team's live fantasy score updates.

        Args:
            websocket: The WebSocket connection to unregister
            team_id: The team ID this connection was associated with
        """
        if team_id in self.live_team_connections:
            if websocket in self.live_team_connections[team_id]:
                self.live_team_connections[team_id].remove(websocket)

            # Clean up empty team entries
            if not self.live_team_connections[team_id]:
                del self.live_team_connections[team_id]
                print(f"[WebSocketManager] Disconnected from live team {team_id}. No connections remaining.")
            else:
                print(
                    f"[WebSocketManager] Disconnected from live team {team_id}. Remaining connections: {len(self.live_team_connections[team_id])}"
                )

    async def broadcast_live_team_update(self, team_id: int, message: dict):
        """
        Broadcast a live fantasy score update to all connections for a specific team.

        Args:
            team_id: The team ID to broadcast to
            message: The message to broadcast (will be JSON-serialized)
        """
        if team_id not in self.live_team_connections:
            print(f"[WebSocketManager] No connections for live team {team_id} to broadcast to")
            return

        connection_count = len(self.live_team_connections[team_id])
        print(f"[WebSocketManager] Broadcasting live team update to {connection_count} connections for team {team_id}")

        # Track failed connections to clean up
        disconnected = set()
        successful_broadcasts = 0

        for connection in self.live_team_connections[team_id]:
            try:
                await connection.send_json(message)
                successful_broadcasts += 1
            except Exception as e:
                print(f"[WebSocketManager] Failed to send live team update: {e}")
                disconnected.add(connection)

        # Clean up any failed connections
        for connection in disconnected:
            self.live_team_connections[team_id].remove(connection)

        # Clean up empty team entries
        if not self.live_team_connections[team_id]:
            del self.live_team_connections[team_id]

        print(
            f"[WebSocketManager] Live team broadcast complete. Successful: {successful_broadcasts}, Failed: {len(disconnected)}"
        )

    async def connect_notifications(self, websocket: WebSocket, user_id: int):
        """
        Connect a WebSocket to a specific user's notification channel.

        Args:
            websocket: The WebSocket connection to register
            user_id: The user ID to associate this connection with
        """
        await websocket.accept()

        # Create user entry if it doesn't exist
        if user_id not in self.notification_connections:
            self.notification_connections[user_id] = set()

        self.notification_connections[user_id].add(websocket)
        print(
            f"[WebSocketManager] Connected to notifications for user {user_id}. Total connections: {len(self.notification_connections[user_id])}"
        )

    def disconnect_notifications(self, websocket: WebSocket, user_id: int):
        """
        Disconnect a WebSocket from a user's notification channel.

        Args:
            websocket: The WebSocket connection to unregister
            user_id: The user ID this connection was associated with
        """
        if user_id in self.notification_connections:
            if websocket in self.notification_connections[user_id]:
                self.notification_connections[user_id].remove(websocket)

            # Clean up empty user entries
            if not self.notification_connections[user_id]:
                del self.notification_connections[user_id]
                print(
                    f"[WebSocketManager] Disconnected from notifications for user {user_id}. No connections remaining."
                )
            else:
                print(
                    f"[WebSocketManager] Disconnected from notifications for user {user_id}. Remaining connections: {len(self.notification_connections[user_id])}"
                )

    async def send_notification_to_user(self, user_id: int, notification_data: dict):
        """
        Send a notification to a specific user via WebSocket.

        Args:
            user_id: The user ID to send the notification to
            notification_data: The notification data to send
        """
        if user_id not in self.notification_connections:
            print(f"[WebSocketManager] No notification connections for user {user_id}")
            return

        connection_count = len(self.notification_connections[user_id])
        print(f"[WebSocketManager] Sending notification to {connection_count} connections for user {user_id}")

        message = {"type": "notification", "notification": notification_data}

        # Track failed connections to clean up
        disconnected = set()
        successful_sends = 0

        for connection in self.notification_connections[user_id]:
            try:
                await connection.send_json(message)
                successful_sends += 1
            except Exception as e:
                print(f"[WebSocketManager] Failed to send notification: {e}")
                disconnected.add(connection)

        # Clean up any failed connections
        for connection in disconnected:
            self.notification_connections[user_id].remove(connection)

        # Clean up empty user entries
        if not self.notification_connections[user_id]:
            del self.notification_connections[user_id]

        print(
            f"[WebSocketManager] Notification send complete. Successful: {successful_sends}, Failed: {len(disconnected)}"
        )

    async def broadcast_notification_to_users(self, user_ids: List[int], notification_data: dict):
        """
        Broadcast a notification to multiple users via WebSocket.

        Args:
            user_ids: List of user IDs to send the notification to
            notification_data: The notification data to send
        """
        for user_id in user_ids:
            await self.send_notification_to_user(user_id, notification_data)


# Global connection manager instance
manager = ConnectionManager()
