"""WebSocket endpoint for real-time trade streaming."""

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.services.websocket_manager import get_ws_manager
from app.services.execution import get_broker_client

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


@router.websocket("/ws/pnl")
async def websocket_pnl(websocket: WebSocket):
    """WebSocket endpoint for real-time P&L updates.
    
    Clients connect to /ws/pnl and receive JSON P&L messages every 5 seconds.
    
    Message format:
    {
      "total_pnl": 123.45,
      "positions": [
        {
          "symbol": "EURUSD",
          "side": "buy",
          "volume": 0.1,
          "price": 1.0812,
          "profit_loss": 12.34
        }
      ]
    }
    """
    await websocket.accept()
    
    try:
        while True:
            # Get broker client and fetch positions
            client = await get_broker_client()
            positions = await client.get_positions()
            
            # Calculate total P&L
            total_pnl = sum(pos.get("profit_loss", 0) for pos in positions)
            
            # Send update
            await websocket.send_json({
                "total_pnl": total_pnl,
                "positions": positions
            })
            
            # Wait 5 seconds before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("PnL WebSocket client disconnected")
    except Exception as e:
        logger.error(f"PnL WebSocket error: {e}")


@router.websocket("/ws/ml-signals")
async def websocket_ml_signals(websocket: WebSocket):
    """WebSocket endpoint for real-time ML trading signals.
    
    Clients connect to /ws/ml-signals and receive JSON ML signal messages in real-time
    as they are published to the `ml_signals` Redis channel.
    
    Message format:
    {
      "symbol": "EURUSD",
      "signal": "BUY",
      "confidence": 0.85,
      "prediction": 1.0825,
      "features": {
        "rsi": 65.2,
        "macd": 0.0012,
        "bb_position": 0.3
      },
      "timestamp": "2025-11-17T10:05:00Z",
      "model_version": "v1.0"
    }
    """
    manager = get_ws_manager(settings.redis_url)
    await manager.connect(websocket)

    try:
        # Subscribe to Redis ML signals channel
        async with manager.subscribe("ml_signals") as pubsub:
            if pubsub is None:
                # Redis not available; keep connection open but send warning
                await websocket.send_json(
                    {"error": "Redis pub/sub not available; ML signals will not update in real-time"}
                )
                # Keep connection alive
                while True:
                    await websocket.receive_text()
            else:
                # Listen for messages from Redis and broadcast to WebSocket
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            # Parse ML signal data from Redis message
                            signal_data = message["data"]
                            if isinstance(signal_data, bytes):
                                signal_data = signal_data.decode("utf-8")
                            
                            # Send to WebSocket client
                            await websocket.send_text(signal_data)
                        except Exception as e:
                            logger.error(f"Error processing ML signal Redis message: {e}")
                            continue
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info("ML signals WebSocket client disconnected")
    except asyncio.CancelledError:
        await manager.disconnect(websocket)
        logger.info("ML signals WebSocket task cancelled")
    except Exception as e:
        logger.error(f"ML signals WebSocket error: {e}")
        await manager.disconnect(websocket)
