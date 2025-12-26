# ===== WebSocket Connection Manager =====

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

from cribbage.models import GameStateResponse


class ConnectionManager:
    """Tracks active websocket connections per game and broadcasts state changes."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(game_id, set()).add(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                self.active_connections.pop(game_id, None)

    async def send_state(self, websocket: WebSocket, state: GameStateResponse):
        await websocket.send_json(state.model_dump())

    async def broadcast_state(self, game_id: str, state: GameStateResponse):
        connections = list(self.active_connections.get(game_id, set()))
        for connection in connections:
            try:
                await self.send_state(connection, state)
            except WebSocketDisconnect:
                self.disconnect(game_id, connection)
            except Exception:
                # Drop any connection that fails to send
                self.disconnect(game_id, connection)