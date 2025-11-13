import json
from typing import Dict, Any
from app.core.config import settings

from app.core.database import SessionLocal
from app.models.orm_models import Trade

try:
    import redis.asyncio as redis_async
except Exception:
    redis_async = None


def execute_order(order: Dict[str, Any]):
    """Saves the executed trade to DB and publishes to Redis `trades` channel.

    Order dict expected keys: symbol, side, price, qty, timestamp (optional), order_id, user_id, metadata
    """
    # save to DB (sync)
    db = SessionLocal()
    try:
        trade_payload = {
            "symbol": order.get("symbol"),
            "side": order.get("side"),
            "price": order.get("price"),
            "qty": order.get("qty"),
            "order_id": order.get("order_id"),
            "user_id": order.get("user_id"),
            "metadata": order.get("metadata"),
        }
        if order.get("timestamp"):
            trade_payload["timestamp"] = order.get("timestamp")

        t = Trade(**trade_payload)
        db.add(t)
        db.commit()
        db.refresh(t)
    finally:
        db.close()

    # publish to redis channel (async fire-and-forget if possible)
    if redis_async is not None:
        try:
            # create a short-lived client and publish
            r = redis_async.from_url(settings.redis_url)

            # Serialise simple fields only
            pub = {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "price": t.price,
                "qty": t.qty,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "order_id": t.order_id,
                "user_id": t.user_id,
                "metadata": t.metadata,
            }

            # schedule publish in background event loop if present
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # fire-and-forget
                    loop.create_task(r.publish("trades", json.dumps(pub)))
                else:
                    loop.run_until_complete(r.publish("trades", json.dumps(pub)))
            except RuntimeError:
                # no running loop; publish synchronously
                import asyncio

                asyncio.run(r.publish("trades", json.dumps(pub)))
        except Exception:
            # don't raise for publish failures; trade is persisted
            pass

    return {"order_id": t.id, "status": "executed"}
