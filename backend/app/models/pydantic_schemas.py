from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    created_at: Optional[datetime]


class OrderCreate(BaseModel):
    symbol: str
    quantity: float
    current_price: float
    stop_loss_pips: Optional[float] = None
    indicators: Optional[List[Dict[str, Any]]] = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    symbol: str
    quantity: float
    status: str
    created_at: Optional[datetime]


# Trade schemas


class TradeCreate(BaseModel):
    symbol: str
    side: str
    price: float
    qty: float
    timestamp: Optional[datetime]
    order_id: Optional[str]
    user_id: Optional[int]
    metadata: Optional[dict]


class TradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    symbol: str
    side: str
    price: float
    qty: float
    timestamp: Optional[datetime]
    order_id: Optional[str]
    user_id: Optional[int]
    metadata: Optional[dict]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InstrumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    symbol: str
    name: Optional[str]


# Indicator schemas
class IndicatorCreate(BaseModel):
    symbol: str
    source: Optional[str] = "supertrend_ai"
    signal: Optional[str] = None
    value: Optional[dict] = None
    timestamp: Optional[datetime] = None


class IndicatorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    symbol: str
    source: str
    signal: Optional[str]
    value: Optional[dict]
    timestamp: Optional[datetime]
    created_at: Optional[datetime]
