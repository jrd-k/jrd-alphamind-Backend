"""Test Fibonacci endpoint integration."""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core import config

client = TestClient(app)


def _make_candles(n=50, start_price=100.0):
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


def test_fibonacci_compute_endpoint_public():
    """Test POST /api/v1/indicators/compute/fibonacci is public when key not set."""
    config.settings.indicator_api_key = ""
    payload = {
        "ind": {"symbol": "TEST", "source": "fibonacci", "signal": None, "value": {}},
        "candles": _make_candles(50, start_price=1.2),
    }
    resp = client.post("/api/v1/indicators/compute/fibonacci", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "TEST"
    assert data["source"] == "fibonacci"
    print(f"✓ Fibonacci endpoint returned signal: {data.get('signal')}")


def test_fibonacci_compute_endpoint_requires_key():
    """Test that endpoint requires API key when set."""
    config.settings.indicator_api_key = "secret123"
    payload = {
        "ind": {"symbol": "TEST", "source": "fibonacci", "signal": None, "value": {}},
        "candles": _make_candles(50, start_price=1.2),
    }
    # Missing header
    resp = client.post("/api/v1/indicators/compute/fibonacci", json=payload)
    assert resp.status_code == 401
    print("✓ Missing API key rejected")


def test_fibonacci_compute_endpoint_with_key():
    """Test that endpoint works with correct API key."""
    config.settings.indicator_api_key = "secret123"
    payload = {
        "ind": {"symbol": "TEST", "source": "fibonacci", "signal": None, "value": {}},
        "candles": _make_candles(50, start_price=1.2),
    }
    headers = {"X-Indicator-API-Key": "secret123"}
    resp = client.post("/api/v1/indicators/compute/fibonacci", json=payload, headers=headers)
    assert resp.status_code == 200
    print("✓ Valid API key accepted")


def test_fibonacci_response_structure():
    """Test that Fibonacci endpoint returns proper response structure."""
    config.settings.indicator_api_key = ""
    payload = {
        "ind": {"symbol": "EURUSD", "source": "fibonacci", "signal": None, "value": {}},
        "candles": _make_candles(50, start_price=1.2),
    }
    resp = client.post("/api/v1/indicators/compute/fibonacci", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    # Verify structure
    assert "id" in data  # DB ID
    assert "symbol" in data
    assert "source" in data
    assert data["source"] == "fibonacci"
    assert "signal" in data
    assert "value" in data
    
    # Value should contain Fibonacci data
    value = data["value"]
    assert "levels" in value
    assert "swing_high" in value
    assert "swing_low" in value
    assert "current_price" in value
    assert "nearest_level" in value
    assert "signals" in value
    
    print(f"✓ Response structure valid, nearest level: {value.get('nearest_level')}")
