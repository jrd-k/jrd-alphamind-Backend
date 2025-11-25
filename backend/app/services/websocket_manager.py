"""WebSocket manager for real-time trade streaming via Redis pub/sub."""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis_async
except ImportError:
    redis_async = None

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and Redis pub/sub subscriptions.
    
    Connects to Redis, subscribes to channels, and broadcasts messages
    to all connected WebSocket clients.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.active_connections: Set[Any] = set()
        self.pubsub = None
        self.redis_client = None

    async def connect(self, websocket: Any):
        """Add a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: Any):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Clean up failed connections
        for conn in disconnected:
            self.active_connections.discard(conn)

    @asynccontextmanager
    async def subscribe(self, channel: str):
        """Subscribe to a Redis channel and yield the pubsub object.
        
        Context manager ensures proper cleanup of connections.
        """
        if not redis_async:
            logger.warning("redis.asyncio not available; WebSocket will not receive messages")
            yield None
            return

        try:
            self.redis_client = redis_async.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to Redis channel: {channel}")
            yield self.pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis: {e}")
            yield None
        finally:
            if self.pubsub:
                try:
                    await self.pubsub.unsubscribe(channel)
                    await self.pubsub.close()
                except Exception as e:
                    logger.warning(f"Error closing pubsub: {e}")
            if self.redis_client:
                try:
                    await self.redis_client.close()
                except Exception as e:
                    logger.warning(f"Error closing redis client: {e}")


# Global manager instance (created per app startup)
_manager: Dict[str, WebSocketManager] = {}


def get_ws_manager(redis_url: str) -> WebSocketManager:
    """Get or create a WebSocket manager for the given Redis URL."""
    if redis_url not in _manager:
        _manager[redis_url] = WebSocketManager(redis_url)
    return _manager[redis_url]
