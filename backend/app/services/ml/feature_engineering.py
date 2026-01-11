"""
ML Trading Feature Engineering Pipeline

Implements comprehensive feature engineering for ML-based trading:
- Price & Return Features
- Trend Indicators
- Momentum Indicators
- Volatility Measures
- Candle Structure Analysis
- Market Context (Sessions, Time)
- Multi-Timeframe Aggregates
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)


class MLFeatureEngineer:
    """Feature engineering for ML trading models."""

    def __init__(self):
        self.supported_symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'SPX500', 'NAS100']
        self.primary_timeframe = 'H1'  # Trend bias
        self.confirmation_timeframe = 'M15'  # Setup confirmation
        self.entry_timeframe = 'M5'  # Entry timing

    def create_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Create comprehensive feature set for ML model.

        Args:
            df: OHLCV DataFrame with columns [open, high, low, close, volume, timestamp]
            symbol: Trading symbol

        Returns:
            DataFrame with engineered features
        """
        if df.empty:
            return pd.DataFrame()

        # Ensure proper datetime index
        df = df.copy()
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp').sort_index()

        # Basic price features
        df = self._add_price_features(df)

        # Trend indicators
        df = self._add_trend_features(df)

        # Momentum indicators
        df = self._add_momentum_features(df)

        # Volatility features
        df = self._add_volatility_features(df)

        # Candle structure
        df = self._add_candle_features(df)

        # Market context
        df = self._add_market_context(df)

        # Multi-timeframe features (if available)
        df = self._add_multitimeframe_features(df)

        # Clean and prepare for ML
        df = self._clean_features(df)

        return df

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price and return-based features."""
        # Log returns
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))

        # Rolling returns
        for period in [5, 10, 20]:
            df[f'rolling_return_{period}'] = df['close'].pct_change(period)

        # Price range features
        df['high_low_range'] = (df['high'] - df['low']) / df['low']
        df['close_open_ratio'] = df['close'] / df['open']

        # Price position in range
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        df['price_position'] = df['price_position'].fillna(0.5)  # Handle zero range

        return df

    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend and moving average features."""
        # EMA calculations
        for period in [20, 50, 200]:
            df[f'ema_{period}'] = self._calculate_ema(df['close'], period)

        # EMA slopes (rate of change)
        for period in [20, 50, 200]:
            df[f'ema_{period}_slope'] = df[f'ema_{period}'].pct_change(5)

        # Price distance from key EMAs
        df['price_dist_ema20'] = (df['close'] - df['ema_20']) / df['ema_20']
        df['price_dist_ema50'] = (df['close'] - df['ema_50']) / df['ema_50']
        df['price_dist_ema200'] = (df['close'] - df['ema_200']) / df['ema_200']

        # EMA alignment (trend strength)
        df['ema_alignment'] = np.where(
            (df['ema_20'] > df['ema_50']) & (df['ema_50'] > df['ema_200']), 1,
            np.where((df['ema_20'] < df['ema_50']) & (df['ema_50'] < df['ema_200']), -1, 0)
        )

        # ADX (Average Directional Index)
        df = self._calculate_adx(df)

        return df

    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum and oscillator features."""
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'])

        # MACD
        df['macd_line'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(df['close'])

        # Stochastic RSI
        df['stoch_rsi'] = self._calculate_stoch_rsi(df['close'])

        # Momentum (rate of change)
        for period in [5, 10, 14]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1

        return df

    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility and risk measures."""
        # ATR (Average True Range)
        df['atr'] = self._calculate_atr(df)

        # Rolling volatility (standard deviation of returns)
        for period in [10, 20, 30]:
            df[f'volatility_{period}'] = df['log_return'].rolling(period).std()

        # Volatility expansion ratio
        df['vol_expansion'] = df['high_low_range'] / df['high_low_range'].rolling(20).mean()

        # Bollinger Bands
        df['bb_middle'], df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        return df

    def _add_candle_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add candle structure and pattern features."""
        # Candle body and wicks
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
        df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
        df['total_range'] = df['high'] - df['low']

        # Wick percentages
        df['upper_wick_pct'] = df['upper_wick'] / df['total_range']
        df['lower_wick_pct'] = df['lower_wick'] / df['total_range']
        df['body_pct'] = df['body_size'] / df['total_range']

        # Candle direction and type
        df['is_bullish'] = (df['close'] > df['open']).astype(int)
        df['is_bearish'] = (df['close'] < df['open']).astype(int)

        # Simple pattern detection
        df['is_pin_bar'] = ((df['upper_wick_pct'] > 0.6) | (df['lower_wick_pct'] > 0.6)).astype(int)
        df['is_doji'] = (df['body_pct'] < 0.1).astype(int)

        # Engulfing pattern (simplified)
        prev_body = df['body_size'].shift(1)
        df['is_bullish_engulfing'] = (
            (df['close'] > df['open']) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1)) &
            (df['body_size'] > prev_body)
        ).astype(int)

        return df

    def _add_market_context(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market session and time-based features."""
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("No datetime index for market context features")
            return df

        # London session (8:00-16:00 GMT)
        london_start = time(8, 0)
        london_end = time(16, 0)

        # New York session (13:30-20:00 GMT)
        ny_start = time(13, 30)
        ny_end = time(20, 0)

        df['london_session'] = [
            london_start <= t <= london_end for t in df.index.time
        ]

        df['ny_session'] = [
            ny_start <= t <= ny_end for t in df.index.time
        ]

        # London-NY overlap (13:30-16:00 GMT)
        df['london_ny_overlap'] = (
            (df['london_session'] == 1) & (df['ny_session'] == 1)
        ).astype(int)

        # Day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df.index.dayofweek

        # Hour of day
        df['hour_of_day'] = df.index.hour

        # Is weekend
        df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)

        return df

    def _add_multitimeframe_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add higher timeframe features (placeholders for now)."""
        # These would require data from multiple timeframes
        # For now, we'll add placeholders that can be populated later

        df['htf_trend'] = 0  # Higher timeframe trend direction
        df['htf_rsi'] = 50   # Higher timeframe RSI
        df['htf_ema_alignment'] = 0  # Higher TF EMA alignment

        return df

    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare features for ML."""
        # Remove NaN values
        df = df.dropna()

        # Remove infinite values
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        # Ensure numeric types
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].astype(np.float32)

        return df

    # Technical indicator calculations
    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator."""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _calculate_stoch_rsi(self, prices: pd.Series, rsi_period: int = 14, stoch_period: int = 14) -> pd.Series:
        """Calculate Stochastic RSI."""
        rsi = self._calculate_rsi(prices, rsi_period)
        return (rsi - rsi.rolling(stoch_period).min()) / (rsi.rolling(stoch_period).max() - rsi.rolling(stoch_period).min())

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        return tr.rolling(period).mean()

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate ADX (Average Directional Index)."""
        # Simplified ADX calculation
        df['tr'] = self._calculate_atr(df, 1)  # True Range

        df['dm_plus'] = np.where(
            (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
            np.maximum(df['high'] - df['high'].shift(1), 0),
            0
        )
        df['dm_minus'] = np.where(
            (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
            np.maximum(df['low'].shift(1) - df['low'], 0),
            0
        )

        df['di_plus'] = 100 * (df['dm_plus'].rolling(period).mean() / df['tr'].rolling(period).mean())
        df['di_minus'] = 100 * (df['dm_minus'].rolling(period).mean() / df['tr'].rolling(period).mean())

        df['dx'] = 100 * abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus'])
        df['adx'] = df['dx'].rolling(period).mean()

        return df

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return sma, upper_band, lower_band