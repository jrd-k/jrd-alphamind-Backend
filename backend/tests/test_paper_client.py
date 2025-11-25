import asyncio
import pytest

from app.services.brokers.paper_client import PaperTradingClient


@pytest.mark.asyncio
async def test_place_order_and_positions():
    client = PaperTradingClient()

    resp = await client.place_order(symbol="EURUSD", side="buy", qty=0.1)
    assert resp["status"] == "filled"
    assert "price" in resp
    assert resp["symbol"] == "EURUSD"

    positions = await client.get_positions()
    # position may be present since we bought
    assert isinstance(positions, list)


@pytest.mark.asyncio
async def test_get_balance():
    client = PaperTradingClient()
    bal = await client.get_balance()
    assert isinstance(bal, dict)
    assert "balance" in bal
