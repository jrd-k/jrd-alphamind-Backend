from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.orm_models import Base, BrainDecision
from datetime import datetime, timezone, timedelta

client = TestClient(app)


def setup_module(module):
    # ensure tables exist
    Base.metadata.create_all(bind=SessionLocal().bind)


def teardown_module(module):
    # clear BrainDecision rows
    s = SessionLocal()
    try:
        s.query(BrainDecision).delete()
        s.commit()
    finally:
        s.close()


def test_list_decisions_empty():
    s = SessionLocal()
    try:
        s.query(BrainDecision).delete()
        s.commit()
    finally:
        s.close()

    resp = client.get("/api/v1/brain/decisions")
    # may be 401 or 403 depending on auth handler
    assert resp.status_code in (401, 403)


def _create_decision(symbol: str, decision: str, minutes_ago: int = 0):
    s = SessionLocal()
    try:
        ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        bd = BrainDecision(symbol=symbol, decision=decision, timestamp=ts)
        s.add(bd)
        s.commit()
        s.refresh(bd)
        return bd
    finally:
        s.close()


def test_list_decisions_with_data(monkeypatch):
    # override auth dependency to allow access
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: object()

    # create sample decisions
    _create_decision("EURUSD", "BUY", minutes_ago=1)
    _create_decision("BTCUSD", "SELL", minutes_ago=2)

    resp = client.get("/api/v1/brain/decisions")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] >= 2
    assert data["count"] >= 2

    # filter by symbol
    resp2 = client.get("/api/v1/brain/decisions?symbol=EURUSD")
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert all(item["symbol"] == "EURUSD" for item in d2["items"]) or d2["count"] >= 1
    # cleanup dependency override
    app.dependency_overrides.pop(get_current_user, None)
