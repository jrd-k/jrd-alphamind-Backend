from fastapi import APIRouter

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    return {"symbol": symbol, "price": 123.45}
