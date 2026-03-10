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
from .Pytrader_API_V4_01 import Pytrader_API

logger = logging.getLogger(__name__)


class PyTraderClient(BrokerClient):
    """PyTrader client for MT4/MT5 connectivity via TCP socket to EA.
    
    Connects to a running MT4/MT5 terminal with PyTrader EA installed.
    Supports all market symbols through configurable instrument lookup.
    """

    def __init__(self, host: str = "localhost", port: int = 1122, instrument_lookup: Optional[Dict[str, str]] = None):
        """Initialize PyTrader client.
        
        Args:
            host: MT4/MT5 terminal host (default: localhost)
            port: PyTrader EA port (default: 1122)
            instrument_lookup: Dict mapping universal symbols to broker-specific names
        """
        self.host = host
        self.port = port
        self.instrument_lookup = instrument_lookup or self._get_default_instrument_lookup()
        self.mt = Pytrader_API()
        self._connected = False
        self._connect()

    def _get_default_instrument_lookup(self) -> Dict[str, str]:
        """Get default instrument lookup mapping for major symbols.
        
        Returns:
            Dict mapping universal symbols to broker-specific names
        """
        return {
            # Forex Majors
            'EURUSD': 'EURUSD',
            'GBPUSD': 'GBPUSD', 
            'USDJPY': 'USDJPY',
            'USDCHF': 'USDCHF',
            'AUDUSD': 'AUDUSD',
            'USDCAD': 'USDCAD',
            'NZDUSD': 'NZDUSD',
            
            # Forex Crosses
            'EURGBP': 'EURGBP',
            'EURJPY': 'EURJPY',
            'GBPJPY': 'GBPJPY',
            'AUDJPY': 'AUDJPY',
            'CADJPY': 'CADJPY',
            'CHFJPY': 'CHFJPY',
            'NZDJPY': 'NZDJPY',
            'GBPAUD': 'GBPAUD',
            'GBPCAD': 'GBPCAD',
            'GBPCHF': 'GBPCHF',
            'GBPNZD': 'GBPNZD',
            'EURAUD': 'EURAUD',
            'EURCAD': 'EURCAD',
            'EURCHF': 'EURCHF',
            'EURNZD': 'EURNZD',
            'AUDCAD': 'AUDCAD',
            'AUDCHF': 'AUDCHF',
            'AUDNZD': 'AUDNZD',
            'CADCHF': 'CADCHF',
            'NZDCAD': 'NZDCAD',
            'NZDCHF': 'NZDCHF',
            
            # Commodities
            'XAUUSD': 'XAUUSD',  # Gold
            'XAGUSD': 'XAGUSD',  # Silver
            'XAUEUR': 'XAUEUR',  # Gold vs EUR
            'XAGEUR': 'XAGEUR',  # Silver vs EUR
            'XAUAUD': 'XAUAUD',  # Gold vs AUD
            'XAUGBP': 'XAUGBP',  # Gold vs GBP
            'XPDUSD': 'XPDUSD',  # Palladium
            'XPTUSD': 'XPTUSD',  # Platinum
            
            # Oil & Energy
            'WTI': 'WTI',        # WTI Crude Oil
            'BRENT': 'BRENT',    # Brent Crude Oil
            'NATURALGAS': 'NATURALGAS',
            
            # Indices
            'SPX500': 'SPX500',  # S&P 500
            'NAS100': 'NAS100',  # NASDAQ 100
            'US30': 'US30',      # Dow Jones
            'GER30': 'GER30',    # DAX
            'UK100': 'UK100',    # FTSE 100
            'FRA40': 'FRA40',    # CAC 40
            'ESP35': 'ESP35',    # IBEX 35
            'ITA40': 'ITA40',    # FTSE MIB
            'JPN225': 'JPN225',  # Nikkei 225
            'AUS200': 'AUS200',  # ASX 200
            'CHN50': 'CHN50',    # China A50
            'HKG33': 'HKG33',    # Hang Seng
            'NLD25': 'NLD25',    # AEX
            'SUI20': 'SUI20',    # SMI
            'BEL20': 'BEL20',    # BEL 20
            'POR20': 'POR20',    # PSI 20
            'AUT20': 'AUT20',    # ATX
            
            # Crypto (if supported)
            'BTCUSD': 'BTCUSD',
            'ETHUSD': 'ETHUSD',
            'LTCUSD': 'LTCUSD',
            'BCHUSD': 'BCHUSD',
            
            # Bonds
            'US10Y': 'US10Y',    # US 10 Year Treasury
            'DE10Y': 'DE10Y',    # German 10 Year Bund
            'UK10Y': 'UK10Y',    # UK 10 Year Gilt
            'JP10Y': 'JP10Y',    # Japan 10 Year JGB
        }

    def _connect(self):
        """Initialize and connect to PyTrader EA."""
        try:
            # Connect to PyTrader EA via TCP
            connected = self.mt.Connect(
                server=self.host,
                port=self.port,
                instrument_lookup=self.instrument_lookup,
                authorization_code='None'
            )
            self._connected = connected
            if connected:
                logger.info(f"Connected to PyTrader EA at {self.host}:{self.port}")
            else:
                logger.error(f"Failed to connect to PyTrader EA: {self.mt.command_return_error}")
        except Exception as e:
            logger.error(f"Error connecting to PyTrader EA: {e}")
            self._connected = False

    def _ensure_connected(self) -> bool:
        """Ensure PyTrader is connected and ready."""
        if not self._connected:
            self._connect()
        return self._connected

    def _get_universal_symbol(self, broker_symbol: str) -> str:
        """Convert broker-specific symbol back to universal symbol.
        
        Args:
            broker_symbol: Symbol as returned by broker
            
        Returns:
            Universal symbol format
        """
        # Create reverse lookup
        reverse_lookup = {v: k for k, v in self.instrument_lookup.items()}
        return reverse_lookup.get(broker_symbol.upper(), broker_symbol.upper())

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Place an order on PyTrader.
        
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
            # Map universal symbol to broker-specific symbol
            broker_symbol = self.instrument_lookup.get(symbol.upper(), symbol.upper())
            
            # Determine order type
            if order_type.lower() == "market":
                ordertype = "buy" if side.lower() == "buy" else "sell"
                openprice = 0.0  # Market order
            elif order_type.lower() == "limit":
                if side.lower() == "buy":
                    ordertype = "buy_limit"
                else:
                    ordertype = "sell_limit"
                openprice = price or 0.0
            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            # Place order using PyTrader API
            ticket = self.mt.Open_order(
                instrument=broker_symbol,
                ordertype=ordertype,
                volume=qty,
                openprice=openprice,
                slippage=10,
                magicnumber=12345,
                stoploss=0.0,
                takeprofit=0.0,
                comment="AI Trading Bot",
                market=(order_type.lower() == "market")
            )

            if ticket and ticket > 0:
                logger.info(f"Order placed successfully: {ticket}")
                return {
                    "broker": "pytrader",
                    "order_id": ticket,
                    "status": "filled",
                    "price": openprice if openprice > 0 else None,
                    "volume": qty,
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                error_msg = getattr(self.mt, 'command_return_error', 'Unknown error')
                logger.error(f"Order placement failed: {error_msg}")
                return {
                    "broker": "pytrader",
                    "order_id": None,
                    "status": "failed",
                    "error": error_msg,
                    "symbol": symbol,
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
            account_info = self.mt.Get_account_info()
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
            positions = self.mt.Get_positions()
            if positions:
                result = []
                for pos in positions:
                    # Map broker symbol back to universal symbol
                    universal_symbol = self._get_universal_symbol(pos.get("symbol", ""))
                    
                    result.append({
                        "broker": "pytrader",
                        "symbol": universal_symbol,
                        "broker_symbol": pos.get("symbol"),
                        "side": "buy" if pos.get("type") == 0 else "sell",  # Assuming 0=buy, 1=sell
                        "volume": pos.get("volume"),
                        "price": pos.get("price_open"),
                        "current_price": pos.get("current_price", 0),
                        "profit_loss": pos.get("profit"),
                        "open_time": pos.get("time"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
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
            # Map universal symbol to broker-specific symbol
            broker_symbol = self.instrument_lookup.get(symbol.upper(), symbol.upper())
            
            data = self.mt.Get_last_x_bars_from_now(broker_symbol, timeframe, bars)
            if data:
                # Add universal symbol to each bar
                for bar in data:
                    bar['universal_symbol'] = symbol
                return data
            else:
                logger.error(f"Failed to get historical data for {symbol} ({broker_symbol})")
                return []

        except Exception as e:
            logger.error(f"Error getting historical data from PyTrader: {e}")
            return []

    def close(self):
        """Close PyTrader connection."""
        if self.mt:
            self.mt.Disconnect()
            logger.info("PyTrader connection closed")
