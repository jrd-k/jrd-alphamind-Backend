import json
import os
import asyncio
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.orm_models import Trade
from app.services.brokers.exness_client import ExnessClient
from app.services.brokers.paper_client import PaperTradingClient
from app.services.brokers.justmarkets_client import JustMarketsClient
from app.services.brokers.mt5_client import MT5Client

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis_async
except Exception:
    redis_async = None


async def get_broker_client(user_id: Optional[int] = None):
    """Select and return the appropriate broker client based on user settings or BROKER env var.
    
    Args:
        user_id: User ID to get broker account for. If None, falls back to env var.
    """
    from app.core.database import SessionLocal
    from app.models.orm_models import BrokerAccount
    
    broker_client = None
    
    # If user_id provided, try to get user's active broker account
    if user_id:
        db = SessionLocal()
        try:
            active_account = db.query(BrokerAccount).filter(
                BrokerAccount.user_id == user_id,
                BrokerAccount.is_active == 1
            ).first()
            
            if active_account:
                broker_client = _create_broker_client_from_account(active_account)
                logger.info(f"Using {active_account.broker_name} account for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to get broker account for user {user_id}: {e}")
        finally:
            db.close()
    
    # Fallback to environment variable if no user account found
    if not broker_client:
        broker = os.getenv("BROKER", "paper").lower()
        broker_client = _create_broker_client_from_env(broker)
        logger.info(f"Using {broker} broker from environment (fallback)")
    
    return broker_client


def _create_broker_client_from_account(account: BrokerAccount):
    """Create broker client from BrokerAccount model."""
    broker_name = account.broker_name.lower()
    
    if broker_name == "exness":
        from app.services.brokers.exness_client import ExnessClient
        # Override environment variables with account data
        original_env = {}
        if account.api_key:
            original_env["EXNESS_API_KEY"] = os.environ.get("EXNESS_API_KEY")
            os.environ["EXNESS_API_KEY"] = account.api_key
        if account.base_url:
            original_env["EXNESS_BASE_URL"] = os.environ.get("EXNESS_BASE_URL")
            os.environ["EXNESS_BASE_URL"] = account.base_url
        
        client = ExnessClient()
        
        # Restore original environment
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
        
        return client
        
    elif broker_name == "justmarkets":
        from app.services.brokers.justmarkets_client import JustMarketsClient
        # Similar pattern for JustMarkets
        return JustMarketsClient()
        
    elif broker_name == "mt5":
        from app.services.brokers.mt5_client import MT5Client
        return MT5Client(
            mt5_path=account.mt5_path,
            account=account.account_id,
            password=account.mt5_password
        )
    
    # Default to paper trading
    from app.services.brokers.paper_client import PaperTradingClient
    return PaperTradingClient()


def _create_broker_client_from_env(broker: str):
    """Create broker client from environment variables (legacy method)."""
    if broker == "exness":
        return ExnessClient()
    elif broker == "justmarkets":
        return JustMarketsClient()
    elif broker == "mt5":
        return MT5Client(
            mt5_path=os.getenv("MT5_PATH"),
            account=os.getenv("MT5_ACCOUNT"),
            password=os.getenv("MT5_PASSWORD")
        )
    return PaperTradingClient()


async def execute_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """Execute order via broker client, save trade to DB, and publish to Redis.

    Args:
        order: Dict with keys: symbol, side, qty, price (optional), order_id, user_id, metadata
        
    Returns:
        Dict with order_id and status
    """
    # Get broker client
    client = await get_broker_client(order.get("user_id"))

    # If live trading is disabled or not explicitly confirmed, simulate the broker result (dry-run)
    # Require BOTH ENABLE_LIVE_TRADING=true and CONFIRM_LIVE=CONFIRM-LIVE to allow live execution
    if not (settings.enable_live_trading and settings.confirm_live_token == "CONFIRM-LIVE"):
        # Simulate a broker result without contacting external brokers
        import uuid

        broker_result = {
            "order_id": f"sim-{uuid.uuid4().hex}",
            "price": order.get("price") or 1.0,
            "status": "simulated",
        }
    else:
        # Place order with broker for real execution
        broker_result = await client.place_order(
            symbol=order.get("symbol"),
            side=order.get("side"),
            qty=order.get("qty"),
            price=order.get("price"),
            order_type="market",
        )

    # Save to DB (sync)
    db = SessionLocal()
    try:
        # Mark metadata to indicate simulated vs live
        metadata = order.get("metadata") or {}
        metadata.setdefault("broker_order_id", broker_result.get("order_id"))
        if broker_result.get("status") == "simulated":
            metadata["simulated"] = True

        trade_payload = {
            "symbol": order.get("symbol"),
            "side": order.get("side"),
            "price": broker_result.get("price"),
            "qty": order.get("qty"),
            "order_id": order.get("order_id"),
            "user_id": order.get("user_id"),
            "metadata": metadata,
        }

        t = Trade(**trade_payload)
        db.add(t)
        db.commit()
        db.refresh(t)
    finally:
        db.close()

    # Publish to Redis trades channel
    if redis_async is not None:
        try:
            r = redis_async.from_url(settings.redis_url)
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
            await r.publish("trades", json.dumps(pub))
        except Exception:
            # Don't raise for publish failures; trade is persisted
            pass

    return {"order_id": t.id, "status": broker_result.get("status", "filled")}


def execute_order_sync(order: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for execute_order (for sync contexts).
    
    Use this when calling from non-async code (e.g., FastAPI route without async).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from async context, create a task (fire-and-forget)
            task = loop.create_task(execute_order(order))
            return {"order_id": 0, "status": "pending"}
        else:
            return asyncio.run(execute_order(order))
    except RuntimeError:
        return asyncio.run(execute_order(order))
