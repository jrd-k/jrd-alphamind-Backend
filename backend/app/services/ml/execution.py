"""
ML Execution Layer

Handles live inference and trade execution:
- Real-time signal generation
- Order execution with risk management
- Performance monitoring
- Separate from ML prediction logic
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class MLExecutionEngine:
    """Execution engine for ML trading signals."""

    def __init__(self,
                 brain_service,
                 risk_manager,
                 trade_orchestrator,
                 min_signal_interval: int = 5,  # minutes
                 max_daily_trades: int = 10,
                 confidence_threshold: float = 0.6):
        """
        Initialize execution engine.

        Args:
            brain_service: Brain service instance
            risk_manager: Risk manager instance
            trade_orchestrator: Trade orchestrator instance
            min_signal_interval: Minimum minutes between signals
            max_daily_trades: Maximum trades per day
            confidence_threshold: Minimum confidence for execution
        """
        self.brain_service = brain_service
        self.risk_manager = risk_manager
        self.trade_orchestrator = trade_orchestrator
        self.min_signal_interval = min_signal_interval
        self.max_daily_trades = max_daily_trades
        self.confidence_threshold = confidence_threshold

        # State tracking
        self.last_signal_time = None
        self.daily_trade_count = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.active_signals = []
        self.execution_history = []

    async def process_market_data(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming market data and generate trading signals.

        Args:
            market_data: Real-time market data

        Returns:
            Trading signal if conditions met, None otherwise
        """
        try:
            # Check daily limits
            if not self._check_daily_limits():
                return None

            # Check signal frequency
            if not self._check_signal_frequency():
                return None

            # Generate ML features
            features = await self._generate_features(market_data)
            if not features:
                return None

            # Get ML prediction
            signal = await self._generate_ml_signal(features, market_data)
            if not signal:
                return None

            # Apply risk filters
            if not self._apply_risk_filters(signal, market_data):
                return None

            # Execute trade
            execution_result = await self._execute_trade(signal, market_data)

            # Update state
            self._update_execution_state(signal, execution_result)

            return execution_result

        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            return None

    async def _generate_features(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate ML features from market data."""
        try:
            # This would integrate with the feature engineering module
            # For now, return basic features
            features = {
                'close': market_data.get('close'),
                'volume': market_data.get('volume'),
                'timestamp': market_data.get('timestamp'),
                'symbol': market_data.get('symbol')
            }

            # Add technical indicators if available
            if 'indicators' in market_data:
                features.update(market_data['indicators'])

            return features

        except Exception as e:
            logger.error(f"Error generating features: {e}")
            return None

    async def _generate_ml_signal(self,
                                 features: Dict[str, Any],
                                 market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate ML trading signal."""
        try:
            # Get Brain decision
            brain_decision = await self.brain_service.decide({
                'symbol': market_data.get('symbol'),
                'current_price': market_data.get('close'),
                'features': features,
                'indicators': market_data.get('indicators', {})
            })

            if not brain_decision or brain_decision.get('confidence', 0) < self.confidence_threshold:
                return None

            # Convert to execution signal
            signal = {
                'symbol': market_data.get('symbol'),
                'direction': brain_decision.get('action'),
                'confidence': brain_decision.get('confidence'),
                'prediction_probability': brain_decision.get('probability', 0),
                'features': features,
                'timestamp': datetime.now(),
                'market_data': market_data
            }

            return signal

        except Exception as e:
            logger.error(f"Error generating ML signal: {e}")
            return None

    def _apply_risk_filters(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
        """Apply risk management filters to signal."""
        try:
            # Check portfolio risk limits
            current_positions = self._get_current_positions()
            if len(current_positions) >= self.risk_manager.max_concurrent_trades:
                logger.info("Maximum concurrent trades reached")
                return False

            # Check daily loss limits
            if self._check_daily_loss_limit():
                logger.info("Daily loss limit reached")
                return False

            # Check signal strength
            if signal.get('confidence', 0) < self.confidence_threshold:
                logger.info(f"Signal confidence {signal['confidence']} below threshold {self.confidence_threshold}")
                return False

            # Additional risk checks would go here
            # (trend alignment, volatility filters, etc.)

            return True

        except Exception as e:
            logger.error(f"Error applying risk filters: {e}")
            return False

    async def _execute_trade(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the trading signal."""
        try:
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                signal_strength=signal.get('confidence', 0),
                volatility=market_data.get('atr', 0.01),  # Default ATR
                portfolio_value=self._get_portfolio_value(),
                current_exposure=self._get_current_exposure()
            )

            if position_size <= 0:
                return {'status': 'rejected', 'reason': 'position_size_zero'}

            # Prepare order data
            order_data = {
                'symbol': signal['symbol'],
                'direction': signal['direction'],
                'quantity': position_size,
                'current_price': market_data.get('close'),
                'indicators': signal.get('features', {}),
                'ml_signal': {
                    'confidence': signal.get('confidence'),
                    'features': signal.get('features'),
                    'timestamp': signal.get('timestamp')
                }
            }

            # Execute through orchestrator
            result = await self.trade_orchestrator.orchestrate_trade(order_data)

            execution_result = {
                'status': 'executed' if result.get('success') else 'failed',
                'signal': signal,
                'order_result': result,
                'execution_time': datetime.now(),
                'position_size': position_size
            }

            return execution_result

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {'status': 'error', 'error': str(e)}

    def _check_daily_limits(self) -> bool:
        """Check if daily trading limits have been reached."""
        now = datetime.now()

        # Reset daily count at midnight
        if now.date() > self.daily_reset_time.date():
            self.daily_trade_count = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

        return self.daily_trade_count < self.max_daily_trades

    def _check_signal_frequency(self) -> bool:
        """Check if minimum time has passed since last signal."""
        if self.last_signal_time is None:
            return True

        time_since_last = datetime.now() - self.last_signal_time
        min_interval = timedelta(minutes=self.min_signal_interval)

        return time_since_last >= min_interval

    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been exceeded."""
        # Calculate daily P&L
        today_trades = [trade for trade in self.execution_history
                       if trade.get('execution_time', datetime.min).date() == datetime.now().date()]

        daily_pnl = sum(trade.get('pnl', 0) for trade in today_trades)
        portfolio_value = self._get_portfolio_value()

        return not self.risk_manager.check_daily_loss_limit(daily_pnl, portfolio_value)

    def _get_current_positions(self) -> List[Dict[str, Any]]:
        """Get current open positions."""
        # This would integrate with position tracking
        return self.active_signals

    def _get_portfolio_value(self) -> float:
        """Get current portfolio value."""
        # This would integrate with portfolio tracking
        return 100000.0  # Default portfolio value

    def _get_current_exposure(self) -> float:
        """Get current portfolio exposure."""
        positions = self._get_current_positions()
        total_exposure = sum(pos.get('exposure', 0) for pos in positions)
        return total_exposure

    def _update_execution_state(self, signal: Dict[str, Any], execution_result: Dict[str, Any]):
        """Update execution state after trade."""
        self.last_signal_time = datetime.now()
        self.daily_trade_count += 1

        # Track active signals
        if execution_result.get('status') == 'executed':
            self.active_signals.append({
                'signal': signal,
                'execution': execution_result,
                'status': 'open'
            })

        # Add to history
        self.execution_history.append({
            'signal': signal,
            'execution': execution_result,
            'timestamp': datetime.now()
        })

        # Clean old history (keep last 1000 entries)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        try:
            recent_trades = [trade for trade in self.execution_history
                           if (datetime.now() - trade.get('timestamp', datetime.min)).days <= 7]

            stats = {
                'total_signals': len(self.execution_history),
                'recent_signals': len(recent_trades),
                'daily_trade_count': self.daily_trade_count,
                'active_positions': len(self.active_signals),
                'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
                'success_rate': self._calculate_success_rate(recent_trades)
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting execution stats: {e}")
            return {}

    def _calculate_success_rate(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate success rate of recent trades."""
        if not trades:
            return 0.0

        successful_trades = sum(1 for trade in trades
                              if trade.get('execution', {}).get('status') == 'executed')

        return successful_trades / len(trades)

    async def close_position(self, position_id: str, reason: str = 'manual') -> bool:
        """Close an open position."""
        try:
            # Find position
            position = None
            for pos in self.active_signals:
                if pos.get('id') == position_id:
                    position = pos
                    break

            if not position:
                return False

            # Close through orchestrator
            close_result = await self.trade_orchestrator.close_position(position)

            # Update state
            position['status'] = 'closed'
            position['close_reason'] = reason
            position['close_time'] = datetime.now()

            return close_result.get('success', False)

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False