from fastapi.testclient import TestClient
from app.main import app
from app.core import config
from datetime import datetime, timedelta, timezone

client = TestClient(app)


def _make_candles(n=30, start_price=100.0):
    # simple synthetic increasing candles
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


def _make_payload():
    ind = {"symbol": "TEST", "source": "supertrend_ai", "signal": "bull", "value": {}}
    candles = _make_candles(30)
    return {"ind": ind, "candles": candles}


def test_compute_endpoint_public_when_key_empty():
    # ensure the indicator key is empty (public mode)
    config.settings.indicator_api_key = ""
    resp = client.post("/api/v1/indicators/compute", json=_make_payload())
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("symbol") == "TEST"


def test_compute_endpoint_requires_key_when_set_and_missing():
    config.settings.indicator_api_key = "secret-abc"
    # missing header
    resp = client.post("/api/v1/indicators/compute", json=_make_payload())
    assert resp.status_code == 401


def test_compute_endpoint_with_valid_key():
    config.settings.indicator_api_key = "secret-abc"
    headers = {"X-Indicator-API-Key": "secret-abc"}
    resp = client.post("/api/v1/indicators/compute", json=_make_payload(), headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("symbol") == "TEST"
