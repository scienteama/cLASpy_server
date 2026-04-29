import socketio
from typing import Dict
from app.utils.auth_utils import verify_token


class SocketIOService:
    def __init__(self):
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")

        self.active_users: Dict[int, str] = {}

    async def connect(self, sid: str, environ):
        try:
            cookie_header = environ.get("HTTP_COOKIE", "")
            token = self._extract_token(cookie_header)

            if not token:
                return False

            user = verify_token(token)
            user_id = user.id

            self.active_users[user_id] = sid

            await self.sio.save_session(sid, {"user_id": user_id})
            await self.sio.enter_room(sid, f"user:{user_id}")

            print(f"[WS] User {user_id} connected (sid={sid})")
            return True

        except Exception as e:
            print(f"[WS] Auth error: {e}")
            return False

    def _extract_token(self, cookie_header: str) -> str | None:
        if not cookie_header:
            return None

        cookies = dict(item.split("=", 1) for item in cookie_header.split("; ") if "=" in item)

        return cookies.get("token")

    async def disconnect(self, sid: str):
        user_id = None

        for uid, stored_sid in list(self.active_users.items()):
            if stored_sid == sid:
                user_id = uid
                del self.active_users[uid]
                break

        print(f"[WS] disconnect sid={sid} user={user_id}")

    async def send_all(self, event: str, payload: dict):
        await self.sio.emit(event, payload)

    async def send_to_user(self, user_id: int, event: str, payload: dict):
        room = f"user:{user_id}"
        await self.sio.emit(event, payload, room=room)

    def register_handlers(self):
        @self.sio.event
        async def connect(sid, environ):
            return await self.connect(sid, environ)

        @self.sio.event
        async def disconnect(sid):
            await self.disconnect(sid)
