from fastapi import APIRouter
from app.services.brokers.paper_client import PaperTradingClient
from app.services.execution import get_broker_client

router = APIRouter()


@router.get("/balance")
async def get_account_balance():
    """Get current account balance and equity from broker."""
    client = await get_broker_client()
    balance = await client.get_balance()
    return {
        "balance": balance.get("balance"),
        "equity": balance.get("equity"),
        "margin_used": balance.get("margin_used"),
        "margin_free": balance.get("margin_free"),
        "currency": balance.get("currency", "USD"),
    }


@router.get("/positions")
async def get_open_positions():
    """Get current open positions from broker."""
    client = await get_broker_client()
    positions = await client.get_positions()
    return positions
