from fastapi import WebSocket
import json


class ConnectionManager:
    """
    Manages WebSocket connections per room.
    Each room (main, MI, CSK) has its own set of connected clients.
    """

    def __init__(self):
        # room_name -> list of (websocket, user_info) tuples
        self.active_connections: dict[str, list[tuple[WebSocket, dict]]] = {}

    async def connect(self, websocket: WebSocket, room_name: str, user_info: dict):
        await websocket.accept()
        if room_name not in self.active_connections:
            self.active_connections[room_name] = []
        self.active_connections[room_name].append((websocket, user_info))

    def disconnect(self, websocket: WebSocket, room_name: str):
        if room_name in self.active_connections:
            self.active_connections[room_name] = [
                (ws, info) for ws, info in self.active_connections[room_name]
                if ws != websocket
            ]

    async def broadcast_to_room(self, room_name: str, message: dict):
        """Send a message to everyone in a room."""
        if room_name not in self.active_connections:
            return
        disconnected = []
        for ws, _ in self.active_connections[room_name]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(ws)
        # Clean up dead connections
        for ws in disconnected:
            self.disconnect(ws, room_name)


# Singleton instance
manager = ConnectionManager()
