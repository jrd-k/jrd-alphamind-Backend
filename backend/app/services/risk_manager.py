"""
Risk Management Service

Comprehensive risk controls for the trading system:
- Daily loss limits
- Account drawdown checks
- Position limits
- Correlation analysis (avoid correlated pairs)
- Exposure checks
- Risk of ruin calculations
- Margin requirements
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels."""
    SAFE = "safe"           # All checks pass
    WARNING = "warning"     # Some concern, proceed with caution
    CRITICAL = "critical"   # Should NOT trade


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    level: RiskLevel
    message: str
    details: Dict[str, Any]


class RiskManager:
    """Comprehensive risk management system."""

    # Pair correlations (historical approximations)
    PAIR_CORRELATIONS = {
        ("EURUSD", "GBPUSD"): 0.82,
        ("EURUSD", "AUDUSD"): 0.68,
        ("EURUSD", "NZDUSD"): 0.64,
        ("GBPUSD", "AUDUSD"): 0.65,
        ("GBPUSD", "NZDUSD"): 0.72,
        ("USDJPY", "EURUSD"): -0.73,  # Inverse correlation
        ("USDJPY", "GBPUSD"): -0.65,
        ("USDCHF", "EURUSD"): -0.80,  # Strong inverse
    }

    # Margin requirements by pair (% of position value)
    MARGIN_REQUIREMENTS = {
        "EURUSD": 2.0,      # 1:50 leverage
        "GBPUSD": 2.0,
        "USDJPY": 2.0,
        "AUDUSD": 2.0,
        "NZDUSD": 2.0,
        "USDCAD": 2.0,
        "USDCHF": 2.0,
        "XAUUSD": 5.0,      # Stricter on gold
        "SPX500": 10.0,     # CFDs require more margin
    }

    def __init__(
        self,
        account_balance: float,
        max_daily_loss_pct: float = 5.0,  # Stop trading if lost 5% today
        max_drawdown_pct: float = 15.0,   # Never risk more than 15% equity
        max_correlation_threshold: float = 0.7,  # Avoid correlated positions
        max_position_size_pct: float = 5.0,  # Single position max 5% of account
        max_margin_usage_pct: float = 80.0,  # Keep 20% margin buffer
    ):
        """
        Initialize risk manager.

        Args:
            account_balance: Current account balance in USD
            max_daily_loss_pct: Max daily loss before stopping
            max_drawdown_pct: Max account drawdown
            max_correlation_threshold: Threshold for correlated positions
            max_position_size_pct: Max single position size
            max_margin_usage_pct: Max margin usage allowed
        """
        self.account_balance = account_balance
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_correlation_threshold = max_correlation_threshold
        self.max_position_size_pct = max_position_size_pct
        self.max_margin_usage_pct = max_margin_usage_pct

        # Track daily trades for loss limit
        self.daily_realized_pnl = 0.0
        self.daily_trades = []

    def check_all_risks(
        self,
        symbol: str,
        qty: float,
        entry_price: float,
        stop_loss_price: float,
        current_positions: List[Dict[str, Any]],
        current_equity: Optional[float] = None,
        margin_available: Optional[float] = None,
    ) -> List[RiskCheckResult]:
        """
        Run all risk checks before executing a trade.

        Returns list of RiskCheckResult objects.
        """
        results = []

        # 1. Daily loss check
        results.append(self.check_daily_loss())

        # 2. Drawdown check
        results.append(
            self.check_drawdown(
                current_equity or self.account_balance,
                self.account_balance,
            )
        )

        # 3. Position size check
        results.append(self.check_position_size(qty, entry_price))

        # 4. Margin check
        if margin_available is not None:
            results.append(
                self.check_margin(
                    symbol, qty, entry_price, margin_available
                )
            )

        # 5. Correlation check
        if current_positions:
            results.append(
                self.check_correlation(symbol, current_positions)
            )

        # 6. Stop-loss validity check
        results.append(
            self.check_stop_loss(symbol, entry_price, stop_loss_price)
        )

        return results

    def check_daily_loss(self) -> RiskCheckResult:
        """Check if daily loss limit exceeded."""
        daily_loss_pct = (
            abs(self.daily_realized_pnl) / self.account_balance
        ) * 100

        if daily_loss_pct > self.max_daily_loss_pct:
            return RiskCheckResult(
                level=RiskLevel.CRITICAL,
                message=f"Daily loss limit exceeded: {daily_loss_pct:.2f}%",
                details={
                    "daily_pnl": self.daily_realized_pnl,
                    "daily_loss_pct": daily_loss_pct,
                    "max_allowed": self.max_daily_loss_pct,
                    "trades_today": len(self.daily_trades),
                },
            )

        if daily_loss_pct > self.max_daily_loss_pct * 0.7:
            return RiskCheckResult(
                level=RiskLevel.WARNING,
                message=f"Approaching daily loss limit: {daily_loss_pct:.2f}%",
                details={
                    "daily_pnl": self.daily_realized_pnl,
                    "daily_loss_pct": daily_loss_pct,
                    "max_allowed": self.max_daily_loss_pct,
                },
            )

        return RiskCheckResult(
            level=RiskLevel.SAFE,
            message="Daily loss within limits",
            details={
                "daily_pnl": self.daily_realized_pnl,
                "daily_loss_pct": daily_loss_pct,
            },
        )

    def check_drawdown(
        self, current_equity: float, account_start: float
    ) -> RiskCheckResult:
        """Check account drawdown percentage."""
        if current_equity <= 0 or account_start <= 0:
            return RiskCheckResult(
                level=RiskLevel.CRITICAL,
                message="Invalid account values",
                details={"current_equity": current_equity, "account_start": account_start},
            )

        drawdown_pct = ((account_start - current_equity) / account_start) * 100

        if drawdown_pct > self.max_drawdown_pct:
            return RiskCheckResult(
                level=RiskLevel.CRITICAL,
                message=f"Account drawdown exceeded: {drawdown_pct:.2f}%",
                details={
                    "current_equity": current_equity,
                    "starting_equity": account_start,
                    "drawdown_pct": drawdown_pct,
                    "max_allowed": self.max_drawdown_pct,
                },
            )

        if drawdown_pct > self.max_drawdown_pct * 0.7:
            return RiskCheckResult(
                level=RiskLevel.WARNING,
                message=f"Drawdown approaching limit: {drawdown_pct:.2f}%",
                details={
                    "drawdown_pct": drawdown_pct,
                    "max_allowed": self.max_drawdown_pct,
                },
            )

        return RiskCheckResult(
            level=RiskLevel.SAFE,
            message="Drawdown within limits",
            details={
                "drawdown_pct": drawdown_pct,
                "max_allowed": self.max_drawdown_pct,
            },
        )

    def check_position_size(
        self, qty: float, entry_price: float
    ) -> RiskCheckResult:
        """Check if position size is within limits."""
        position_value = qty * entry_price
        position_pct = (position_value / self.account_balance) * 100

        if position_pct > self.max_position_size_pct:
            return RiskCheckResult(
                level=RiskLevel.CRITICAL,
                message=f"Position too large: {position_pct:.2f}%",
                details={
                    "position_value": position_value,
                    "position_pct": position_pct,
                    "max_allowed": self.max_position_size_pct,
                },
            )

        return RiskCheckResult(
            level=RiskLevel.SAFE,
            message="Position size acceptable",
            details={
                "position_value": position_value,
                "position_pct": position_pct,
            },
        )

    def check_margin(
        self,
        symbol: str,
        qty: float,
        entry_price: float,
        margin_available: float,
    ) -> RiskCheckResult:
        """Check if sufficient margin available."""
        margin_req_pct = self.MARGIN_REQUIREMENTS.get(symbol, 2.0)
        position_value = qty * entry_price
        required_margin = position_value * (margin_req_pct / 100)

        if required_margin > margin_available:
            return RiskCheckResult(
                level=RiskLevel.CRITICAL,
                message=f"Insufficient margin: {required_margin:.2f} > {margin_available:.2f}",
                details={
                    "required_margin": required_margin,
                    "available_margin": margin_available,
                    "position_value": position_value,
                    "margin_req_pct": margin_req_pct,
                },
            )

        margin_usage_pct = (
            (required_margin / (required_margin + margin_available)) * 100
        )

        if margin_usage_pct > self.max_margin_usage_pct:
            return RiskCheckResult(
                level=RiskLevel.WARNING,
                message=f"High margin usage: {margin_usage_pct:.2f}%",
                details={
                    "margin_usage_pct": margin_usage_pct,
                    "max_allowed": self.max_margin_usage_pct,
                },
            )

        return RiskCheckResult(
            level=RiskLevel.SAFE,
            message="Margin available",
            details={
                "margin_usage_pct": margin_usage_pct,
                "available_margin": margin_available,
            },
        )

    def check_correlation(
        self, symbol: str, current_positions: List[Dict[str, Any]]
    ) -> RiskCheckResult:
        """Check if new position correlates too much with existing positions."""
        warnings = []

        for position in current_positions:
            existing_symbol = position.get("symbol", "").upper()
            pair = tuple(sorted([symbol.upper(), existing_symbol]))

            correlation = self.PAIR_CORRELATIONS.get(pair)
            if correlation is None:
                continue

            abs_correlation = abs(correlation)

            if abs_correlation > self.max_correlation_threshold:
                warnings.append(
                    f"{symbol} vs {existing_symbol}: {correlation:.2f} correlation"
                )

        if warnings:
            return RiskCheckResult(
                level=RiskLevel.WARNING,
                message=f"High correlation detected: {'; '.join(warnings)}",
                details={
                    "warnings": warnings,
                    "threshold": self.max_correlation_threshold,
                },
            )

        return RiskCheckResult(
            level=RiskLevel.SAFE,
            message="No problematic correlations",
            details={"existing_positions": len(current_positions)},
        )

    def check_stop_loss(
        self, symbol: str, entry_price: float, stop_loss_price: float
    ) -> RiskCheckResult:
        """Validate stop-loss is appropriately placed."""
        if stop_loss_price <= 0:
            return RiskCheckResult(
                level=RiskLevel.CRITICAL,
                message="Stop-loss price must be > 0",
                details={"entry_price": entry_price, "stop_loss_price": stop_loss_price},
            )

        pips_distance = abs(entry_price - stop_loss_price) * 10000  # Approx pips
        max_allowed_pips = entry_price * 0.02  # 2% max stop-loss

        if pips_distance > max_allowed_pips:
            return RiskCheckResult(
                level=RiskLevel.WARNING,
                message=f"Stop-loss very wide: ~{pips_distance:.0f} pips",
                details={
                    "entry_price": entry_price,
                    "stop_loss_price": stop_loss_price,
                    "pips_distance": pips_distance,
                },
            )

        if pips_distance < 5:
            return RiskCheckResult(
                level=RiskLevel.WARNING,
                message=f"Stop-loss too tight: ~{pips_distance:.1f} pips (unrealistic)",
                details={
                    "entry_price": entry_price,
                    "stop_loss_price": stop_loss_price,
                    "pips_distance": pips_distance,
                },
            )

        return RiskCheckResult(
            level=RiskLevel.SAFE,
            message="Stop-loss placement acceptable",
            details={"pips_distance": pips_distance},
        )

    def calculate_risk_of_ruin(
        self,
        win_rate: float,
        avg_win_pct: float,
        avg_loss_pct: float,
        trade_count: int = 100,
    ) -> Dict[str, Any]:
        """
        Calculate probability of account ruin (losing account to 0).

        Based on Kelly Criterion and ruin theory.

        Args:
            win_rate: Historical win rate (0-1)
            avg_win_pct: Average win size (% of account)
            avg_loss_pct: Average loss size (% of account)
            trade_count: Number of trades to project

        Returns:
            Dict with ruin probability and analysis
        """
        if not (0 < win_rate < 1):
            return {"error": "win_rate must be between 0 and 1"}

        loss_rate = 1 - win_rate

        # Kelly fraction
        kelly_fraction = (win_rate * avg_win_pct - loss_rate * avg_loss_pct) / avg_loss_pct

        if kelly_fraction <= 0:
            return {
                "kelly_fraction": kelly_fraction,
                "risk_of_ruin_pct": 100.0,
                "verdict": "System is losing; high risk of ruin",
            }

        # Simplified ruin probability (Gambler's Ruin formula)
        # P(ruin) ≈ ((1-kelly)/1+kelly)^trades
        ruin_probability = ((1 - kelly_fraction) / (1 + kelly_fraction)) ** trade_count

        ruin_pct = ruin_probability * 100

        verdict = "Safe" if ruin_pct < 5 else ("Moderate risk" if ruin_pct < 25 else "High risk")

        return {
            "win_rate": win_rate,
            "kelly_fraction": kelly_fraction,
            "kelly_conservative": kelly_fraction / 2,  # Half-Kelly
            "trades_projected": trade_count,
            "risk_of_ruin_pct": round(ruin_pct, 2),
            "verdict": verdict,
            "details": {
                "avg_win_pct": avg_win_pct,
                "avg_loss_pct": avg_loss_pct,
                "expected_return_per_trade": win_rate * avg_win_pct - loss_rate * avg_loss_pct,
            },
        }

    def record_trade_result(self, pnl: float, symbol: str = ""):
        """Record a trade result for daily P&L tracking."""
        self.daily_realized_pnl += pnl
        self.daily_trades.append({
            "timestamp": datetime.now(),
            "pnl": pnl,
            "symbol": symbol,
        })

    def reset_daily_stats(self):
        """Reset daily statistics (call at market open each day)."""
        self.daily_realized_pnl = 0.0
        self.daily_trades = []

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get current daily trading statistics."""
        daily_loss_pct = (
            abs(self.daily_realized_pnl) / self.account_balance * 100
            if self.account_balance > 0
            else 0
        )

        return {
            "date": datetime.now().date().isoformat(),
            "daily_pnl": round(self.daily_realized_pnl, 2),
            "daily_loss_pct": round(daily_loss_pct, 2),
            "max_daily_loss_allowed": self.max_daily_loss_pct,
            "trades_today": len(self.daily_trades),
            "largest_win": round(max([t["pnl"] for t in self.daily_trades], default=0), 2),
            "largest_loss": round(min([t["pnl"] for t in self.daily_trades], default=0), 2),
        }
