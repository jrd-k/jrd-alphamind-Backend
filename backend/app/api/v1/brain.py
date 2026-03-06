from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from pydantic import Field
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.services.brain.brain import Brain
from app.core.security import get_current_user
from app.core.database import get_db
from app.models.orm_models import User, BrainDecision

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
    kimi: Optional[dict] = None
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


@router.get("/analytics")
async def get_brain_analytics(
    symbol: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive AI decision analytics for visualization dashboard.
    
    Returns:
    - Summary statistics (total decisions, ratios, avg confidence)
    - Confidence distribution (high/medium/low)
    - Time series data for charts
    - Indicator performance metrics
    - Recent decisions with full details
    """
    since = datetime.utcnow() - timedelta(days=days)

    query = db.query(BrainDecision).filter(BrainDecision.timestamp >= since)

    if symbol:
        query = query.filter(BrainDecision.symbol == symbol)

    decisions = query.order_by(desc(BrainDecision.timestamp)).all()

    if not decisions:
        return {
            "summary": {
                "total_decisions": 0,
                "buy_ratio": 0,
                "sell_ratio": 0,
                "hold_ratio": 0,
                "avg_confidence": 0,
            },
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "avg_confidence_by_type": {"BUY": 0, "SELL": 0, "HOLD": 0},
            "time_series": [],
            "indicator_performance": {},
            "recent_decisions": [],
        }

    # Calculate statistics
    total = len(decisions)
    buy_count = sum(1 for d in decisions if d.decision == "BUY")
    sell_count = sum(1 for d in decisions if d.decision == "SELL")
    hold_count = sum(1 for d in decisions if d.decision == "HOLD")

    # Confidence distribution
    confidence_ranges = {
        "high": sum(1 for d in decisions if d.confidence >= 0.7),
        "medium": sum(1 for d in decisions if 0.4 <= d.confidence < 0.7),
        "low": sum(1 for d in decisions if d.confidence < 0.4),
    }

    # Average confidence by decision type
    avg_confidence = {
        "BUY": (
            sum(d.confidence for d in decisions if d.decision == "BUY") / buy_count
            if buy_count
            else 0
        ),
        "SELL": (
            sum(d.confidence for d in decisions if d.decision == "SELL") / sell_count
            if sell_count
            else 0
        ),
        "HOLD": (
            sum(d.confidence for d in decisions if d.decision == "HOLD") / hold_count
            if hold_count
            else 0
        ),
    }

    # Time series data for charts
    daily_stats = {}
    for d in decisions:
        day = d.timestamp.strftime("%Y-%m-%d")
        if day not in daily_stats:
            daily_stats[day] = {"buy": 0, "sell": 0, "hold": 0, "avg_confidence": []}
        daily_stats[day][d.decision.lower()] += 1
        daily_stats[day]["avg_confidence"].append(d.confidence)

    # Calculate daily averages
    time_series = [
        {
            "date": day,
            "buy": stats["buy"],
            "sell": stats["sell"],
            "hold": stats["hold"],
            "avg_confidence": (
                sum(stats["avg_confidence"]) / len(stats["avg_confidence"])
                if stats["avg_confidence"]
                else 0
            ),
        }
        for day, stats in sorted(daily_stats.items())
    ]

    # Indicator performance
    indicator_signals = {}
    for d in decisions:
        if d.indicator and isinstance(d.indicator, dict):
            signal = d.indicator.get("signals", "unknown")
            if signal not in indicator_signals:
                indicator_signals[signal] = {"count": 0, "avg_confidence": []}
            indicator_signals[signal]["count"] += 1
            indicator_signals[signal]["avg_confidence"].append(d.confidence)

    indicator_perf = {
        k: {
            "count": v["count"],
            "avg_confidence": (
                sum(v["avg_confidence"]) / len(v["avg_confidence"])
                if v["avg_confidence"]
                else 0
            ),
        }
        for k, v in indicator_signals.items()
    }

    return {
        "summary": {
            "total_decisions": total,
            "buy_ratio": buy_count / total if total else 0,
            "sell_ratio": sell_count / total if total else 0,
            "hold_ratio": hold_count / total if total else 0,
            "avg_confidence": sum(d.confidence for d in decisions) / total if total else 0,
        },
        "confidence_distribution": confidence_ranges,
        "avg_confidence_by_type": avg_confidence,
        "time_series": time_series,
        "indicator_performance": indicator_perf,
        "recent_decisions": [
            {
                "id": d.id,
                "symbol": d.symbol,
                "decision": d.decision,
                "confidence": d.confidence,
                "timestamp": d.timestamp.isoformat(),
                "indicator_summary": (
                    d.indicator.get("summary", "") if isinstance(d.indicator, dict) else ""
                ),
                "rsi": d.indicator.get("rsi") if isinstance(d.indicator, dict) else None,
                "macd": (
                    d.indicator.get("macd_signal")
                    if isinstance(d.indicator, dict)
                    else None
                ),
            }
            for d in decisions[:20]
        ],
    }


@router.get("/symbols")
async def get_brain_symbols(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all symbols that have brain decisions."""
    symbols = db.query(BrainDecision.symbol).distinct().all()
    return {"symbols": [s[0] for s in symbols]}
