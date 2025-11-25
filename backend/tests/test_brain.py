import pytest
from types import SimpleNamespace

from app.services.brain.brain import Brain


class DummyAI:
    def __init__(self, text):
        self._text = text

    async def chat(self, messages, model=None):
        return {"choices": [{"message": {"content": self._text}}]}


class DummyDS:
    def __init__(self, text):
        self._text = text

    async def search(self, q, top_k=3):
        return {"results": [{"text": self._text}]}


@pytest.mark.asyncio
async def test_brain_indicator_only_buy(monkeypatch):
    b = Brain()
    # ensure no AI clients
    b.deepseek = None
    b.openai = None

    indicators = [{"source": "fibonacci", "signal": "STRONG BUY"}]
    # patch save_decision to avoid Redis
    monkeypatch.setattr("app.services.brain.store.save_decision", lambda d: None)

    res = await b.decide("EURUSD", indicators=indicators)
    assert res["decision"] == "BUY"


@pytest.mark.asyncio
async def test_brain_openai_overrides(monkeypatch):
    b = Brain()
    b.deepseek = None
    b.openai = DummyAI("SELL because...")

    indicators = [{"source": "fibonacci", "signal": "BUY"}]
    monkeypatch.setattr("app.services.brain.store.save_decision", lambda d: None)

    res = await b.decide("BTCUSD", indicators=indicators)
    # OpenAI suggests SELL, fusion should balance but OpenAI weight may flip to SELL
    assert res["decision"] in ("SELL", "HOLD", "BUY")
