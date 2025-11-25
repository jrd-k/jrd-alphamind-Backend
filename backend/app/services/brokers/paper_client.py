import random
import datetime
from typing import Optional, Dict, Any
from .base import BrokerClient


class PaperTradingClient(BrokerClient):
    """Paper trading (simulated) broker client.
    
    Useful for testing without real broker connections or risking money.
    Simulates fills at random prices and maintains fictional account state.
    """

    def __init__(self):
        self.balance = 10000.0
        self.equity = 10000.0
        self.positions = {}

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Simulate order fill at random price."""
        # Simulate a fill price between 1.05 and 1.10 for demo
        fill_price = price or round(random.uniform(1.05, 1.10), 5)

        # Update fictional positions
        if symbol not in self.positions:
            self.positions[symbol] = {"volume": 0, "entry_price": 0}

        if side == "buy":
            self.positions[symbol]["volume"] += qty
            self.positions[symbol]["entry_price"] = fill_price
        else:  # sell
            self.positions[symbol]["volume"] -= qty

        return {
            "broker": "paper",
            "order_id": random.randint(10000, 99999),
            "symbol": symbol,
            "side": side,
            "volume": qty,
            "price": fill_price,
            "status": "filled",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    async def get_balance(self) -> Dict[str, Any]:
        """Return simulated balance."""
        return {
            "balance": self.balance,
            "equity": self.equity,
            "margin_used": 0.0,
            "margin_free": self.balance,
            "currency": "USD",
        }

    async def get_positions(self) -> list:
        """Return simulated open positions."""
        result = []
        for symbol, pos in self.positions.items():
            if pos["volume"] != 0:
                result.append(
                    {
                        "symbol": symbol,
                        "side": "buy" if pos["volume"] > 0 else "sell",
                        "volume": abs(pos["volume"]),
                        "price": pos["entry_price"],
                        "profit_loss": random.uniform(-100, 100),
                    }
                )
        return result
