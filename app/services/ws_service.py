import asyncio
from collections import defaultdict
from typing import Dict, Set
from fastapi import WebSocket

from app.utils.auth_utils import verify_token


class WebSocketService:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = defaultdict(set)
        self.heartbeat_interval = 30

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id].add(websocket)
        asyncio.create_task(self.send_heartbeat(websocket))

    def disconnect(self, websocket: WebSocket):
        self.active_connections = {
            user_id: {ws for ws in connections if ws != websocket}
            for user_id, connections in self.active_connections.items()
        }

    async def send_all(self, message: str):
        disconnected = []
        for user_id, connections in self.active_connections.items():
            for conn in connections:
                try:
                    await conn.send_text(message)
                except BaseException:
                    disconnected.append(conn)
        for ws in disconnected:
            self.disconnect(ws)

    async def send_to_user(self, user_id: int, message_type: str, payload: dict):
        """
        Envoie un message JSON à un utilisateur spécifique.

        :param user_id: l'identifiant de l'utilisateur
        :param message_type: type du message (ex: "notification", "update", etc.)
        :param payload: dictionnaire avec les données du message
        """
        message = {
            "type": message_type,
            **payload  # fusionne le contenu du message
        }

        for conn in self.active_connections.get(user_id, set()):
            try:
                await conn.send_json(message)
            except Exception:
                self.disconnect(conn)

    async def send_heartbeat(self, websocket: WebSocket):
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception as e:
                    print(f"Heartbeat error, disconnecting: {str(e)}")
                    self.disconnect(websocket)
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Unexpected heartbeat error: {str(e)}")
            self.disconnect(websocket)

    async def receive_text(self, websocket: WebSocket) -> str:
        return await websocket.receive_text()

    async def authenticate_and_connect(self, websocket: WebSocket):
        try:
            token = websocket.cookies.get("token") or websocket.headers.get("Authorization")
            if token is None:
                await websocket.close(code=4001)
                return False
            
            user_data = verify_token(token)
            
            await self.connect(websocket, user_data.id)
            return True
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            try:
                await websocket.close(code=4001)
            except Exception:
                pass
            return False
