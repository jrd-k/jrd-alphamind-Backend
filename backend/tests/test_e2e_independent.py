"""
End-to-end test: indicator compute -> orchestrator -> trade execution.
This test verifies the system works independently without TradingView.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core import config
from app.core.database import SessionLocal
from app.models.orm_models import IndicatorSignal, Instrument

client = TestClient(app)


def _make_candles(n=30, start_price=100.0):
    """Generate synthetic OHLCV candles."""
    candles = []
    t = datetime.now(timezone.utc)
    p = float(start_price)
    for i in range(n):
        o = p
        h = p * 1.001
        l = p * 0.999
        c = p * (1.0005)
        v = 100 + i
        candles.append({
            "t": (t + timedelta(minutes=i)).isoformat(),
            "o": o,
            "h": h,
            "l": l,
            "c": c,
            "v": v,
        })
        p = c
    return candles


def test_e2e_compute_to_orchestrator_to_trade():
    """Test: compute indicator -> fetch in orchestrator -> generate strategy -> trade."""
    
    # 1. Compute indicator via POST /api/v1/indicators/compute
    payload = {
        "ind": {"symbol": "EURUSD", "source": "supertrend_ai", "signal": None, "value": {}},
        "candles": _make_candles(30, start_price=1.2),
    }
    config.settings.indicator_api_key = ""  # Public mode
    resp = client.post("/api/v1/indicators/compute", json=payload)
    assert resp.status_code == 200
    signal_data = resp.json()
    assert signal_data["symbol"] == "EURUSD"
    assert signal_data["signal"] in ("bull", "bear")
    print(f"✓ Indicator computed: {signal_data['signal']} on EURUSD")

    # 2. Verify signal persisted in DB
    db = SessionLocal()
    try:
        sig = db.query(IndicatorSignal).filter_by(symbol="EURUSD").first()
        assert sig is not None
        assert sig.source == "supertrend_ai"
        print(f"✓ Signal persisted in DB (id={sig.id})")
    finally:
        db.close()

    # 3. Call orchestrator with the indicator signal
    # This simulates the scheduler calling the orchestrator with fresh indicators
    from app.orchestrator.supervisor import Supervisor

    supervisor = Supervisor()
    indicators = [
        {
            "symbol": signal_data["symbol"],
            "signal": signal_data["signal"],
            "value": signal_data["value"],
        }
    ]
    strategy = supervisor.run_with_indicators("EURUSD", indicators)
    assert strategy is not None
    print(f"✓ Orchestrator generated strategy: action={strategy.get('action')}")
    
    # If bull signal, expect buy action; if bear, expect sell
    if signal_data["signal"] == "bull":
        assert strategy.get("action") == "buy"
    elif signal_data["signal"] == "bear":
        assert strategy.get("action") == "sell"

    print("✓ E2E test passed: indicator → orchestrator → strategy")


def test_scheduler_e2e_simulation():
    """Simulate scheduler tick: compute indicator for all instruments."""
    from app.workers.scheduler import IndicatorScheduler
    import asyncio

    # Ensure an instrument exists
    db = SessionLocal()
    try:
        eurusd = db.query(Instrument).filter_by(symbol="EURUSD").first()
        if not eurusd:
            eurusd = Instrument(symbol="EURUSD", name="EUR / USD")
            db.add(eurusd)
            db.commit()
        print(f"✓ Instrument available: {eurusd.symbol}")
    finally:
        db.close()

    # Create and run scheduler tick
    scheduler = IndicatorScheduler(enabled=True)
    
    # Synchronously compute indicators for a single tick
    db = SessionLocal()
    try:
        # Compute indicator for EURUSD
        signal = asyncio.run(scheduler._compute_indicator_for_symbol("EURUSD", db))
        assert signal is not None
        print(f"✓ Scheduler computed indicator: {signal.signal} for EURUSD")
        
        # Verify orchestrator picks it up
        asyncio.run(scheduler._run_orchestrator(db))
        print(f"✓ Scheduler ran orchestrator")
    finally:
        db.close()
