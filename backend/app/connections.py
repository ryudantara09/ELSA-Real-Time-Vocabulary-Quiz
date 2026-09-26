import asyncio

from fastapi import WebSocket


class ConnectionManager:
    """In-memory WebSocket rooms keyed by quiz_id."""

    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, WebSocket]] = {}
        self._room_locks: dict[str, asyncio.Lock] = {}
        self._guard = asyncio.Lock()

    def room_lock(self, quiz_id: str) -> asyncio.Lock:
        lock = self._room_locks.get(quiz_id)
        if lock is None:
            lock = asyncio.Lock()
            self._room_locks[quiz_id] = lock
        return lock

    async def connect(self, quiz_id: str, user_id: str, websocket: WebSocket) -> None:
        previous: WebSocket | None = None
        async with self._guard:
            room = self._rooms.setdefault(quiz_id, {})
            previous = room.get(user_id)
            room[user_id] = websocket
        if previous is not None and previous is not websocket:
            await _close_quietly(previous)

    async def disconnect(self, quiz_id: str, user_id: str, websocket: WebSocket) -> None:
        async with self._guard:
            room = self._rooms.get(quiz_id)
            if room is None or room.get(user_id) is not websocket:
                return
            room.pop(user_id, None)
            if not room:
                self._rooms.pop(quiz_id, None)

    async def broadcast(self, quiz_id: str, message: dict[str, object]) -> None:
        async with self._guard:
            targets = list(self._rooms.get(quiz_id, {}).items())
        for user_id, websocket in targets:
            try:
                await websocket.send_json(message)
            except Exception:
                # One closed client must not stop the rest of the room.
                await self.disconnect(quiz_id, user_id, websocket)


connection_manager = ConnectionManager()


async def _close_quietly(websocket: WebSocket) -> None:
    try:
        await websocket.close(code=1000)
    except Exception:
        return
