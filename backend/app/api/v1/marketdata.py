from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta
import random

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Get current quote for a symbol"""
    # Generate realistic mock data
    base_price = 100 + random.uniform(-20, 20)
    change = random.uniform(-5, 5)
    return {
        "symbol": symbol.upper(),
        "price": round(base_price, 2),
        "change": round(change, 2),
        "changePercent": round((change / base_price) * 100, 2)
    }


@router.get("")
async def get_stocks(
    symbol: Optional[str] = Query(None, description="Stock symbol"),
    interval: Optional[str] = Query("daily", description="Data interval")
):
    """Get stock data for charts - Frontend compatible endpoint"""
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol parameter required")

    # Generate mock historical data
    end_date = datetime.now()
    if interval == "daily":
        start_date = end_date - timedelta(days=365)
        periods = 365
    elif interval == "hourly":
        start_date = end_date - timedelta(days=30)
        periods = 720  # 30 days * 24 hours
    else:
        start_date = end_date - timedelta(days=90)
        periods = 90

    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, periods=periods)

    # Generate realistic price data
    base_price = 100 + random.uniform(50, 200)
    prices = []
    current_price = base_price

    for i, date in enumerate(dates):
        # Add some trend and volatility
        trend = 0.001 * (i - periods/2)  # Slight upward trend
        noise = random.gauss(0, 0.02)  # 2% daily volatility
        current_price *= (1 + trend + noise)

        # Generate OHLC data
        high = current_price * (1 + abs(random.gauss(0, 0.01)))
        low = current_price * (1 - abs(random.gauss(0, 0.01)))
        open_price = current_price * (1 + random.gauss(0, 0.005))
        close = current_price

        prices.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": random.randint(100000, 1000000)
        })

    return {
        "symbol": symbol.upper(),
        "data": prices,
        "interval": interval
    }


@router.post("/data")
async def submit_data(data: dict):
    """Generic data submission endpoint for frontend forms"""
    # Process and store data as needed
    return {
        "success": True,
        "message": "Data submitted successfully",
        "received": data
    }


# Additional frontend-compatible endpoints
@router.get("/stocks")
async def get_stocks_list():
    """Get list of available stocks"""
    return {
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "EURUSD", "name": "Euro vs US Dollar"},
            {"symbol": "GBPUSD", "name": "British Pound vs US Dollar"}
        ]
    }
