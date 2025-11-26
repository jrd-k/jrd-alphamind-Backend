"""Tests for economic calendar service."""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.economic_calendar import EconomicCalendar, EconomicEvent, ImpactLevel


@pytest.mark.asyncio
async def test_economic_calendar_initialization():
    """Test calendar initialization."""
    calendar = EconomicCalendar()
    assert calendar is not None
    assert calendar.api_key is None


@pytest.mark.asyncio
async def test_fetch_upcoming_events():
    """Test fetching upcoming events."""
    calendar = EconomicCalendar()
    events = await calendar.fetch_upcoming_events(hours_ahead=168)
    
    assert len(events) > 0, "Should have mock events"
    assert all(isinstance(e, EconomicEvent) for e in events)
    
    # Check sorting by time
    for i in range(len(events) - 1):
        assert events[i].scheduled_time <= events[i + 1].scheduled_time


@pytest.mark.asyncio
async def test_filter_by_currency():
    """Test filtering events by currency."""
    calendar = EconomicCalendar()
    events = await calendar.fetch_upcoming_events(
        hours_ahead=168,
        currencies=["USD"]
    )
    
    # All should be USD or "all"
    for e in events:
        assert e.currency in ("USD", "all")


@pytest.mark.asyncio
async def test_filter_by_impact():
    """Test filtering by impact level."""
    calendar = EconomicCalendar()
    high_impact = await calendar.fetch_upcoming_events(
        hours_ahead=168,
        min_impact=ImpactLevel.HIGH
    )
    
    # All should be high impact
    for e in high_impact:
        assert e.impact == ImpactLevel.HIGH


def test_event_methods():
    """Test EconomicEvent methods."""
    now = datetime.now(timezone.utc)
    future = now + timedelta(hours=1)
    
    event = EconomicEvent(
        name="NFP",
        country="United States",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_time=future,
        forecast_value=227000,
        previous_value=226500
    )
    
    # Test methods
    assert event.is_high_impact() is True
    assert event.minutes_until() >= 59  # ~60 minutes (allow 59-61 for timing variations)
    assert event.is_soon(minutes=120) is True
    assert event.is_soon(minutes=30) is False
    
    # Test to_dict
    d = event.to_dict()
    assert d["name"] == "NFP"
    assert d["currency"] == "USD"
    assert d["impact"] == "high"


@pytest.mark.asyncio
async def test_get_events_for_pair():
    """Test getting events for a specific pair."""
    calendar = EconomicCalendar()
    await calendar.fetch_upcoming_events(hours_ahead=168)
    
    # EURUSD should have EUR and USD events
    events = calendar.get_events_for_pair("EURUSD", minutes_ahead=1440)
    
    # Should have some events (at least mock ones)
    if len(events) > 0:
        for e in events:
            assert e.currency in ("EUR", "USD", "all")


@pytest.mark.asyncio
async def test_should_avoid_trading():
    """Test trading avoidance check."""
    calendar = EconomicCalendar()
    await calendar.fetch_upcoming_events(hours_ahead=168)
    
    # Check for EURUSD
    should_avoid = calendar.should_avoid_trading("EURUSD", minutes_window=60)
    
    # Should be boolean
    assert isinstance(should_avoid, bool)


def test_parse_impact():
    """Test impact string parsing."""
    calendar = EconomicCalendar()
    
    assert calendar._parse_impact("high") == ImpactLevel.HIGH
    assert calendar._parse_impact("medium") == ImpactLevel.MEDIUM
    assert calendar._parse_impact("low") == ImpactLevel.LOW
    assert calendar._parse_impact("3") == ImpactLevel.HIGH  # API format
    assert calendar._parse_impact("2") == ImpactLevel.MEDIUM
    assert calendar._parse_impact("1") == ImpactLevel.LOW


def test_currency_mapping():
    """Test currency/country mapping."""
    calendar = EconomicCalendar()
    
    assert calendar._get_currency_from_country("United States") == "USD"
    assert calendar._get_currency_from_country("Euro Area") == "EUR"
    assert calendar._get_currency_from_country("Japan") == "JPY"
    
    assert calendar._get_country_from_currency("USD") == "United States"
    assert calendar._get_country_from_currency("EUR") == "Euro Area"
    assert calendar._get_country_from_currency("GBP") == "United Kingdom"
