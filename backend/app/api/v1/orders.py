from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pydantic_schemas import OrderCreate, OrderRead
from app.models.orm_models import Order
from app.services import execution
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=OrderRead)
def submit_order(order_in: OrderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # create order associated with authenticated user
    o = Order(user_id=current_user.id, symbol=order_in.symbol, quantity=order_in.quantity, status="new")
    db.add(o)
    db.commit()
    db.refresh(o)

    # simulate immediate execution for demo purposes
    exec_payload = {
        "symbol": o.symbol,
        "side": "buy",
        "price": 0.0,
        "qty": o.quantity,
        "order_id": str(o.id),
        "user_id": o.user_id,
    }
    # call execution service (will persist trade and publish)
    try:
        # execution.execute_order is async-capable; call sync wrapper if available
        if hasattr(execution, "execute_order_sync"):
            execution.execute_order_sync(exec_payload)
        else:
            execution.execute_order(exec_payload)
        # update order status
        o.status = "filled"
        db.add(o)
        db.commit()
        db.refresh(o)
    except Exception:
        # leave as new if execution fails
        pass

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
