from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pydantic_schemas import OrderCreate, OrderRead
from app.models.orm_models import Order
from app.services import execution
from app.core.security import get_current_user
from app.services.trade_orchestrator import TradeOrchestrator

router = APIRouter()
orchestrator = TradeOrchestrator()


@router.post("/", response_model=OrderRead)
async def submit_order(order_in: OrderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Create order record first with pending status
    o = Order(
        user_id=current_user.id,
        symbol=order_in.symbol,
        quantity=order_in.quantity,
        status="pending",
    )
    db.add(o)
    db.commit()
    db.refresh(o)

    # Now run orchestrator to check risks and execute if safe
    try:
        result = await orchestrator.orchestrate_trade(
            symbol=order_in.symbol,
            current_price=order_in.current_price,
            requested_qty=order_in.quantity,
            stop_loss_pips=order_in.stop_loss_pips,
            indicators=order_in.indicators,
            order_id=str(o.id),  # Pass the order ID
            user_id=current_user.id,
            auto_execute=True,
        )
    except Exception as e:
        # If orchestrator fails, mark order as rejected
        o.status = "rejected"
        db.add(o)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Orchestration failed: {str(e)}")

    # Update order status based on orchestrator result
    if result.get("can_execute") and result.get("execution_result"):
        # Order was executed successfully
        o.status = "filled"
        # Update quantity to the actual lot size used
        o.quantity = result.get("lot_size", o.quantity)
    else:
        # Order rejected by risk checks
        o.status = "rejected"

    db.add(o)
    db.commit()
    db.refresh(o)

    return o


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="order not found")
    return o


@router.get("/", response_model=List[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.created_at.desc()).limit(100).all()
