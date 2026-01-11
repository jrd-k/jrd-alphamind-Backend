"""
ML Risk Management Layer

Implements comprehensive risk management:
- Position sizing based on volatility
- Stop loss and take profit levels
- Risk filters and constraints
- Portfolio-level risk controls
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MLRiskManager:
    """Risk management for ML trading signals."""

    def __init__(self,
                 max_position_size_pct: float = 0.01,  # 1% of portfolio
                 max_portfolio_risk_pct: float = 0.02,  # 2% max risk per trade
                 stop_loss_atr_multiplier: float = 1.5,
                 take_profit_atr_multiplier: float = 3.0,
                 max_concurrent_trades: int = 5,
                 max_daily_loss_pct: float = 0.05,  # 5% max daily loss
                 volatility_lookback: int = 20):
        """
        Initialize risk manager.

        Args:
            max_position_size_pct: Maximum position size as % of portfolio
            max_portfolio_risk_pct: Maximum risk per trade as % of portfolio
            stop_loss_atr_multiplier: ATR multiplier for stop loss
            take_profit_atr_multiplier: ATR multiplier for take profit
            max_concurrent_trades: Maximum concurrent open trades
            max_daily_loss_pct: Maximum daily loss before stopping
            volatility_lookback: Periods for volatility calculation
        """
        self.max_position_size_pct = max_position_size_pct
        self.max_portfolio_risk_pct = max_portfolio_risk_pct
        self.stop_loss_atr_multiplier = stop_loss_atr_multiplier
        self.take_profit_atr_multiplier = take_profit_atr_multiplier
        self.max_concurrent_trades = max_concurrent_trades
        self.max_daily_loss_pct = max_daily_loss_pct
        self.volatility_lookback = volatility_lookback

    def calculate_position_size(self,
                               signal_strength: float,
                               volatility: float,
                               portfolio_value: float,
                               current_exposure: float = 0.0) -> float:
        """
        Calculate position size based on signal strength and volatility.

        Args:
            signal_strength: ML model confidence (0-1)
            volatility: Current market volatility (ATR or similar)
            portfolio_value: Current portfolio value
            current_exposure: Current portfolio exposure

        Returns:
            Position size as percentage of portfolio
        """
        if signal_strength < 0.5:
            return 0.0  # No trade for weak signals

        # Base position size from Kelly criterion approximation
        # Simplified: position_size = signal_strength / volatility
        base_size = min(signal_strength / (volatility * 10), self.max_position_size_pct)

        # Adjust for current exposure
        available_exposure = max(0, 1.0 - current_exposure)
        position_size = min(base_size, available_exposure)

        # Risk-based adjustment
        risk_adjusted_size = min(position_size, self.max_portfolio_risk_pct / volatility)

        return max(0, risk_adjusted_size)

    def calculate_stop_levels(self,
                             entry_price: float,
                             atr: float,
                             direction: str) -> Dict[str, float]:
        """
        Calculate stop loss and take profit levels.

        Args:
            entry_price: Entry price
            atr: Average True Range
            direction: 'long' or 'short'

        Returns:
            Dictionary with stop_loss and take_profit prices
        """
        if direction == 'long':
            stop_loss = entry_price - (atr * self.stop_loss_atr_multiplier)
            take_profit = entry_price + (atr * self.take_profit_atr_multiplier)
        elif direction == 'short':
            stop_loss = entry_price + (atr * self.stop_loss_atr_multiplier)
            take_profit = entry_price - (atr * self.take_profit_atr_multiplier)
        else:
            raise ValueError("Direction must be 'long' or 'short'")

        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_per_share': abs(entry_price - stop_loss)
        }

    def apply_risk_filters(self,
                          df: pd.DataFrame,
                          predictions: np.ndarray,
                          current_positions: List[Dict[str, Any]] = None) -> np.ndarray:
        """
        Apply risk filters to predictions.

        Args:
            df: DataFrame with market data and features
            predictions: Raw ML predictions
            current_positions: List of current open positions

        Returns:
            Filtered predictions
        """
        filtered_predictions = predictions.copy()

        # Trend alignment filter
        filtered_predictions = self._filter_trend_alignment(df, filtered_predictions)

        # Volatility filter
        filtered_predictions = self._filter_volatility(df, filtered_predictions)

        # Probability threshold filter
        filtered_predictions = self._filter_probability_threshold(df, filtered_predictions)

        # Portfolio risk filter
        if current_positions:
            filtered_predictions = self._filter_portfolio_risk(df, filtered_predictions, current_positions)

        return filtered_predictions

    def _filter_trend_alignment(self, df: pd.DataFrame, predictions: np.ndarray) -> np.ndarray:
        """Filter trades that don't align with trend."""
        if 'trend_direction' not in df.columns:
            return predictions

        # Only allow long trades in uptrend, short trades in downtrend
        trend_aligned = (
            ((predictions == 1) & (df['trend_direction'] > 0)) |  # Long in uptrend
            ((predictions == 2) & (df['trend_direction'] < 0)) |  # Short in downtrend
            (predictions == 0)  # No trade
        )

        return np.where(trend_aligned, predictions, 0)

    def _filter_volatility(self, df: pd.DataFrame, predictions: np.ndarray) -> np.ndarray:
        """Filter trades in high volatility conditions."""
        if 'volatility_regime' not in df.columns:
            return predictions

        # Avoid trading in extreme volatility
        low_volatility = df['volatility_regime'] < 2  # Not extreme high volatility

        return np.where(low_volatility, predictions, 0)

    def _filter_probability_threshold(self, df: pd.DataFrame, predictions: np.ndarray) -> np.ndarray:
        """Filter trades below probability threshold."""
        if 'prediction_probability' not in df.columns:
            return predictions

        # Require minimum probability for trades
        high_confidence = df['prediction_probability'] > 0.6

        return np.where(high_confidence, predictions, 0)

    def _filter_portfolio_risk(self,
                              df: pd.DataFrame,
                              predictions: np.ndarray,
                              current_positions: List[Dict[str, Any]]) -> np.ndarray:
        """Filter based on portfolio-level risk constraints."""
        # Count current positions
        current_trade_count = len([p for p in current_positions if p.get('status') == 'open'])

        if current_trade_count >= self.max_concurrent_trades:
            # No new trades if at max capacity
            return np.zeros_like(predictions)

        # Calculate current portfolio exposure
        current_exposure = sum(p.get('exposure', 0) for p in current_positions)

        if current_exposure >= 0.8:  # 80% max exposure
            return np.zeros_like(predictions)

        return predictions

    def check_daily_loss_limit(self,
                              daily_pnl: float,
                              portfolio_value: float) -> bool:
        """
        Check if daily loss limit has been exceeded.

        Args:
            daily_pnl: Daily profit/loss
            portfolio_value: Current portfolio value

        Returns:
            True if trading should stop
        """
        daily_loss_pct = abs(daily_pnl) / portfolio_value if portfolio_value > 0 else 0
        return daily_loss_pct >= self.max_daily_loss_pct

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_volatility_regime(self, df: pd.DataFrame) -> pd.Series:
        """Calculate volatility regime (normalized ATR)."""
        atr = self.calculate_atr(df)
        atr_mean = atr.rolling(window=self.volatility_lookback).mean()
        atr_std = atr.rolling(window=self.volatility_lookback).std()

        # Z-score of current ATR
        volatility_regime = (atr - atr_mean) / atr_std

        return volatility_regime.abs()  # Absolute value for regime strength

    def get_risk_metrics(self,
                        trades: List[Dict[str, Any]],
                        portfolio_value: float) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        if not trades:
            return {}

        trades_df = pd.DataFrame(trades)

        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]

        metrics = {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / total_trades if total_trades > 0 else 0,
            'avg_win': winning_trades['pnl'].mean() if not winning_trades.empty else 0,
            'avg_loss': losing_trades['pnl'].mean() if not losing_trades.empty else 0,
            'largest_win': winning_trades['pnl'].max() if not winning_trades.empty else 0,
            'largest_loss': losing_trades['pnl'].min() if not losing_trades.empty else 0,
            'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if not losing_trades.empty and losing_trades['pnl'].sum() != 0 else float('inf'),
        }

        # Risk metrics
        returns = trades_df['pnl'] / portfolio_value
        cumulative_returns = (1 + returns).cumprod()

        metrics.update({
            'total_return': cumulative_returns.iloc[-1] - 1 if not cumulative_returns.empty else 0,
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'max_drawdown': self._calculate_max_drawdown(cumulative_returns),
            'sortino_ratio': self._calculate_sortino_ratio(returns),
            'calmar_ratio': self._calculate_calmar_ratio(returns),
        })

        return metrics

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        return np.sqrt(252) * (returns.mean() - risk_free_rate) / returns.std()

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        if len(cumulative_returns) == 0:
            return 0.0
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio (downside deviation only)."""
        if len(returns) == 0:
            return 0.0

        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf') if returns.mean() > 0 else 0.0

        return np.sqrt(252) * (returns.mean() - risk_free_rate) / downside_returns.std()

    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio."""
        if len(returns) == 0:
            return 0.0

        cumulative_returns = (1 + returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1
        max_dd = self._calculate_max_drawdown(cumulative_returns)

        if max_dd == 0:
            return float('inf') if total_return > 0 else 0.0

        return total_return / abs(max_dd)