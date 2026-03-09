"""PyTrader MT4/MT5 broker client integration.

This client connects to MT4/MT5 terminals via PyTrader API (TCP socket to EA)
and executes orders, retrieves balance/positions, and manages account information.

Requires:
- MetaTrader 4 or 5 terminal running locally or remotely
- PyTrader EA installed in the terminal
- PyTrader Python package
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from .base import BrokerClient

try:
    import PyTrader as MT
    PYTRADER_AVAILABLE = True
except ImportError:
    PYTRADER_AVAILABLE = False
    logging.warning("PyTrader package not found. Install with: pip install PyTrader")


logger = logging.getLogger(__name__)


class PyTraderClient(BrokerClient):
    """PyTrader client for MT4/MT5 connectivity via TCP socket to EA.
    
    Connects to a running MT4/MT5 terminal with PyTrader EA installed.
    Supports both demo and live accounts.
    """

    def __init__(self, host: str = "localhost", port: int = 1122):
        """Initialize PyTrader client.
        
        Args:
            host: MT4/MT5 terminal host (default: localhost)
            port: PyTrader EA port (default: 1122)
        """
        if not PYTRADER_AVAILABLE:
            raise RuntimeError(
                "PyTrader package not found. Install PyTrader EA and Python package."
            )
        
        self.host = host
        self.port = port
        self._connected = False
        self._connect()

    def _connect(self):
        """Initialize and connect to PyTrader EA."""
        try:
            # Connect to PyTrader EA via TCP
            MT.connect(host=self.host, port=self.port)
            self._connected = True
            logger.info(f"Connected to PyTrader EA at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error connecting to PyTrader EA: {e}")
            self._connected = False

    def _ensure_connected(self) -> bool:
        """Ensure PyTrader is connected and ready."""
        if not self._connected:
            self._connect()
        return self._connected

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Place an order on MT5.
        
        Args:
            symbol: Trading pair (e.g., 'EURUSD')
            side: 'buy' or 'sell'
            qty: Quantity to trade (in lots)
            price: Limit price (for limit orders); ignored for market orders
            order_type: 'market' or 'limit'
            
        Returns:
            Dict with order details: order_id, status, price, volume, timestamp
        """
        if not self._ensure_connected():
            raise RuntimeError("PyTrader not connected")

        try:
            # Normalize symbol
            instrument = symbol.upper()

            # Map order type
            if side.lower() == "buy":
                ordertype = "buy"
            elif side.lower() == "sell":
                ordertype = "sell"
            else:
                raise ValueError(f"Invalid side: {side}")

            # Use PyTrader API to place order
            order_result = MT.Open_order(
                instrument=instrument,
                ordertype=ordertype,
                volume=qty,
                price=price if order_type.lower() == "limit" else None,
                slippage=0
            )

            if order_result:
                logger.info(f"Order placed successfully: {order_result}")
                return {
                    "broker": "pytrader",
                    "order_id": order_result.get("ticket"),
                    "status": "filled",
                    "price": order_result.get("price"),
                    "volume": qty,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                logger.error("Order placement failed")
                return {
                    "broker": "pytrader",
                    "order_id": None,
                    "status": "failed",
                    "error": "Order placement failed",
                }

            return {
                "broker": "mt5",
                "order_id": str(result.order),
                "symbol": mt5_symbol,
                "side": side,
                "volume": qty,
                "price": order_price,
                "status": "filled",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "comment": result.comment,
            }

        except Exception as e:
            logger.error(f"Error placing order on MT5: {e}")
            return {
                "broker": "mt5",
                "order_id": None,
                "status": "error",
                "error": str(e),
            }

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance and account info from PyTrader.
        
        Returns:
            Dict with balance, equity, margin info
        """
        if not self._ensure_connected():
            raise RuntimeError("PyTrader not connected")

        try:
            account_info = MT.Get_account_info()
            if account_info:
                return {
                    "broker": "pytrader",
                    "balance": account_info.get("balance"),
                    "equity": account_info.get("equity"),
                    "margin_used": account_info.get("margin"),
                    "margin_free": account_info.get("margin_free"),
                    "currency": account_info.get("currency"),
                    "leverage": account_info.get("leverage"),
                    "account_number": account_info.get("login"),
                }
            else:
                logger.error("Failed to get account info")
                return {}

        except Exception as e:
            logger.error(f"Error getting balance from PyTrader: {e}")
            return {"error": str(e)}

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions from PyTrader.
        
        Returns:
            List of open positions with symbol, side, volume, price, profit/loss
        """
        if not self._ensure_connected():
            raise RuntimeError("PyTrader not connected")

        try:
            positions = MT.Get_positions()
            if positions:
                result = []
                for pos in positions:
                    result.append({
                        "symbol": pos.get("symbol"),
                        "side": "buy" if pos.get("type") == 0 else "sell",  # Assuming 0=buy, 1=sell
                        "volume": pos.get("volume"),
                        "price": pos.get("price_open"),
                        "profit_loss": pos.get("profit"),
                        "open_time": pos.get("time"),
                    })
                return result
            else:
                logger.info("No open positions")
                return []

        except Exception as e:
            logger.error(f"Error getting positions from PyTrader: {e}")
            return []

    async def get_historical_data(self, symbol: str, timeframe: str = "M1", bars: int = 100) -> List[Dict[str, Any]]:
        """Get historical bar data from PyTrader.
        
        Args:
            symbol: Trading pair (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., 'M1', 'H1', 'D1')
            bars: Number of bars to retrieve
            
        Returns:
            List of OHLCV data
        """
        if not self._ensure_connected():
            raise RuntimeError("PyTrader not connected")

        try:
            data = MT.Get_last_x_bars_from_now(symbol, timeframe, bars)
            if data:
                return data
            else:
                logger.error(f"Failed to get historical data for {symbol}")
                return []

        except Exception as e:
            logger.error(f"Error getting historical data from PyTrader: {e}")
            return []

    def close(self):
        """Close PyTrader connection."""
        if PYTRADER_AVAILABLE:
            MT.disconnect()
            logger.info("PyTrader connection closed")
