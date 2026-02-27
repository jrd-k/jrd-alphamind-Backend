from fastapi import APIRouter, Depends
from app.services.brokers.paper_client import PaperTradingClient
from app.services.execution import get_broker_client
from app.core.security import get_current_user

router = APIRouter()


@router.get("/balance")
async def get_account_balance(current_user=Depends(get_current_user)):
    """Get current account balance and equity from broker."""
    client = await get_broker_client(current_user.id)
    balance = await client.get_balance()
    return {
        "balance": balance.get("balance"),
        "equity": balance.get("equity"),
        "margin_used": balance.get("margin_used"),
        "margin_free": balance.get("margin_free"),
        "currency": balance.get("currency", "USD"),
    }


@router.get("/positions")
async def get_open_positions(current_user=Depends(get_current_user)):
    """Get current open positions from broker."""
    client = await get_broker_client(current_user.id)
    positions = await client.get_positions()
    return positions
