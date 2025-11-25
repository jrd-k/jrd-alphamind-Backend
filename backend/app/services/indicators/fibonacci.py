"""
Fibonacci Retracement Indicator

Computes Fibonacci retracement levels based on recent price swings.
Levels: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
"""

from typing import List, Dict, Any, Tuple


def compute_fibonacci(candles: List[Dict[str, Any]], lookback: int = 50) -> Dict[str, Any]:
    """
    Compute Fibonacci retracement levels from price candles.
    
    Args:
        candles: List of OHLCV candles with 'h', 'l', 'c' keys
        lookback: Number of recent candles to analyze
    
    Returns:
        Dict with:
        - levels: {level_name: price} e.g., {'23.6%': 1.2345}
        - swing_high: Highest price in lookback period
        - swing_low: Lowest price in lookback period
        - swing_range: High - Low
        - current_price: Latest candle close
        - signals: Buy/Sell signals based on price proximity to levels
        - summary: String summary of signals
    """
    if not candles or len(candles) < 2:
        return {"error": "Insufficient candles"}
    
    # Use last N candles for analysis
    analysis_candles = candles[-lookback:]
    
    # Find swing high and low
    highs = [c.get("h", c.get("c", 0)) for c in analysis_candles]
    lows = [c.get("l", c.get("c", 0)) for c in analysis_candles]
    closes = [c.get("c", 0) for c in analysis_candles]
    
    swing_high = max(highs) if highs else 0
    swing_low = min(lows) if lows else 0
    current_price = closes[-1] if closes else 0
    swing_range = swing_high - swing_low
    
    if swing_range == 0:
        return {
            "error": "No price movement",
            "swing_high": swing_high,
            "swing_low": swing_low,
            "current_price": current_price,
        }
    
    # Fibonacci ratios
    ratios = {
        "0%": 0.0,
        "23.6%": 0.236,
        "38.2%": 0.382,
        "50%": 0.5,
        "61.8%": 0.618,
        "78.6%": 0.786,
        "100%": 1.0,
    }
    
    # Calculate retracement levels from swing high
    levels = {}
    for label, ratio in ratios.items():
        level = swing_high - (swing_range * ratio)
        levels[label] = round(level, 8)
    
    # Determine signals based on price proximity to levels
    signals = _determine_signals(current_price, levels, swing_range)
    
    # Calculate distance to nearest level
    distances = {
        label: abs(current_price - level)
        for label, level in levels.items()
    }
    nearest_level = min(distances, key=distances.get)
    
    return {
        "levels": levels,
        "swing_high": round(swing_high, 8),
        "swing_low": round(swing_low, 8),
        "swing_range": round(swing_range, 8),
        "current_price": round(current_price, 8),
        "nearest_level": nearest_level,
        "distance_to_nearest": round(distances[nearest_level], 8),
        "signals": signals,
        "summary": _generate_summary(signals, nearest_level, current_price, levels),
        "timestamp": candles[-1].get("t"),
    }


def _determine_signals(price: float, levels: Dict[str, float], swing_range: float) -> Dict[str, str]:
    """
    Determine buy/sell signals based on price proximity to Fibonacci levels.
    
    - STRONG BUY: Price near 61.8% (strong support)
    - BUY: Price near 38.2% or 50%
    - SELL: Price near 0% (resistance)
    - STRONG SELL: Price near or above swing high
    """
    tolerance = swing_range * 0.02  # 2% tolerance
    
    signals = {}
    
    # Check each level
    for level_name, level_price in levels.items():
        distance = abs(price - level_price)
        if distance < tolerance:
            if level_name == "61.8%":
                signals["strong_support"] = "STRONG BUY at 61.8%"
            elif level_name in ("38.2%", "50%"):
                signals["support"] = f"BUY at {level_name}"
            elif level_name == "0%":
                signals["resistance"] = "SELL at 0%"
            elif level_name == "100%":
                signals["strong_resistance"] = "STRONG SELL at 100%"
    
    # If price is above swing high, strong sell
    if price > levels["100%"]:
        signals["above_swing"] = "STRONG SELL - Above swing high"
    
    # If price is below swing low, strong buy
    if price < levels["0%"]:
        signals["below_swing"] = "STRONG BUY - Below swing low"
    
    return signals


def _generate_summary(signals: Dict[str, str], nearest_level: str, price: float, levels: Dict[str, float]) -> str:
    """Generate a human-readable summary of Fibonacci signals."""
    if not signals:
        return f"Price {price:.4f} between Fibonacci levels"
    
    # Combine all signals
    all_signals = " | ".join(signals.values())
    return f"Nearest level: {nearest_level} ({levels[nearest_level]:.4f}). Signals: {all_signals}"
