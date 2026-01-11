"""
ML Data Loader

Handles market data ingestion and preprocessing:
- Multiple data sources (CSV, API, database)
- Data validation and cleaning
- Multi-timeframe data aggregation
- Market data storage and retrieval
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import asyncio
from datetime import datetime, timedelta
import os
import glob

logger = logging.getLogger(__name__)


class MLDataLoader:
    """Data loader for ML training and inference."""

    def __init__(self,
                 data_dir: str = "data",
                 cache_dir: str = "cache",
                 supported_symbols: List[str] = None,
                 supported_timeframes: List[str] = None):
        """
        Initialize data loader.

        Args:
            data_dir: Directory for data storage
            cache_dir: Directory for cached data
            supported_symbols: List of supported trading symbols
            supported_timeframes: List of supported timeframes
        """
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        self.supported_symbols = supported_symbols or ['EURUSD', 'GBPUSD', 'XAUUSD', 'SPY', 'QQQ']
        self.supported_timeframes = supported_timeframes or ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']

        # Create directories
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

        # Data cache
        self.data_cache = {}
        self.last_update = {}

    async def load_historical_data(self,
                                  symbol: str,
                                  timeframe: str = 'H1',
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None,
                                  limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load historical market data.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of records

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}"
            if cache_key in self.data_cache:
                cached_data = self.data_cache[cache_key]
                if self._is_cache_valid(cache_key):
                    logger.info(f"Using cached data for {cache_key}")
                    return self._filter_data(cached_data, start_date, end_date, limit)

            # Load from file
            data = await self._load_from_file(symbol, timeframe)

            if data.empty:
                # Try to load from API or generate sample data
                data = await self._load_from_api(symbol, timeframe, start_date, end_date)

            if data.empty:
                logger.warning(f"No data available for {symbol} {timeframe}")
                return pd.DataFrame()

            # Validate and clean data
            data = self._validate_and_clean_data(data)

            # Cache data
            self.data_cache[cache_key] = data
            self.last_update[cache_key] = datetime.now()

            # Filter and return
            return self._filter_data(data, start_date, end_date, limit)

        except Exception as e:
            logger.error(f"Error loading historical data for {symbol}: {e}")
            return pd.DataFrame()

    async def _load_from_file(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Load data from local files."""
        try:
            # Look for data files
            pattern = os.path.join(self.data_dir, f"{symbol}_{timeframe}_*.csv")
            files = glob.glob(pattern)

            if not files:
                return pd.DataFrame()

            # Use most recent file
            latest_file = max(files, key=os.path.getctime)

            # Read CSV
            data = pd.read_csv(latest_file, parse_dates=['timestamp'])
            data.set_index('timestamp', inplace=True)
            data.sort_index(inplace=True)

            logger.info(f"Loaded {len(data)} records from {latest_file}")
            return data

        except Exception as e:
            logger.error(f"Error loading from file: {e}")
            return pd.DataFrame()

    async def _load_from_api(self,
                           symbol: str,
                           timeframe: str,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Load data from external API."""
        # Placeholder for API integration
        # This would connect to trading APIs like Alpha Vantage, Yahoo Finance, etc.

        logger.info(f"API loading not implemented for {symbol} {timeframe}")
        return pd.DataFrame()

    def _validate_and_clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean market data."""
        if data.empty:
            return data

        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Remove duplicates
        data = data[~data.index.duplicated(keep='first')]

        # Sort by timestamp
        data.sort_index(inplace=True)

        # Fill missing values (forward fill, then backward fill)
        data.fillna(method='ffill', inplace=True)
        data.fillna(method='bfill', inplace=True)

        # Remove rows with invalid prices
        valid_mask = (
            (data['high'] >= data['low']) &
            (data['close'] >= data['low']) &
            (data['close'] <= data['high']) &
            (data['open'] >= data['low']) &
            (data['open'] <= data['high'])
        )
        data = data[valid_mask]

        # Ensure positive volume
        if 'volume' in data.columns:
            data = data[data['volume'] >= 0]

        return data

    def _filter_data(self,
                    data: pd.DataFrame,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    limit: Optional[int] = None) -> pd.DataFrame:
        """Filter data by date range and limit."""
        if data.empty:
            return data

        # Date filtering
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]

        # Limit records
        if limit and len(data) > limit:
            data = data.tail(limit)

        return data

    def _is_cache_valid(self, cache_key: str, max_age_minutes: int = 60) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.last_update:
            return False

        age = datetime.now() - self.last_update[cache_key]
        return age < timedelta(minutes=max_age_minutes)

    async def save_data(self, data: pd.DataFrame, symbol: str, timeframe: str):
        """Save data to disk."""
        try:
            if data.empty:
                return

            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_{timeframe}_{timestamp}.csv"
            filepath = os.path.join(self.data_dir, filename)

            # Save to CSV
            data.to_csv(filepath)

            logger.info(f"Saved {len(data)} records to {filepath}")

        except Exception as e:
            logger.error(f"Error saving data: {e}")

    async def get_multi_timeframe_data(self,
                                      symbol: str,
                                      timeframes: List[str],
                                      start_date: Optional[datetime] = None,
                                      end_date: Optional[datetime] = None) -> Dict[str, pd.DataFrame]:
        """
        Load data for multiple timeframes.

        Args:
            symbol: Trading symbol
            timeframes: List of timeframes to load
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of DataFrames by timeframe
        """
        multi_data = {}

        for tf in timeframes:
            if tf in self.supported_timeframes:
                data = await self.load_historical_data(symbol, tf, start_date, end_date)
                if not data.empty:
                    multi_data[tf] = data

        return multi_data

    async def resample_data(self,
                           data: pd.DataFrame,
                           target_timeframe: str) -> pd.DataFrame:
        """
        Resample data to different timeframe.

        Args:
            data: Source DataFrame
            target_timeframe: Target timeframe (e.g., 'H1', 'D1')

        Returns:
            Resampled DataFrame
        """
        if data.empty:
            return data

        # Map timeframe to pandas frequency
        freq_map = {
            'M1': '1min',
            'M5': '5min',
            'M15': '15min',
            'H1': '1H',
            'H4': '4H',
            'D1': '1D'
        }

        if target_timeframe not in freq_map:
            raise ValueError(f"Unsupported timeframe: {target_timeframe}")

        freq = freq_map[target_timeframe]

        # Resample OHLCV data
        resampled = data.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        return resampled

    def get_data_info(self) -> Dict[str, Any]:
        """Get information about available data."""
        try:
            info = {
                'supported_symbols': self.supported_symbols,
                'supported_timeframes': self.supported_timeframes,
                'cached_symbols': list(self.data_cache.keys()),
                'data_directory': self.data_dir,
                'cache_directory': self.cache_dir
            }

            # Check available files
            if os.path.exists(self.data_dir):
                csv_files = glob.glob(os.path.join(self.data_dir, "*.csv"))
                info['available_files'] = len(csv_files)
                info['file_list'] = [os.path.basename(f) for f in csv_files[:10]]  # First 10
            else:
                info['available_files'] = 0
                info['file_list'] = []

            return info

        except Exception as e:
            logger.error(f"Error getting data info: {e}")
            return {}

    async def generate_sample_data(self,
                                  symbol: str,
                                  timeframe: str = 'H1',
                                  days: int = 365) -> pd.DataFrame:
        """
        Generate sample market data for testing.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            days: Number of days of data to generate

        Returns:
            DataFrame with sample OHLCV data
        """
        try:
            # Generate timestamps
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            if timeframe == 'H1':
                freq = 'H'
            elif timeframe == 'D1':
                freq = 'D'
            else:
                freq = 'H'  # Default to hourly

            timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)

            # Generate random walk prices
            np.random.seed(42)  # For reproducibility

            # Base price depending on symbol
            base_prices = {
                'EURUSD': 1.10,
                'GBPUSD': 1.30,
                'XAUUSD': 1800,
                'SPY': 400,
                'QQQ': 300
            }

            base_price = base_prices.get(symbol, 100)

            # Generate price movements
            n_points = len(timestamps)
            returns = np.random.normal(0, 0.02, n_points)  # 2% daily volatility

            # Cumulative returns
            cum_returns = np.cumprod(1 + returns)
            prices = base_price * cum_returns

            # Generate OHLC from close prices
            data = []
            for i, (ts, close) in enumerate(zip(timestamps, prices)):
                # Add some noise to create OHLC
                noise = np.random.normal(0, 0.005, 4)  # 0.5% noise
                ohlc = close * (1 + noise)

                # Ensure OHLC relationships
                open_price = ohlc[0]
                high_price = max(ohlc)
                low_price = min(ohlc)
                close_price = ohlc[3]

                # Volume (random)
                volume = np.random.randint(1000, 10000)

                data.append({
                    'timestamp': ts,
                    'open': round(open_price, 5 if 'USD' in symbol else 2),
                    'high': round(high_price, 5 if 'USD' in symbol else 2),
                    'low': round(low_price, 5 if 'USD' in symbol else 2),
                    'close': round(close_price, 5 if 'USD' in symbol else 2),
                    'volume': volume
                })

            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)

            logger.info(f"Generated {len(df)} sample records for {symbol} {timeframe}")
            return df

        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
            return pd.DataFrame()