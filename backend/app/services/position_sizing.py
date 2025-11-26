"""
Position Sizing Service

Calculates optimal lot sizes based on:
- Account balance
- Leverage
- Risk percentage per trade
- Stop-loss distance
- Pair contract specifications
- Currency conversion rates
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskStrategy(Enum):
    """Risk management strategies for position sizing."""
    FIXED_LOT = "fixed_lot"              # Fixed lot size (0.1, 0.5, 1.0, etc.)
    FIXED_RISK = "fixed_risk"            # Risk fixed % per trade (2% rule)
    KELLY_CRITERION = "kelly"             # Kelly formula
    VOLATILITY_BASED = "volatility"       # Scale based on ATR/volatility


class PositionSizer:
    """Calculate optimal position sizes for forex/crypto trading."""

    # Standard forex lot sizes (in base currency units)
    STANDARD_LOT = 100_000      # 1 standard lot
    MINI_LOT = 10_000           # 0.1 standard lot
    MICRO_LOT = 1_000           # 0.01 standard lot
    NANO_LOT = 100              # 0.001 standard lot

    # Contract specifications for common pairs
    CONTRACT_SPECS = {
        # Forex pairs (1 lot = 100k base currency)
        "EURUSD": {"lot_size": STANDARD_LOT, "pip_value": 10, "decimal": 4},
        "GBPUSD": {"lot_size": STANDARD_LOT, "pip_value": 10, "decimal": 4},
        "USDJPY": {"lot_size": STANDARD_LOT, "pip_value": 1000, "decimal": 2},
        "AUDUSD": {"lot_size": STANDARD_LOT, "pip_value": 10, "decimal": 4},
        "NZDUSD": {"lot_size": STANDARD_LOT, "pip_value": 10, "decimal": 4},
        "USDCAD": {"lot_size": STANDARD_LOT, "pip_value": 10, "decimal": 4},
        "USDCHF": {"lot_size": STANDARD_LOT, "pip_value": 10, "decimal": 4},

        # CFD indices (1 lot varies by broker)
        "SPX500": {"lot_size": 1, "pip_value": 1, "decimal": 1},
        "DAX40": {"lot_size": 1, "pip_value": 0.1, "decimal": 1},
        "FTSE100": {"lot_size": 1, "pip_value": 1, "decimal": 1},

        # Commodities
        "XAUUSD": {"lot_size": 1, "pip_value": 1, "decimal": 2},  # Gold
        "XAGUSD": {"lot_size": 1, "pip_value": 0.01, "decimal": 3},  # Silver
    }

    def __init__(
        self,
        account_balance: float,
        leverage: int = 1,
        risk_strategy: RiskStrategy = RiskStrategy.FIXED_RISK,
        risk_percent: float = 2.0,  # Default 2% risk per trade
        fixed_lot_size: float = 0.1,
        min_lot_size: float = 0.01,
        max_lot_size: float = 10.0,
    ):
        """
        Initialize position sizer.

        Args:
            account_balance: Account balance in USD
            leverage: Account leverage (1x, 10x, 50x, 100x, etc.)
            risk_strategy: Which strategy to use (fixed_risk, kelly, etc.)
            risk_percent: % of account to risk per trade (for FIXED_RISK)
            fixed_lot_size: Fixed lot size to use (for FIXED_LOT strategy)
            min_lot_size: Minimum lot size (cannot go below)
            max_lot_size: Maximum lot size (hard cap)
        """
        self.account_balance = account_balance
        self.leverage = leverage
        self.risk_strategy = risk_strategy
        self.risk_percent = risk_percent
        self.fixed_lot_size = fixed_lot_size
        self.min_lot_size = min_lot_size
        self.max_lot_size = max_lot_size

        # Calculate effective trading capital with leverage
        self.trading_capital = account_balance * leverage

    def calculate_lot_size(
        self,
        symbol: str,
        stop_loss_pips: float,
        current_price: float = 1.0,
        atr: Optional[float] = None,
        win_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate recommended lot size for a trade.

        Args:
            symbol: Trading pair (e.g., "EURUSD")
            stop_loss_pips: Distance in pips to stop-loss level
            current_price: Current price (for calculations)
            atr: Average True Range (for volatility-based sizing)
            win_rate: Win rate % (for Kelly criterion)

        Returns:
            Dict with lot_size, risk_amount, max_loss, reward_if_hit, etc.
        """
        if stop_loss_pips <= 0:
            raise ValueError("Stop-loss must be > 0 pips")

        # Get contract specs for symbol
        specs = self.CONTRACT_SPECS.get(symbol)
        if not specs:
            logger.warning(f"Unknown symbol {symbol}, using default specs")
            specs = {
                "lot_size": self.STANDARD_LOT,
                "pip_value": 10,
                "decimal": 4,
            }

        # Calculate lot size based on strategy
        if self.risk_strategy == RiskStrategy.FIXED_LOT:
            lot_size = self.fixed_lot_size

        elif self.risk_strategy == RiskStrategy.FIXED_RISK:
            lot_size = self._calculate_fixed_risk_lot(
                stop_loss_pips, specs
            )

        elif self.risk_strategy == RiskStrategy.KELLY_CRITERION:
            if win_rate is None:
                raise ValueError("win_rate required for Kelly criterion")
            lot_size = self._calculate_kelly_lot(
                stop_loss_pips, specs, win_rate
            )

        elif self.risk_strategy == RiskStrategy.VOLATILITY_BASED:
            if atr is None:
                raise ValueError("ATR required for volatility-based sizing")
            lot_size = self._calculate_volatility_lot(
                atr, specs, stop_loss_pips
            )

        else:
            lot_size = self.fixed_lot_size

        # Apply min/max constraints
        lot_size = max(self.min_lot_size, min(lot_size, self.max_lot_size))

        # Calculate risk metrics
        position_value = lot_size * specs["lot_size"] * current_price
        pips_value = lot_size * specs["pip_value"]
        max_loss = pips_value * stop_loss_pips
        risk_percent_actual = (max_loss / self.account_balance) * 100

        return {
            "symbol": symbol,
            "lot_size": round(lot_size, 3),
            "position_value_usd": round(position_value, 2),
            "risk_amount_usd": round(max_loss, 2),
            "risk_percent_of_account": round(risk_percent_actual, 2),
            "stop_loss_pips": stop_loss_pips,
            "stop_loss_usd": round(max_loss, 2),
            "strategy_used": self.risk_strategy.value,
            "account_balance": self.account_balance,
            "leverage": self.leverage,
            "trading_capital": self.trading_capital,
        }

    def _calculate_fixed_risk_lot(
        self, stop_loss_pips: float, specs: Dict[str, Any]
    ) -> float:
        """
        Fixed Risk strategy: Risk a fixed % of account per trade.

        Formula: Lot Size = (Account × Risk%) / (Stop-Loss Pips × Pip Value)

        Example:
            Account: $10,000
            Risk: 2%
            Stop-Loss: 50 pips
            Pip Value (EURUSD): $10 per 0.0001

            Lot Size = (10,000 × 0.02) / (50 × 10) = $200 / $500 = 0.4 lots
        """
        risk_amount = self.account_balance * (self.risk_percent / 100)
        pip_value = specs["pip_value"]
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        return lot_size

    def _calculate_kelly_lot(
        self,
        stop_loss_pips: float,
        specs: Dict[str, Any],
        win_rate: float,
    ) -> float:
        """
        Kelly Criterion: Maximize long-term growth based on win rate.

        Formula: f* = (win_rate × avg_win - loss_rate × avg_loss) / avg_loss

        Simplified for forex:
            f* = (2 × win_rate - 1) / (stop_loss_pips / take_profit_pips)

        Note: Kelly can be aggressive; many traders use Kelly/2 for safety.
        """
        if not (0 < win_rate < 1):
            raise ValueError("win_rate must be between 0 and 1 (as decimal)")

        loss_rate = 1 - win_rate

        # Assume take-profit = stop-loss (1:1 ratio)
        # Adjust if your strategy has different R:R
        avg_win_pips = stop_loss_pips
        avg_loss_pips = stop_loss_pips

        if avg_loss_pips == 0:
            raise ValueError("avg_loss_pips cannot be 0")

        # Kelly fraction (can be > 1, which means aggressive)
        kelly_fraction = (
            win_rate * avg_win_pips - loss_rate * avg_loss_pips
        ) / avg_loss_pips

        # Use conservative Kelly/2 to reduce volatility
        kelly_fraction = kelly_fraction / 2

        if kelly_fraction <= 0:
            return 0.01  # Minimum

        # Convert Kelly fraction to lot size
        risk_amount = self.account_balance * kelly_fraction
        pip_value = specs["pip_value"]
        lot_size = risk_amount / (stop_loss_pips * pip_value)

        return lot_size

    def _calculate_volatility_lot(
        self,
        atr: float,
        specs: Dict[str, Any],
        stop_loss_pips: float,
    ) -> float:
        """
        Volatility-based sizing: Inverse relationship with volatility.

        High volatility → smaller lot (more risk per pip)
        Low volatility → larger lot (less risk per pip)

        Adjusts position size based on current market conditions.
        """
        # Normalize volatility to a multiplier (0.5 to 2.0)
        # Assuming ATR is in pips
        base_atr = 50  # Reference volatility (50 pips)
        volatility_multiplier = base_atr / max(atr, 1.0)

        # Clamp multiplier to reasonable range
        volatility_multiplier = max(0.5, min(volatility_multiplier, 2.0))

        # Start with fixed risk calculation
        base_lot = self._calculate_fixed_risk_lot(stop_loss_pips, specs)

        # Apply volatility adjustment
        adjusted_lot = base_lot * volatility_multiplier

        return adjusted_lot

    def calculate_lot_for_risk_amount(
        self,
        symbol: str,
        risk_amount_usd: float,
        stop_loss_pips: float,
    ) -> Dict[str, Any]:
        """
        Reverse calculation: Given a risk amount, what lot size?

        Useful when you want to risk a specific USD amount per trade.

        Example:
            Risk: $50 per trade
            Stop-Loss: 50 pips
            Pip Value (EURUSD): $10

            Lot Size = $50 / (50 × $10) = 0.1 lots
        """
        specs = self.CONTRACT_SPECS.get(symbol, {
            "lot_size": self.STANDARD_LOT,
            "pip_value": 10,
            "decimal": 4,
        })

        pip_value = specs["pip_value"]
        lot_size = risk_amount_usd / (stop_loss_pips * pip_value)

        # Apply constraints
        lot_size = max(self.min_lot_size, min(lot_size, self.max_lot_size))

        risk_percent_actual = (risk_amount_usd / self.account_balance) * 100

        return {
            "symbol": symbol,
            "lot_size": round(lot_size, 3),
            "target_risk_usd": risk_amount_usd,
            "actual_risk_usd": round(lot_size * pip_value * stop_loss_pips, 2),
            "risk_percent_of_account": round(risk_percent_actual, 2),
            "stop_loss_pips": stop_loss_pips,
        }

    def calculate_multiple_entries(
        self,
        symbol: str,
        stop_loss_pips: float,
        num_entries: int = 3,
    ) -> Dict[str, Any]:
        """
        Scale-in strategy: Split position into multiple entries.

        Example: 3 entries of 0.1 lots each = 0.3 lots total
        """
        base_lot = self.calculate_lot_size(symbol, stop_loss_pips)
        total_lot = base_lot["lot_size"]
        entry_lot = total_lot / num_entries

        return {
            "total_lot_size": round(total_lot, 3),
            "entry_lot_size": round(entry_lot, 3),
            "num_entries": num_entries,
            "entries": [
                {
                    "entry": i + 1,
                    "lot_size": round(entry_lot, 3),
                    "cumulative_lot": round(entry_lot * (i + 1), 3),
                }
                for i in range(num_entries)
            ],
            "base_calculation": base_lot,
        }


def calculate_position_size_simple(
    account_balance: float,
    risk_percent: float = 2.0,
    stop_loss_pips: float = 50,
    current_price: float = 1.0,
    symbol: str = "EURUSD",
) -> float:
    """
    Quick calculation for common use case: Fixed 2% risk per trade.

    Args:
        account_balance: Account balance in USD
        risk_percent: % of account to risk (default 2%)
        stop_loss_pips: Distance to stop-loss in pips
        current_price: Current pair price (default 1.0)
        symbol: Trading pair (default EURUSD)

    Returns:
        Recommended lot size (float)

    Example:
        >>> calculate_position_size_simple(
        ...     account_balance=10000,
        ...     risk_percent=2,
        ...     stop_loss_pips=50
        ... )
        0.4  # Recommended lot size
    """
    sizer = PositionSizer(
        account_balance=account_balance,
        leverage=1,
        risk_strategy=RiskStrategy.FIXED_RISK,
        risk_percent=risk_percent,
    )
    result = sizer.calculate_lot_size(symbol, stop_loss_pips, current_price)
    return result["lot_size"]
