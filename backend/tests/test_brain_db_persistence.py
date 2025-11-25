import pytest
from datetime import datetime

from app.services.brain.brain import Brain
from app.services.brain import store as brain_store
from app.core.database import engine, SessionLocal
from app.models.orm_models import Base, BrainDecision


@pytest.mark.asyncio
async def test_brain_persists_to_db(monkeypatch, tmp_path):
    # Ensure tables exist for test DB (engine points to settings.database_url)
    Base.metadata.create_all(bind=engine)

    b = Brain()
    b.deepseek = None
    b.openai = None

    indicators = [{"source": "fibonacci", "signal": "STRONG BUY"}]

    # avoid touching Redis during this test - provide async noop
    async def _noop(d):
        return None

    monkeypatch.setattr(brain_store, "save_decision", _noop)

    res = await b.decide("TESTSYM", indicators=indicators)

    # give brief moment for background DB write to complete
    # (Brain schedules DB write as a background task)
    import asyncio

    await asyncio.sleep(0.1)

    s = SessionLocal()
    try:
        row = s.query(BrainDecision).filter_by(symbol="TESTSYM").order_by(BrainDecision.id.desc()).first()
        assert row is not None, "No BrainDecision row was saved"
        assert row.decision == res["decision"]
    finally:
        s.close()
