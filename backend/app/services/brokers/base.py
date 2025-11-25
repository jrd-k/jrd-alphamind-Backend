from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BrokerClient(ABC):
    """Abstract base class for all broker integrations.
    
    All broker clients must implement this interface to ensure consistent
    order placement, balance queries, and position retrieval across different brokers.
    """

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Dict[str, Any]:
        """Send an order to the broker and return broker response.
        
        Args:
            symbol: Trading pair (e.g., 'EURUSD')
            side: 'buy' or 'sell'
            qty: Quantity to trade
            price: Limit price (for limit orders)
            order_type: 'market' or 'limit'
            
        Returns:
            Dict with keys: order_id, status, price, volume, timestamp
        """
        raise NotImplementedError

    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """Return account balance and equity info.
        
        Returns:
            Dict with keys: balance, equity, margin_used, etc.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Return current open positions.
        
        Returns:
            List of dicts with keys: symbol, side, volume, price, profit_loss
        """
        raise NotImplementedError
