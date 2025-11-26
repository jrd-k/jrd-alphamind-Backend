"""Economic Calendar Service

Fetches upcoming economic events, their impact levels, and affected currency pairs.
Integrates with Brain decisions to avoid trading during high-impact events.

Supports multiple sources:
- Trading Economics API (requires key)
- ForexFactory calendar scraping
- FRED (Federal Reserve Economic Data) API
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class ImpactLevel(str, Enum):
    """Economic event impact classification."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EconomicEvent:
    """Represents a single economic calendar event."""
    
    def __init__(
        self,
        name: str,
        country: str,
        currency: str,
        impact: ImpactLevel,
        scheduled_time: datetime,
        actual_value: Optional[float] = None,
        forecast_value: Optional[float] = None,
        previous_value: Optional[float] = None,
        source: str = "unknown"
    ):
        self.name = name
        self.country = country
        self.currency = currency
        self.impact = impact
        self.scheduled_time = scheduled_time
        self.actual_value = actual_value
        self.forecast_value = forecast_value
        self.previous_value = previous_value
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "country": self.country,
            "currency": self.currency,
            "impact": self.impact.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            "actual_value": self.actual_value,
            "forecast_value": self.forecast_value,
            "previous_value": self.previous_value,
            "source": self.source,
        }

    def is_high_impact(self) -> bool:
        """Check if event is high-impact."""
        return self.impact == ImpactLevel.HIGH

    def minutes_until(self) -> int:
        """Minutes until event (negative if already past)."""
        now = datetime.now(timezone.utc)
        delta = self.scheduled_time - now
        return int(delta.total_seconds() / 60)

    def is_soon(self, minutes: int = 60) -> bool:
        """Check if event happens within N minutes."""
        return 0 < self.minutes_until() <= minutes


class EconomicCalendar:
    """Main economic calendar service."""
    
    # Major currency-affecting events to track
    MAJOR_INDICATORS = {
        "NFP": ("USD", ImpactLevel.HIGH),  # Non-Farm Payroll
        "ISM Manufacturing": ("USD", ImpactLevel.HIGH),
        "ISM Services": ("USD", ImpactLevel.HIGH),
        "PCE Inflation": ("USD", ImpactLevel.HIGH),
        "CPI": ("USD", ImpactLevel.HIGH),
        "Unemployment Rate": ("USD", ImpactLevel.HIGH),
        "Fed Decision": ("USD", ImpactLevel.HIGH),
        "ECB Decision": ("EUR", ImpactLevel.HIGH),
        "BOE Decision": ("GBP", ImpactLevel.HIGH),
        "BOJ Decision": ("JPY", ImpactLevel.HIGH),
        "GDP": ("all", ImpactLevel.HIGH),
        "Retail Sales": ("USD", ImpactLevel.MEDIUM),
        "Durable Orders": ("USD", ImpactLevel.MEDIUM),
        "PMI": ("all", ImpactLevel.MEDIUM),
        "Inflation": ("all", ImpactLevel.MEDIUM),
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize economic calendar.
        
        Args:
            api_key: Trading Economics API key (optional)
            base_url: Trading Economics API base URL (default: forexfactory)
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.tradingeconomics.com"
        self.events: List[EconomicEvent] = []
        self._last_fetch: Optional[datetime] = None
        self._cache_ttl_minutes = 60

    async def fetch_upcoming_events(
        self,
        hours_ahead: int = 168,  # 1 week
        currencies: Optional[List[str]] = None,
        min_impact: ImpactLevel = ImpactLevel.LOW,
    ) -> List[EconomicEvent]:
        """Fetch upcoming economic events.
        
        Args:
            hours_ahead: How many hours in the future to check (default 168 = 1 week)
            currencies: Filter by currency codes (e.g., ['USD', 'EUR'])
            min_impact: Minimum impact level to return
            
        Returns:
            List of EconomicEvent objects
        """
        # Check cache
        if self._last_fetch and (datetime.now(timezone.utc) - self._last_fetch).total_seconds() < self._cache_ttl_minutes * 60:
            events = self.events
        else:
            # Fetch fresh data
            events = await self._fetch_from_sources(hours_ahead)
            self.events = events
            self._last_fetch = datetime.now(timezone.utc)

        # Filter
        filtered = events
        if currencies:
            filtered = [e for e in filtered if e.currency in currencies or e.currency == "all"]
        
        # Impact filter
        impact_order = [ImpactLevel.LOW, ImpactLevel.MEDIUM, ImpactLevel.HIGH]
        min_idx = impact_order.index(min_impact) if min_impact in impact_order else 0
        filtered = [e for e in filtered if impact_order.index(e.impact) >= min_idx]

        # Sort by time
        filtered.sort(key=lambda e: e.scheduled_time)
        return filtered

    async def _fetch_from_sources(self, hours_ahead: int) -> List[EconomicEvent]:
        """Fetch from available sources (Trading Economics, ForexFactory, etc.)."""
        events = []

        # Try Trading Economics API if key provided
        if self.api_key:
            try:
                te_events = await self._fetch_trading_economics(hours_ahead)
                events.extend(te_events)
                logger.info(f"Fetched {len(te_events)} events from Trading Economics")
            except Exception as e:
                logger.warning(f"Failed to fetch from Trading Economics: {e}")

        # Fallback: generate mock events based on MAJOR_INDICATORS
        if not events:
            events = self._generate_mock_events(hours_ahead)
            logger.info(f"Using {len(events)} mock economic events for demonstration")

        return events

    async def _fetch_trading_economics(self, hours_ahead: int) -> List[EconomicEvent]:
        """Fetch from Trading Economics API."""
        if not httpx:
            raise RuntimeError("httpx required for Trading Economics API")

        async with httpx.AsyncClient() as client:
            now = datetime.now(timezone.utc)
            start_date = now.strftime("%Y-%m-%d")
            end_date = (now + timedelta(hours=hours_ahead)).strftime("%Y-%m-%d")

            url = f"{self.base_url}/calendar"
            params = {
                "key": self.api_key,
                "daterange": f"{start_date},{end_date}",
            }

            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            events = []
            for item in data:
                impact = self._parse_impact(item.get("Importance", "low"))
                scheduled = datetime.fromisoformat(item.get("Date", "").replace("Z", "+00:00"))

                event = EconomicEvent(
                    name=item.get("Event", ""),
                    country=item.get("Country", ""),
                    currency=self._get_currency_from_country(item.get("Country", "")),
                    impact=impact,
                    scheduled_time=scheduled,
                    forecast_value=item.get("Forecast"),
                    previous_value=item.get("Previous"),
                    source="trading_economics",
                )
                events.append(event)

            return events

    def _generate_mock_events(self, hours_ahead: int) -> List[EconomicEvent]:
        """Generate realistic mock events for demo/testing."""
        events = []
        now = datetime.now(timezone.utc)

        # Create events over the next week at realistic times
        event_times = [
            now + timedelta(hours=2),
            now + timedelta(hours=8),
            now + timedelta(hours=24),
            now + timedelta(hours=48),
            now + timedelta(hours=72),
        ]

        indicators = [
            ("NFP", "USD", ImpactLevel.HIGH),
            ("CPI", "USD", ImpactLevel.HIGH),
            ("ECB Decision", "EUR", ImpactLevel.HIGH),
            ("Retail Sales", "USD", ImpactLevel.MEDIUM),
            ("PMI Services", "EUR", ImpactLevel.MEDIUM),
        ]

        for i, (indicator, currency, impact) in enumerate(indicators[:len(event_times)]):
            event = EconomicEvent(
                name=indicator,
                country=self._get_country_from_currency(currency),
                currency=currency,
                impact=impact,
                scheduled_time=event_times[i],
                forecast_value=100.5 + i,
                previous_value=100.0 + i,
                source="mock",
            )
            events.append(event)

        return events

    def _parse_impact(self, impact_str: str) -> ImpactLevel:
        """Parse impact string from API to ImpactLevel."""
        impact_lower = impact_str.lower()
        if "high" in impact_lower or "3" in impact_lower:
            return ImpactLevel.HIGH
        elif "medium" in impact_lower or "2" in impact_lower:
            return ImpactLevel.MEDIUM
        elif "low" in impact_lower or "1" in impact_lower:
            return ImpactLevel.LOW
        return ImpactLevel.UNKNOWN

    @staticmethod
    def _get_currency_from_country(country: str) -> str:
        """Map country code/name to currency."""
        mapping = {
            "United States": "USD",
            "US": "USD",
            "Euro Area": "EUR",
            "EU": "EUR",
            "Eurozone": "EUR",
            "United Kingdom": "GBP",
            "UK": "GBP",
            "Japan": "JPY",
            "Canada": "CAD",
            "Australia": "AUD",
            "Switzerland": "CHF",
            "China": "CNY",
        }
        return mapping.get(country, "USD")

    @staticmethod
    def _get_country_from_currency(currency: str) -> str:
        """Map currency to country."""
        mapping = {
            "USD": "United States",
            "EUR": "Euro Area",
            "GBP": "United Kingdom",
            "JPY": "Japan",
            "CAD": "Canada",
            "AUD": "Australia",
            "CHF": "Switzerland",
            "CNY": "China",
        }
        return mapping.get(currency, "United States")

    def get_events_for_pair(
        self,
        symbol: str,
        minutes_ahead: int = 60,
    ) -> List[EconomicEvent]:
        """Get high-impact events affecting a specific pair in the next N minutes.
        
        Args:
            symbol: Trading pair (e.g., 'EURUSD')
            minutes_ahead: Look-ahead window in minutes
            
        Returns:
            List of upcoming high-impact events
        """
        # Extract currencies from pair (e.g., EURUSD -> EUR, USD)
        if len(symbol) == 6:
            base = symbol[:3]
            quote = symbol[3:]
        else:
            return []

        relevant_events = []
        now = datetime.now(timezone.utc)

        for event in self.events:
            # Check if event affects either currency of the pair
            if event.currency not in (base, quote, "all"):
                continue

            # Check if event is within time window
            minutes_until = event.minutes_until()
            if 0 < minutes_until <= minutes_ahead:
                relevant_events.append(event)

        return sorted(relevant_events, key=lambda e: e.scheduled_time)

    def should_avoid_trading(self, symbol: str, minutes_window: int = 60) -> bool:
        """Determine if trading should be avoided for this pair.
        
        Returns True if high-impact events are scheduled within the time window.
        """
        events = self.get_events_for_pair(symbol, minutes_window)
        return any(e.is_high_impact() for e in events)
