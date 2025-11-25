from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.orm_models import IndicatorSignal
from app.models.pydantic_schemas import IndicatorCreate, IndicatorRead
from app.services.indicators.supertrend_ai import compute_supertrend
from app.services.indicators.fibonacci import compute_fibonacci
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter(tags=["indicators"])


def _verify_indicator_api_key(x_indicator_api_key: Optional[str] = Header(None, alias="X-Indicator-API-Key")):
    """If settings.indicator_api_key is set (non-empty), require the incoming header to match it.
    If settings.indicator_api_key is empty, allow access (public).
    """
    configured = (settings.indicator_api_key or "").strip()
    if not configured:
        return True
    if x_indicator_api_key == configured:
        return True
    raise HTTPException(status_code=401, detail="Invalid indicator API key")


@router.post("/", response_model=IndicatorRead)
def ingest_indicator(ind: IndicatorCreate, db: Session = Depends(get_db), _auth=Depends(_verify_indicator_api_key)):
    # create and persist indicator signal
    ts = ind.timestamp
    if ts is None:
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc)

    obj = IndicatorSignal(
        symbol=ind.symbol,
        source=ind.source or "supertrend_ai",
        signal=ind.signal,
        value=ind.value,
        timestamp=ts,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/latest", response_model=List[IndicatorRead])
def latest_indicators(symbol: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(IndicatorSignal)
    if symbol:
        q = q.filter(IndicatorSignal.symbol == symbol)
    q = q.order_by(IndicatorSignal.timestamp.desc()).limit(limit)
    return q.all()


from pydantic import BaseModel


class ComputePayload(BaseModel):
    ind: IndicatorCreate
    candles: List[dict]


@router.post("/compute", response_model=IndicatorRead)
def compute_and_store(payload: ComputePayload, db: Session = Depends(get_db), _auth=Depends(_verify_indicator_api_key)):
    """Compute the SuperTrend AI indicator on provided candles and persist the latest signal.

    Payload: JSON with keys `ind` (IndicatorCreate) and `candles` (list of candle dicts)
    """
    ind = payload.ind
    candles = payload.candles

    if not candles:
        raise HTTPException(status_code=400, detail="candles list required")

    # compute
    res = compute_supertrend(candles, length=10, min_mult=1.0, max_mult=5.0, step=0.5, perf_alpha=10.0, from_cluster=ind.source)

    # store summary into DB as IndicatorSignal (value contains the summary)
    summary = res.get("summary") or {}
    ts_raw = summary.get("timestamp")
    if isinstance(ts_raw, str):
        try:
            ts = datetime.fromisoformat(ts_raw)
        except Exception:
            ts = datetime.now(timezone.utc)
    elif isinstance(ts_raw, datetime):
        ts = ts_raw
    else:
        ts = datetime.now(timezone.utc)

    obj = IndicatorSignal(
        symbol=ind.symbol,
        source=ind.source or "supertrend_ai",
        signal=summary.get("os") and ("bull" if summary.get("os") else "bear"),
        value=summary,
        timestamp=ts,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/compute/fibonacci", response_model=IndicatorRead)
def compute_and_store_fibonacci(payload: ComputePayload, db: Session = Depends(get_db), _auth=Depends(_verify_indicator_api_key)):
    """Compute Fibonacci retracement levels on provided candles and persist the signal.
    
    Returns nearest Fibonacci level and buy/sell signals based on current price.
    """
    ind = payload.ind
    candles = payload.candles

    if not candles:
        raise HTTPException(status_code=400, detail="candles list required")

    # compute fibonacci
    result = compute_fibonacci(candles, lookback=50)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result.get("error"))

    # Determine signal based on nearest level proximity
    nearest = result.get("nearest_level", "50%")
    signals = result.get("signals", {})
    
    # Map signals to buy/sell/hold
    signal_val = "neutral"
    if any(key in signals for key in ["strong_support", "below_swing"]):
        signal_val = "bull"
    elif any(key in signals for key in ["strong_resistance", "above_swing"]):
        signal_val = "bear"
    elif "support" in signals:
        signal_val = "bull"
    elif "resistance" in signals:
        signal_val = "bear"

    ts_raw = result.get("timestamp")
    if isinstance(ts_raw, str):
        try:
            ts = datetime.fromisoformat(ts_raw)
        except Exception:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)

    obj = IndicatorSignal(
        symbol=ind.symbol,
        source="fibonacci",
        signal=signal_val,
        value=result,
        timestamp=ts,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
