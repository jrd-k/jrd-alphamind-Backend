from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.orm_models import Instrument
from app.models.pydantic_schemas import InstrumentRead

router = APIRouter()


@router.get("/", response_model=List[InstrumentRead])
def list_instruments(db: Session = Depends(get_db)):
    return db.query(Instrument).order_by(Instrument.symbol).all()
