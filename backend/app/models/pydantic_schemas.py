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
