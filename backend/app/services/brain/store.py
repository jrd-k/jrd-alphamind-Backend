import json
from typing import List
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY = "brain:decisions"


async def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def save_decision(decision: dict) -> None:
    """Push a decision to Redis list (left push). Keep list trimmed to last 100 items."""
    try:
        r = await _get_redis()
        await r.lpush(_KEY, json.dumps(decision))
        await r.ltrim(_KEY, 0, 99)
    except Exception as e:
        logger.warning("Failed to save brain decision to Redis: %s", e)


async def get_recent(n: int = 20) -> List[dict]:
    try:
        r = await _get_redis()
        items = await r.lrange(_KEY, 0, n - 1)
        return [json.loads(i) for i in items]
    except Exception as e:
        logger.warning("Failed to read recent brain decisions from Redis: %s", e)
        return []


async def save_decision_db(decision: dict) -> None:
    """Persist a brain decision to the SQL database in a thread to avoid blocking the event loop."""
    try:
        import asyncio

        from app.core.database import SessionLocal
        from app.models.orm_models import BrainDecision

        def _save():
            session = SessionLocal()
            try:
                ts = decision.get("timestamp")
                if isinstance(ts, str):
                    try:
                        ts_parsed = datetime.fromisoformat(ts)
                    except Exception:
                        ts_parsed = datetime.now(timezone.utc)
                elif isinstance(ts, datetime):
                    # if naive, make timezone-aware as UTC
                    if ts.tzinfo is None:
                        ts_parsed = ts.replace(tzinfo=timezone.utc)
                    else:
                        ts_parsed = ts
                else:
                    ts_parsed = datetime.now(timezone.utc)

                bd = BrainDecision(
                    symbol=decision.get("symbol"),
                    decision=decision.get("decision"),
                    confidence=decision.get("confidence", 0.0),
                    indicator=decision.get("indicator"),
                    deepseek=decision.get("deepseek"),
                    openai=decision.get("openai"),
                    timestamp=ts_parsed,
                )
                session.add(bd)
                session.commit()
            finally:
                session.close()

        # offload blocking DB write
        await asyncio.to_thread(_save)
    except Exception as e:
        logger.warning("Failed to save brain decision to DB: %s", e)
