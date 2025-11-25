from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime, timezone
from pydantic import Field

from app.services.brain.brain import Brain
from app.core.security import get_current_user

router = APIRouter(tags=["brain"])


class BrainPayload(BaseModel):
    symbol: str
    candles: List[Dict[str, Any]]
    current_price: Optional[float] = None


@router.post("/decide")
async def decide(payload: BrainPayload, current_user=Depends(get_current_user)):
    try:
        brain = Brain()
        res = await brain.decide(payload.symbol, payload.candles, payload.current_price)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def recent(limit: int = 20, current_user=Depends(get_current_user)):
    try:
        from app.services.brain.store import get_recent

        items = await get_recent(limit)
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DecisionRead(BaseModel):
    id: int
    symbol: str
    decision: str
    indicator: Optional[dict] = None
    deepseek: Optional[dict] = None
    openai: Optional[dict] = None
    timestamp: datetime
    created_at: Optional[datetime] = None


@router.get("/decisions")
def list_decisions(
    symbol: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
):
    """List persisted brain decisions from the SQL DB.

    - `symbol` filter: symbol exact match
    - `since` filter: ISO datetime, returns rows with `timestamp` >= since
    - pagination: `limit` and `offset`
    """
    try:
        from app.core.database import SessionLocal
        from app.models.orm_models import BrainDecision

        db = SessionLocal()
        q = db.query(BrainDecision)
        if symbol:
            q = q.filter(BrainDecision.symbol == symbol)
        if since:
            # ensure timezone-aware
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            q = q.filter(BrainDecision.timestamp >= since)

        total = q.count()
        items = q.order_by(BrainDecision.timestamp.desc()).offset(offset).limit(limit).all()

        # convert ORM objects to serializable dicts
        result = []
        for it in items:
            result.append(
                {
                    "id": it.id,
                    "symbol": it.symbol,
                    "decision": it.decision,
                    "indicator": it.indicator,
                    "deepseek": it.deepseek,
                    "openai": it.openai,
                    "timestamp": it.timestamp.isoformat() if it.timestamp else None,
                    "created_at": it.created_at.isoformat() if it.created_at else None,
                }
            )

        db.close()
        return {"total": total, "count": len(result), "items": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
