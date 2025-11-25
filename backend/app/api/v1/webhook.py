from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import json

from app.core.config import settings
from app.services.execution import execute_order_sync

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/tradingview")
async def tradingview_webhook(request: Request):
    secret = settings.confirm_live_token and settings.confirm_live_token or settings.confirm_live_token
    secret = settings.__dict__.get("confirm_live_token") or ""

    body = await request.body()
    sig_header = request.headers.get("X-TradingView-Signature")

    if secret:
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature header")
        computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, sig_header):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    # Expect basic payload with 'action' and 'symbol' and optional 'price' and 'qty'
    action = payload.get("action")
    symbol = payload.get("symbol")
    price = payload.get("price")
    qty = float(payload.get("qty", 0)) if payload.get("qty") is not None else None

    if action in ("buy", "sell") and symbol:
        order = {
            "symbol": symbol,
            "side": action,
            "qty": qty or settings.max_trade_qty,
            "price": price,
            "order_id": payload.get("id") or None,
            "user_id": payload.get("user_id") or None,
            "metadata": {"source": "tradingview", "payload": payload},
        }
        # Use sync wrapper (will be simulated unless live confirmed)
        res = execute_order_sync(order)
        return {"accepted": True, "execute_result": res}

    return {"accepted": False, "reason": "unsupported payload"}
