"""MetaTrader 5 (MT5) broker client integration.

This client connects to MT5 terminals (demo or live accounts) and executes orders,
retrieves balance/positions, and manages account information.

Requires:
- MetaTrader 5 terminal running locally or remotely
- MT5 Python package: pip install MetaTrader5
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from .base import BrokerClient

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logging.warning("MetaTrader5 package not found. Install with: pip install MetaTrader5")


logger = logging.getLogger(__name__)


class MT5Client(BrokerClient):
    """MetaTrader 5 broker client for executing orders and account management.
    
    Connects to a running MT5 terminal and sends orders directly to the MT5 platform.
    Supports both demo and live accounts.
    """

    def __init__(self, mt5_path: Optional[str] = None, account: Optional[str] = None, password: Optional[str] = None):
        """Initialize MT5 client.
        
        Args:
            mt5_path: Optional path to MT5 terminal executable (e.g., 'C:\\Program Files\\MetaTrader 5\\terminal.exe')
            account: Optional account number/login to connect to
            password: Optional password for the account
        """
        if not MT5_AVAILABLE:
            raise RuntimeError(
                "MetaTrader5 package not found. Install with: pip install MetaTrader5"
            )
        
        self.mt5_path = mt5_path
        self.account = account
        self.password = password
        self._initialized = False
        self._connect()

    def _connect(self):
        """Initialize and connect to MT5 terminal."""
        try:
            # Initialize MT5 connection
            if self.mt5_path:
                if not mt5.initialize(path=self.mt5_path):
                    logger.error(f"Failed to initialize MT5 at path: {self.mt5_path}")
                    return
            else:
                if not mt5.initialize():
                    logger.error("Failed to initialize MT5. Ensure MT5 terminal is running.")
                    return

            logger.info("MT5 initialized successfully")

            # Connect to account if credentials provided
            if self.account and self.password:
                if not mt5.login(self.account, password=self.password):
                    logger.error(f"Failed to login to MT5 account {self.account}")
                    return
                logger.info(f"Connected to MT5 account {self.account}")

            self._initialized = True
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            self._initialized = False

    def _ensure_connected(self) -> bool:
        """Ensure MT5 is connected and ready."""
        if not self._initialized:
            self._connect()
        return self._initialized

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
            raise RuntimeError("MT5 not connected")

        try:
            # Normalize symbol for MT5 (add suffix if needed, e.g., EURUSD -> EURUSD)
            mt5_symbol = symbol.upper()

            # Get current price
            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {mt5_symbol}")
                return {
                    "broker": "mt5",
                    "order_id": None,
                    "status": "error",
                    "error": f"Symbol {mt5_symbol} not found",
                }

            # Determine order direction
            if side.lower() == "buy":
                order_direction = mt5.ORDER_BUY
                order_price = tick.ask
            elif side.lower() == "sell":
                order_direction = mt5.ORDER_SELL
                order_price = tick.bid
            else:
                raise ValueError(f"Invalid side: {side}")

            # Use provided price or market price
            if order_type.lower() == "limit" and price:
                order_price = price

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": mt5_symbol,
                "volume": qty,
                "type": order_direction,
                "price": order_price,
                "deviation": 20,  # Deviation in pips
                "magic": 12345,  # Magic number for tracking orders
                "comment": "jrd-alphamind order",
                "type_time": mt5.ORDER_TIME_GTC,  # Good-till-canceled
                "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
            }

            # Send order
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode {result.retcode}: {result.comment}")
                return {
                    "broker": "mt5",
                    "order_id": None,
                    "status": "failed",
                    "error": result.comment,
                    "retcode": result.retcode,
                }

            logger.info(f"Order placed successfully: {result.order}")

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
        """Get account balance and account info from MT5.
        
        Returns:
            Dict with balance, equity, margin info
        """
        if not self._ensure_connected():
            raise RuntimeError("MT5 not connected")

        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return {}

            return {
                "broker": "mt5",
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin_used": account_info.margin,
                "margin_free": account_info.margin_free,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "account_number": account_info.login,
            }

        except Exception as e:
            logger.error(f"Error getting balance from MT5: {e}")
            return {"error": str(e)}

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions from MT5.
        
        Returns:
            List of open positions with symbol, side, volume, price, profit/loss
        """
        if not self._ensure_connected():
            raise RuntimeError("MT5 not connected")

        try:
            positions = mt5.positions_get()
            if positions is None or len(positions) == 0:
                logger.info("No open positions")
                return []

            result = []
            for pos in positions:
                result.append({
                    "symbol": pos.symbol,
                    "side": "buy" if pos.type == mt5.ORDER_BUY else "sell",
                    "volume": pos.volume,
                    "price": pos.price_open,
                    "profit_loss": pos.profit,
                    "open_time": datetime.fromtimestamp(pos.time, tz=timezone.utc).isoformat(),
                })

            return result

        except Exception as e:
            logger.error(f"Error getting positions from MT5: {e}")
            return []

    def close(self):
        """Close MT5 connection."""
        if MT5_AVAILABLE:
            mt5.shutdown()
            logger.info("MT5 connection closed")
