"""
Secure WebSocket implementation with JWT authentication, connection management,
and real-time trade/signal streaming.
"""
import json
import asyncio
import logging
from typing import Dict, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.orm_models import User, BrainDecision
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with user-level tracking and messaging."""

    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_id mapping for cleanup
        self.ws_to_user: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.ws_to_user[websocket] = user_id
        logger.info(
            f"User {user_id} connected. Total connections: {len(self.ws_to_user)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Unregister and clean up a WebSocket connection."""
        user_id = self.ws_to_user.pop(websocket, None)
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected. Remaining: {len(self.ws_to_user)}")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to all connections for a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message: {e}")
                    disconnected.append(connection)

            # Clean up failed connections
            for conn in disconnected:
                self.disconnect(conn)

    async def broadcast(self, message: dict, exclude_user: int = None):
        """Broadcast message to all connected users except excluded."""
        disconnected = []
        for ws, user_id in list(self.ws_to_user.items()):
            if user_id != exclude_user:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to broadcast: {e}")
                    disconnected.append(ws)

        for conn in disconnected:
            self.disconnect(conn)

    def get_connection_stats(self) -> dict:
        """Return connection statistics."""
        return {
            "total_connections": len(self.ws_to_user),
            "unique_users": len(self.active_connections),
            "connections_per_user": {
                uid: len(conns)
                for uid, conns in self.active_connections.items()
            },
        }


manager = ConnectionManager()


def verify_token(token: str) -> int:
    """Verify JWT token and return user_id."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise credentials_exception


async def websocket_trades(
    websocket: WebSocket, token: str = Query(..., description="JWT access token")
):
    """
    Secure WebSocket endpoint for real-time trade updates and AI signals.
    Requires valid JWT token as query parameter.

    Messages sent by client:
    - {"action": "ping"} -> server responds with pong
    - {"action": "subscribe_symbol", "symbol": "EURUSD"} -> subscribe to updates

    Messages sent by server:
    - {"type": "trade", "data": {...}, "timestamp": "2026-02-27T..."}
    - {"type": "brain_signal", "data": {...}, "timestamp": "2026-02-27T..."}
    - {"type": "pong", "timestamp": "2026-02-27T..."}
    - {"type": "subscribed", "symbol": "EURUSD"}
    """
    try:
        user_id = verify_token(token)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid authentication")
        return

    await manager.connect(websocket, user_id)

    # Track Redis subscriptions
    pubsub = None
    redis_listener_task = None
    heartbeat_task = None

    try:
        # Initialize Redis pubsub
        pubsub = redis_service.redis.pubsub()

        # Subscribe to user-specific and global channels
        channels = [
            f"trades:user:{user_id}",  # User's own trades
            "trades:global",  # Global trades
            f"brain:signals:{user_id}",  # AI signals for this user
        ]
        await pubsub.subscribe(*channels)
        logger.info(f"User {user_id} subscribed to channels: {channels}")

        async def redis_listener():
            """Listen for Redis messages and forward to WebSocket."""
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                        msg_type = channel.split(":")[0]

                        await websocket.send_json(
                            {
                                "type": msg_type,
                                "data": data,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from Redis")
                    except Exception as e:
                        logger.error(f"Error forwarding Redis message: {e}")

        async def heartbeat():
            """Send periodic pings to keep connection alive."""
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send_json(
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except Exception:
                    break

        # Start background tasks
        redis_listener_task = asyncio.create_task(redis_listener())
        heartbeat_task = asyncio.create_task(heartbeat())

        # Handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)

                action = msg.get("action")

                if action == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

                elif action == "subscribe_symbol":
                    symbol = msg.get("symbol")
                    if symbol:
                        await pubsub.subscribe(f"trades:symbol:{symbol}")
                        await websocket.send_json(
                            {
                                "type": "subscribed",
                                "symbol": symbol,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                        logger.info(f"User {user_id} subscribed to {symbol}")

                elif action == "stats":
                    stats = manager.get_connection_stats()
                    await websocket.send_json(
                        {
                            "type": "stats",
                            "data": stats,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Unknown action: {action}",
                        }
                    )

            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON"}
                )
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        manager.disconnect(websocket)

        # Cleanup
        if redis_listener_task:
            redis_listener_task.cancel()
        if heartbeat_task:
            heartbeat_task.cancel()
        if pubsub:
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
            except Exception as e:
                logger.warning(f"Error closing pubsub: {e}")

        logger.info(f"WebSocket cleanup completed for user {user_id}")


async def websocket_market_data(websocket: WebSocket):
    """
    Public WebSocket for market data (prices, orderbook) - no auth required.
    """
    await websocket.accept()
    pubsub = None

    try:
        pubsub = redis_service.redis.pubsub()
        await pubsub.subscribe("market:ticks", "market:orderbook")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Market data WebSocket error: {e}")
    finally:
        if pubsub:
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
            except Exception:
                pass
