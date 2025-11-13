from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class OrderCreate(BaseModel):
    symbol: str
    quantity: float


class OrderRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    quantity: float
    status: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


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
    id: int
    symbol: str
    side: str
    price: float
    qty: float
    timestamp: Optional[datetime]
    order_id: Optional[str]
    user_id: Optional[int]
    metadata: Optional[dict]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InstrumentRead(BaseModel):
    id: int
    symbol: str
    name: Optional[str]

    class Config:
        orm_mode = True
