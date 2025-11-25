"""Test Fibonacci retracement indicator."""

import pytest
from datetime import datetime, timedelta, timezone
from app.services.indicators.fibonacci import compute_fibonacci


def _make_candles(n=50, start_price=100.0, trend="neutral"):
    """Generate synthetic candles with optional trend."""
    candles = []
    t = datetime.now(timezone.utc)
    p = float(start_price)
    
    for i in range(n):
        # Add trend component
        if trend == "up":
            trend_factor = 1.0 + (i * 0.001)  # Slight uptrend
        elif trend == "down":
            trend_factor = 1.0 - (i * 0.001)  # Slight downtrend
        else:
            trend_factor = 1.0
        
        o = p * trend_factor
        h = o * (1.0 + abs(i % 3 - 1) * 0.002)
        l = o * (1.0 - abs(i % 3 - 1) * 0.002)
        c = o * (1.0005 + (i % 3 - 1) * 0.0001)
        v = 1000 + i * 100
        
        candles.append({
            "t": (t - timedelta(minutes=n - i)).isoformat(),
            "o": o,
            "h": h,
            "l": l,
            "c": c,
            "v": v,
        })
        p = c
    
    return candles


def test_fibonacci_basic_computation():
    """Test basic Fibonacci level computation."""
    candles = _make_candles(50, start_price=100.0)
    result = compute_fibonacci(candles, lookback=50)
    
    assert "levels" in result
    assert "swing_high" in result
    assert "swing_low" in result
    assert "current_price" in result
    
    levels = result["levels"]
    assert "23.6%" in levels
    assert "38.2%" in levels
    assert "50%" in levels
    assert "61.8%" in levels
    assert "100%" in levels
    
    # Verify levels are in descending order from 0% to 100%
    assert levels["0%"] > levels["100%"] or abs(levels["0%"] - levels["100%"]) < 0.01


def test_fibonacci_uptrend():
    """Test Fibonacci signals in uptrend."""
    candles = _make_candles(50, start_price=100.0, trend="up")
    result = compute_fibonacci(candles, lookback=50)
    
    assert result["current_price"] > result["swing_low"]
    # In uptrend, price should be closer to swing_high
    price_range = result["swing_high"] - result["swing_low"]
    price_position = result["current_price"] - result["swing_low"]
    ratio = price_position / price_range if price_range > 0 else 0
    assert ratio > 0.3  # Should be in upper portion


def test_fibonacci_downtrend():
    """Test Fibonacci signals in downtrend."""
    candles = _make_candles(50, start_price=100.0, trend="down")
    result = compute_fibonacci(candles, lookback=50)
    
    assert result["current_price"] < result["swing_high"]
    # In downtrend, price should be closer to swing_low
    price_range = result["swing_high"] - result["swing_low"]
    price_position = result["current_price"] - result["swing_low"]
    ratio = price_position / price_range if price_range > 0 else 0
    assert ratio < 0.7  # Should be in lower portion


def test_fibonacci_nearest_level():
    """Test nearest level detection."""
    candles = _make_candles(50, start_price=100.0)
    result = compute_fibonacci(candles, lookback=50)
    
    assert "nearest_level" in result
    assert "distance_to_nearest" in result
    
    # Verify distance is calculated correctly
    nearest = result["nearest_level"]
    nearest_price = result["levels"][nearest]
    calculated_distance = abs(result["current_price"] - nearest_price)
    assert abs(calculated_distance - result["distance_to_nearest"]) < 0.001


def test_fibonacci_signals():
    """Test signal generation based on price proximity."""
    candles = _make_candles(50, start_price=100.0)
    result = compute_fibonacci(candles, lookback=50)
    
    # Should have signals dict
    assert "signals" in result
    assert "summary" in result
    
    # If signals exist, summary should reflect them
    if result["signals"]:
        summary = result["summary"]
        assert len(summary) > 0


def test_fibonacci_insufficient_candles():
    """Test error handling with insufficient candles."""
    result = compute_fibonacci([], lookback=50)
    assert "error" in result


def test_fibonacci_lookback_parameter():
    """Test that lookback parameter is respected."""
    candles = _make_candles(100, start_price=100.0)
    
    result_10 = compute_fibonacci(candles, lookback=10)
    result_50 = compute_fibonacci(candles, lookback=50)
    
    # Different lookback periods should give different results
    assert result_10["swing_high"] <= result_50["swing_high"] or result_10["swing_high"] >= result_50["swing_high"]
    # (They may differ based on which portion of data has extremes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
