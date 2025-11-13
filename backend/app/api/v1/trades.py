from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from sqlalchemy.orm import Session
from app.models import pydantic_schemas as schemas
from app.models.orm_models import Trade

router = APIRouter()


@router.get("/", response_model=List[schemas.TradeRead])
def list_trades(symbol: Optional[str] = Query(None), since: Optional[datetime] = Query(None), limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(Trade)
    if symbol:
        q = q.filter(Trade.symbol == symbol)
    if since:
        q = q.filter(Trade.timestamp >= since)
    q = q.order_by(Trade.timestamp.desc()).limit(limit)
    return q.all()


@router.post("/", response_model=schemas.TradeRead, status_code=201)
def create_trade(trade_in: schemas.TradeCreate, db: Session = Depends(get_db)):
    trade_data = trade_in.dict()
    # if timestamp is None, let DB set default
    if trade_data.get("timestamp") is None:
        trade_data.pop("timestamp", None)
    t = Trade(**trade_data)
    db.add(t)
    db.commit()
    db.refresh(t)

    # Publishing to Redis is handled by execution service when used by execution path
    return t
