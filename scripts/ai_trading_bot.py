#!/usr/bin/env python3
"""
AI Trading Bot with Successful Indicators

This bot uses proven technical indicators and ML predictions to trade forex.
Combines RSI, MACD, Bollinger Bands, Moving Averages, and AI decision fusion.

Usage:
    python ai_trading_bot.py --symbol EURUSD --mode live
"""

import asyncio
import logging
import argparse
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

# Import from your trading platform
from app.services.brain.brain import Brain
from app.services.brokers.mt5_client import PyTraderClient
from app.services.ml.ml_service import MLTradingService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AITradingBot:
    """AI-powered trading bot using successful indicators and ML."""

    def __init__(self, symbol: str = "EURUSD", mode: str = "demo"):
        self.symbol = symbol
        self.mode = mode
        self.brain = Brain()
        self.broker = PyTraderClient()
        self.ml_service = MLTradingService()
        self.position = None
        self.last_trade_time = None

        # Trading parameters
        self.min_trade_interval = 300  # 5 minutes between trades
        self.max_risk_per_trade = 0.02  # 2% risk per trade
        self.stop_loss_pips = 50
        self.take_profit_pips = 100

    async def initialize(self):
        """Initialize connections and services."""
        logger.info("🤖 Initializing AI Trading Bot...")

        # Initialize broker connection
        await self.broker._connect()
        logger.info("✅ Broker connected")

        # Load ML models
        await self.ml_service.load_models()
        logger.info("✅ ML models loaded")

    async def get_market_data(self, bars: int = 100) -> pd.DataFrame:
        """Get recent market data for analysis."""
        try:
            data = await self.broker.get_historical_data(self.symbol, "M1", bars)
            if data:
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['time'], unit='s')
                df = df.set_index('timestamp')
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate successful technical indicators."""
        if df.empty:
            return df

        # Moving Averages
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['ema_20'] = df['close'].ewm(span=20).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_middle'] = sma_20
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Momentum
        df['momentum'] = df['close'] / df['close'].shift(10) - 1

        # Volatility (ATR)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = tr.rolling(14).mean()

        return df.dropna()

    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate trading signal using successful indicators."""
        if df.empty:
            return "HOLD"

        latest = df.iloc[-1]

        # Trend signals (Moving Averages)
        trend_up = latest['ema_20'] > latest['sma_50']
        trend_down = latest['ema_20'] < latest['sma_50']

        # Momentum signals
        rsi_oversold = latest['rsi'] < 30
        rsi_overbought = latest['rsi'] > 70

        # MACD signals
        macd_bullish = latest['macd'] > latest['macd_signal']
        macd_bearish = latest['macd'] < latest['macd_signal']

        # Bollinger Band signals
        bb_oversold = latest['bb_position'] < 0.2
        bb_overbought = latest['bb_position'] > 0.8

        # Combine signals
        bullish_signals = sum([trend_up, rsi_oversold, macd_bullish, bb_oversold])
        bearish_signals = sum([trend_down, rsi_overbought, macd_bearish, bb_overbought])

        if bullish_signals >= 2:
            return "BUY"
        elif bearish_signals >= 2:
            return "SELL"
        else:
            return "HOLD"

    async def execute_trade(self, signal: str, confidence: float):
        """Execute trade based on signal."""
        if signal == "HOLD" or confidence < 0.6:
            return

        # Check if we can trade (time interval, existing position)
        now = datetime.now()
        if self.last_trade_time and (now - self.last_trade_time).seconds < self.min_trade_interval:
            return

        # Get account balance for position sizing
        balance_info = await self.broker.get_balance()
        if not balance_info:
            return

        balance = balance_info.get('balance', 1000)
        risk_amount = balance * self.max_risk_per_trade

        # Calculate position size based on stop loss
        # Assuming pip value calculation (simplified)
        pip_value = 0.0001  # For EURUSD
        stop_loss_amount = self.stop_loss_pips * pip_value
        volume = risk_amount / (stop_loss_amount * 100000)  # Standard lot calculation

        # Round to valid lot sizes
        volume = max(0.01, min(1.0, round(volume, 2)))

        logger.info(f"🎯 Executing {signal} trade: {volume} lots, confidence: {confidence:.2f}")

        try:
            order_result = await self.broker.place_order(
                symbol=self.symbol,
                side=signal.lower(),
                qty=volume,
                order_type="market"
            )

            if order_result and order_result.get('status') == 'filled':
                self.position = {
                    'side': signal,
                    'volume': volume,
                    'entry_price': order_result.get('price'),
                    'timestamp': now
                }
                self.last_trade_time = now
                logger.info(f"✅ Trade executed: {order_result}")
            else:
                logger.error(f"❌ Trade failed: {order_result}")

        except Exception as e:
            logger.error(f"Error executing trade: {e}")

    async def run_trading_loop(self):
        """Main trading loop."""
        logger.info(f"🚀 Starting trading loop for {self.symbol} in {self.mode} mode")

        while True:
            try:
                # Get market data
                df = await self.get_market_data(200)
                if df.empty:
                    logger.warning("No market data available")
                    await asyncio.sleep(60)
                    continue

                # Calculate indicators
                df = self.calculate_indicators(df)

                # Get AI/ML prediction
                market_snapshot = {
                    'symbol': self.symbol,
                    'current_price': df['close'].iloc[-1],
                    'indicators': [
                        {'name': 'rsi', 'value': df['rsi'].iloc[-1]},
                        {'name': 'macd', 'value': df['macd'].iloc[-1]},
                        {'name': 'bb_position', 'value': df['bb_position'].iloc[-1]},
                        {'name': 'momentum', 'value': df['momentum'].iloc[-1]}
                    ]
                }

                # Get brain decision
                decision = await self.brain.decide(
                    symbol=self.symbol,
                    current_price=df['close'].iloc[-1],
                    indicators=market_snapshot['indicators']
                )

                signal = decision.get('decision', 'HOLD')
                confidence = decision.get('confidence', 0.0)

                logger.info(f"🧠 Brain decision: {signal} (confidence: {confidence:.2f})")

                # Execute trade if conditions met
                if self.mode == "live":
                    await self.execute_trade(signal, confidence)
                else:
                    logger.info(f"📊 Would execute {signal} trade (demo mode)")

                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)

    async def shutdown(self):
        """Clean shutdown."""
        logger.info("🛑 Shutting down trading bot...")
        self.broker.close()


async def main():
    parser = argparse.ArgumentParser(description='AI Trading Bot')
    parser.add_argument('--symbol', default='EURUSD', help='Trading symbol')
    parser.add_argument('--mode', choices=['demo', 'live'], default='demo', help='Trading mode')

    args = parser.parse_args()

    bot = AITradingBot(symbol=args.symbol, mode=args.mode)

    try:
        await bot.initialize()
        await bot.run_trading_loop()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())