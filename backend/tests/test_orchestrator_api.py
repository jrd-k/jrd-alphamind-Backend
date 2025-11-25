import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_generate_strategy_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.post("/api/v1/orchestrator/generate_strategy", params={"market": "EURUSD"})
        assert resp.status_code == 200
        data = resp.json()
        assert "accepted" in data
        # if accepted, ensure backtest results are present
        if data.get("accepted"):
            assert "pnl" in data and "trades" in data
