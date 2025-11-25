"""WebSocket endpoint for real-time trade streaming."""

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.services.websocket_manager import get_ws_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """WebSocket endpoint for real-time trade updates.
    
    Clients connect to /ws/trades and receive JSON trade messages in real-time
    as they are published to the `trades` Redis channel.
    
    Message format:
    {
      "id": 123,
      "symbol": "EURUSD",
      "side": "buy",
      "price": 1.0812,
      "qty": 0.1,
      "timestamp": "2025-11-17T10:05:00Z",
      "order_id": "order_123",
      "user_id": 1,
      "metadata": {}
    }
    """
    manager = get_ws_manager(settings.redis_url)
    await manager.connect(websocket)

    try:
        # Subscribe to Redis trades channel
        async with manager.subscribe("trades") as pubsub:
            if pubsub is None:
                # Redis not available; keep connection open but send warning
                await websocket.send_json(
                    {"error": "Redis pub/sub not available; trades will not update in real-time"}
                )
                # Keep connection alive
                while True:
                    await websocket.receive_text()
            else:
                # Listen for messages from Redis and broadcast to WebSocket
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            # Parse trade data from Redis message
                            trade_data = message["data"]
                            if isinstance(trade_data, bytes):
                                trade_data = trade_data.decode("utf-8")
                            
                            # Send to WebSocket client
                            await websocket.send_text(trade_data)
                        except Exception as e:
                            logger.error(f"Error processing Redis message: {e}")
                            continue
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except asyncio.CancelledError:
        await manager.disconnect(websocket)
        logger.info("WebSocket task cancelled")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
