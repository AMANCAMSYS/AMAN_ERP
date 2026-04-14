"""
WebSocket Connection Manager for real-time notifications
مدير اتصالات WebSocket للإشعارات الفورية
"""

import json
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("aman.ws")


class ConnectionManager:
    """يدير اتصالات WebSocket لكل مستخدم"""

    MAX_CONNECTIONS_PER_USER = 3

    def __init__(self):
        # { "company_id:user_id": [WebSocket, ...] }
        self._connections: Dict[str, List[WebSocket]] = {}

    def _key(self, company_id: str, user_id: int) -> str:
        return f"{company_id}:{user_id}"

    async def connect(self, ws: WebSocket, company_id: str, user_id: int):
        key = self._key(company_id, user_id)
        current_count = len(self._connections.get(key, []))
        if current_count >= self.MAX_CONNECTIONS_PER_USER:
            await ws.close(code=4008, reason="Too many connections")
            logger.warning(f"WS connection rejected (limit reached): {key}")
            return False
        await ws.accept()
        if key not in self._connections:
            self._connections[key] = []
        self._connections[key].append(ws)
        logger.info(f"WS connected: {key} (total={len(self._connections[key])})")
        return True

    def disconnect(self, ws: WebSocket, company_id: str, user_id: int):
        key = self._key(company_id, user_id)
        if key in self._connections:
            self._connections[key] = [c for c in self._connections[key] if c is not ws]
            if not self._connections[key]:
                del self._connections[key]
        logger.info(f"WS disconnected: {key}")

    async def send_to_user(self, company_id: str, user_id: int, data: dict):
        """إرسال إشعار لمستخدم محدد"""
        key = self._key(company_id, user_id)
        dead = []
        for ws in self._connections.get(key, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws, company_id, user_id)

    async def broadcast_company(self, company_id: str, data: dict):
        """إرسال لجميع مستخدمي شركة"""
        prefix = f"{company_id}:"
        dead_pairs = []
        for key, sockets in self._connections.items():
            if key.startswith(prefix):
                for ws in sockets:
                    try:
                        await ws.send_json(data)
                    except Exception:
                        dead_pairs.append((ws, key))
        for ws, key in dead_pairs:
            parts = key.split(":", 1)
            self.disconnect(ws, parts[0], int(parts[1]))

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Singleton instance
ws_manager = ConnectionManager()
