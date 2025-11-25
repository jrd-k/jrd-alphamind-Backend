import pytest

from app.services.brokers.paper_client import PaperTradingClient


@pytest.mark.asyncio
async def test_place_order_filled():
    client = PaperTradingClient()
    res = await client.place_order("EURUSD", "buy", 0.1)
    assert res["status"] == "filled"
    assert res["symbol"] == "EURUSD"
    assert res["volume"] == 0.1


@pytest.mark.asyncio
async def test_get_balance_and_positions():
    client = PaperTradingClient()
    bal = await client.get_balance()
    assert "balance" in bal
    assert bal["balance"] >= 0

    # place order to create a position and ensure get_positions returns it
    await client.place_order("TESTSYM", "buy", 1.0)
    positions = await client.get_positions()
    assert isinstance(positions, list)
    assert any(p["symbol"] == "TESTSYM" for p in positions)
