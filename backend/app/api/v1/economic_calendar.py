"""Economic Calendar API endpoints."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timezone

from app.core.security import get_current_user
from app.services.economic_calendar import EconomicCalendar, ImpactLevel

logger = logging.getLogger(__name__)

router = APIRouter()

# Global calendar instance
_calendar: Optional[EconomicCalendar] = None


def get_calendar() -> EconomicCalendar:
    """Get or create economic calendar instance."""
    global _calendar
    if _calendar is None:
        from app.core.config import settings
        _calendar = EconomicCalendar(api_key=getattr(settings, "trading_economics_key", None))
    return _calendar


@router.get("/economic-calendar/upcoming")
async def get_upcoming_events(
    current_user=Depends(get_current_user),
    hours_ahead: int = Query(168, ge=1, le=720, description="Hours to look ahead (1-720)"),
    currencies: Optional[str] = Query(None, description="Comma-separated currency codes (e.g., USD,EUR,GBP)"),
    min_impact: str = Query("low", pattern="^(low|medium|high)$", description="Minimum impact level"),
) -> dict:
    """Get upcoming economic events.
    
    **Parameters:**
    - `hours_ahead`: How many hours in future to fetch (default 168 = 1 week, max 720 = 30 days)
    - `currencies`: Filter by currencies (comma-separated, e.g., "USD,EUR")
    - `min_impact`: Minimum impact level (low, medium, high)
    
    **Response:**
    ```json
    {
      "total": 15,
      "items": [
        {
          "name": "NFP",
          "country": "United States",
          "currency": "USD",
          "impact": "high",
          "scheduled_time": "2025-11-28T13:30:00+00:00",
          "forecast_value": 227500,
          "previous_value": 227000,
          "source": "trading_economics",
          "minutes_until": 2880
        },
        ...
      ]
    }
    ```
    """
    try:
        calendar = get_calendar()

        # Parse currencies filter
        currency_list = None
        if currencies:
            currency_list = [c.strip().upper() for c in currencies.split(",")]

        # Parse impact level
        try:
            impact_level = ImpactLevel(min_impact)
        except ValueError:
            impact_level = ImpactLevel.LOW

        # Fetch events
        events = await calendar.fetch_upcoming_events(
            hours_ahead=hours_ahead,
            currencies=currency_list,
            min_impact=impact_level,
        )

        return {
            "total": len(events),
            "items": [
                {
                    **e.to_dict(),
                    "minutes_until": e.minutes_until(),
                }
                for e in events
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching economic events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar: {str(e)}")


@router.get("/economic-calendar/pair/{symbol}")
async def get_events_for_pair(
    symbol: str,
    current_user=Depends(get_current_user),
    minutes_ahead: int = Query(60, ge=1, le=1440, description="Minutes to look ahead"),
) -> dict:
    """Get upcoming high-impact events for a specific trading pair.
    
    **Parameters:**
    - `symbol`: Trading pair (e.g., EURUSD, GBPUSD)
    - `minutes_ahead`: Minutes window to check (default 60)
    
    **Response:**
    ```json
    {
      "symbol": "EURUSD",
      "high_impact_events": 2,
      "should_avoid_trading": true,
      "events": [
        {
          "name": "ECB Decision",
          "currency": "EUR",
          "impact": "high",
          "scheduled_time": "2025-11-27T13:45:00+00:00",
          "minutes_until": 45
        }
      ]
    }
    ```
    """
    try:
        calendar = get_calendar()

        # Normalize symbol
        symbol = symbol.upper()
        if len(symbol) != 6:
            raise HTTPException(status_code=400, detail="Symbol must be 6 characters (e.g., EURUSD)")

        # Fetch events for pair
        events = calendar.get_events_for_pair(symbol, minutes_ahead)
        should_avoid = calendar.should_avoid_trading(symbol, minutes_ahead)
        high_impact_count = sum(1 for e in events if e.is_high_impact())

        return {
            "symbol": symbol,
            "high_impact_events": high_impact_count,
            "should_avoid_trading": should_avoid,
            "events": [
                {
                    **e.to_dict(),
                    "minutes_until": e.minutes_until(),
                }
                for e in events
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching events for pair {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.get("/economic-calendar/risk-check")
async def check_trading_risk(
    current_user=Depends(get_current_user),
    symbol: str = Query(..., description="Trading pair"),
    minutes_ahead: int = Query(60, ge=1, le=1440, description="Minutes to check"),
) -> dict:
    """Quick risk check: is it safe to trade this pair right now?
    
    **Response:**
    ```json
    {
      "symbol": "EURUSD",
      "safe_to_trade": false,
      "reason": "High-impact ECB Decision in 45 minutes",
      "events_count": 1,
      "events": [...]
    }
    ```
    """
    try:
        calendar = get_calendar()
        symbol = symbol.upper()

        events = calendar.get_events_for_pair(symbol, minutes_ahead)
        should_avoid = calendar.should_avoid_trading(symbol, minutes_ahead)

        reason = None
        if should_avoid:
            high_impact = [e for e in events if e.is_high_impact()]
            if high_impact:
                next_event = high_impact[0]
                mins = next_event.minutes_until()
                reason = f"High-impact {next_event.name} in {mins} minutes"

        return {
            "symbol": symbol,
            "safe_to_trade": not should_avoid,
            "reason": reason,
            "events_count": len(events),
            "events": [
                {
                    **e.to_dict(),
                    "minutes_until": e.minutes_until(),
                }
                for e in events
            ],
        }

    except Exception as e:
        logger.error(f"Error checking trading risk: {e}")
        raise HTTPException(status_code=500, detail=f"Risk check failed: {str(e)}")
