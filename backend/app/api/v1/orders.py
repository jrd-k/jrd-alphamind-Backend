from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_order():
    return {"message": "order created (placeholder)"}


@router.get("/{order_id}")
async def get_order(order_id: int):
    return {"id": order_id, "status": "filled"}
