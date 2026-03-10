"""Paper Trading Client - Simulated broker for testing."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


class PaperTradingClient:
    """Simulated broker client for paper trading."""

    def __init__(self):
        self.positions = []
        self.balance = 10000.0
        self.equity = 10000.0

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Simulate placing an order."""
        order_id = f"paper-{uuid.uuid4().hex[:8]}"

        # Simulate order execution
        exec_price = price or 1.0  # Default price for simulation

        # Add to positions if it's a buy
        if side.lower() == "buy":
            self.positions.append({
                "symbol": symbol,
                "side": "buy",
                "qty": qty,
                "price": exec_price,
                "order_id": order_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return {
            "broker": "paper",
            "order_id": order_id,
            "status": "filled",
            "price": exec_price,
            "volume": qty,
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        return [
            {
                "broker": "paper",
                "symbol": pos["symbol"],
                "side": pos["side"],
                "qty": pos["qty"],
                "price": pos["price"],
                "current_price": pos["price"],  # No price change in paper trading
                "pnl": 0.0,  # No P&L calculation
                "timestamp": pos["timestamp"],
            }
            for pos in self.positions
        ]

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        return {
            "broker": "paper",
            "balance": self.balance,
            "equity": self.equity,
            "margin_used": 0.0,
            "margin_free": self.balance,
            "currency": "USD",
            "leverage": 1,
            "account_number": "PAPER001",
        }

    async def get_historical_data(self, symbol: str, timeframe: str = "M1", bars: int = 100) -> List[Dict[str, Any]]:
        """Get simulated historical data."""
        # Return empty list for paper trading
        return []

    def close(self):
        """Close paper trading client."""
        logger.info("Paper trading client closed")
