import os
from typing import Optional, Dict, Any
import httpx
from .base import BrokerClient


class ExnessClient(BrokerClient):
    """Exness broker integration via REST API.
    
    Requires EXNESS_API_KEY and optionally EXNESS_BASE_URL in environment.
    Defaults to demo server if EXNESS_BASE_URL not set.
    """

    def __init__(self):
        self.base_url = os.getenv("EXNESS_BASE_URL", "https://api.exness-demo.com")
        self.token = os.getenv("EXNESS_API_KEY", "demo-token")
        self.timeout = 10

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Place order on Exness."""
        payload = {
            "symbol": symbol,
            "side": side,
            "volume": qty,
            "type": order_type,
        }
        if price and order_type == "limit":
            payload["price"] = price

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/api/v1/orders",
                json=payload,
                headers=headers,
            )
            r.raise_for_status()
            result = r.json()
            return {
                "broker": "exness",
                "order_id": result.get("id"),
                "status": result.get("status", "pending"),
                "price": result.get("price"),
                "volume": result.get("volume"),
                "symbol": result.get("symbol"),
                "side": result.get("side"),
                "timestamp": result.get("created_at"),
            }

    async def get_balance(self) -> Dict[str, Any]:
        """Fetch account balance from Exness."""
        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(
                f"{self.base_url}/api/v1/account/balance",
                headers=headers,
            )
            r.raise_for_status()
            result = r.json()
            return {
                "balance": result.get("balance", 0.0),
                "equity": result.get("equity", 0.0),
                "margin_used": result.get("margin_used", 0.0),
                "margin_free": result.get("margin_free", 0.0),
                "currency": result.get("currency", "USD"),
            }

    async def get_positions(self) -> list:
        """Fetch open positions from Exness."""
        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(
                f"{self.base_url}/api/v1/positions",
                headers=headers,
            )
            r.raise_for_status()
            positions = r.json()
            return [
                {
                    "symbol": p.get("symbol"),
                    "side": p.get("side"),
                    "volume": p.get("volume"),
                    "price": p.get("open_price"),
                    "profit_loss": p.get("profit_loss"),
                }
                for p in positions
            ]
