"""
ML Trading Label Generation

Creates classification labels for ML training:
- Direction classification based on future returns
- Multi-class labels (long/short/no-trade)
- Handles transaction costs and spread buffers
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MLLabelGenerator:
    """Generate labels for ML trading model training."""

    def __init__(self,
                 future_periods: int = 5,
                 return_threshold: float = 0.001,  # 0.1% minimum return
                 transaction_cost_pct: float = 0.0005,  # 0.05% spread + commission
                 min_confidence_periods: int = 3):
        """
        Initialize label generator.

        Args:
            future_periods: Number of future periods to look ahead
            return_threshold: Minimum return threshold (after costs)
            transaction_cost_pct: Transaction cost percentage
            min_confidence_periods: Minimum periods for confident prediction
        """
        self.future_periods = future_periods
        self.return_threshold = return_threshold
        self.transaction_cost_pct = transaction_cost_pct
        self.min_confidence_periods = min_confidence_periods

    def create_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create ML labels from price data.

        Args:
            df: DataFrame with OHLCV data and engineered features

        Returns:
            DataFrame with added label columns
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()

        # Calculate future returns
        df = self._calculate_future_returns(df)

        # Create binary classification labels
        df = self._create_binary_labels(df)

        # Create multi-class labels (optional)
        df = self._create_multiclass_labels(df)

        # Add confidence scores
        df = self._add_confidence_scores(df)

        return df

    def _calculate_future_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate future returns over specified periods."""
        # Future price returns
        for periods in [1, 3, 5, 10]:
            df[f'future_return_{periods}'] = (
                df['close'].shift(-periods) / df['close'] - 1
            )

        # Maximum return over future periods
        df['future_return_max'] = df[[f'future_return_{p}' for p in [1, 3, 5]]].max(axis=1)

        # Minimum return over future periods
        df['future_return_min'] = df[[f'future_return_{p}' for p in [1, 3, 5]]].min(axis=1)

        # Net return after transaction costs
        df['future_return_net'] = df[f'future_return_{self.future_periods}'] - (2 * self.transaction_cost_pct)

        return df

    def _create_binary_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create binary classification labels.
        1 = Long (expecting price increase)
        0 = No trade/Short (expecting price decrease or no clear direction)
        """
        # Primary label: Will price go up enough to cover costs?
        df['label_binary'] = (
            df['future_return_net'] > self.return_threshold
        ).astype(int)

        # Alternative: Strong directional move
        df['label_strong_bull'] = (
            (df['future_return_max'] > 2 * self.return_threshold) &
            (df['future_return_min'] > -self.return_threshold)
        ).astype(int)

        df['label_strong_bear'] = (
            (df['future_return_min'] < -2 * self.return_threshold) &
            (df['future_return_max'] < self.return_threshold)
        ).astype(int)

        return df

    def _create_multiclass_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create multi-class labels.
        0 = No trade (unclear direction)
        1 = Long (bullish)
        2 = Short (bearish)
        """
        # Initialize as no trade
        df['label_multiclass'] = 0

        # Long signals
        long_condition = (
            (df['future_return_net'] > self.return_threshold) &
            (df['future_return_min'] > -self.return_threshold)  # No deep drawdown
        )
        df.loc[long_condition, 'label_multiclass'] = 1

        # Short signals
        short_condition = (
            (df['future_return_net'] < -self.return_threshold) &
            (df['future_return_max'] < self.return_threshold)  # No deep rally
        )
        df.loc[short_condition, 'label_multiclass'] = 2

        return df

    def _add_confidence_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add confidence scores for each prediction."""
        # Confidence based on return magnitude
        df['confidence_score'] = np.abs(df['future_return_net'])

        # Normalize to 0-1 scale
        max_confidence = df['confidence_score'].quantile(0.95)  # 95th percentile
        df['confidence_score'] = np.clip(df['confidence_score'] / max_confidence, 0, 1)

        # Alternative: Time-based confidence (closer predictions are more confident)
        df['time_confidence'] = 1.0 / (1 + np.abs(df[f'future_return_{self.future_periods}'] - df['future_return_1']))

        return df

    def get_label_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get statistics about the generated labels."""
        if df.empty or 'label_binary' not in df.columns:
            return {}

        stats = {
            'total_samples': len(df),
            'positive_labels': (df['label_binary'] == 1).sum(),
            'negative_labels': (df['label_binary'] == 0).sum(),
            'positive_ratio': (df['label_binary'] == 1).mean(),
            'avg_return_positive': df[df['label_binary'] == 1]['future_return_net'].mean(),
            'avg_return_negative': df[df['label_binary'] == 0]['future_return_net'].mean(),
            'avg_confidence': df['confidence_score'].mean(),
        }

        # Multi-class stats
        if 'label_multiclass' in df.columns:
            stats.update({
                'no_trade_ratio': (df['label_multiclass'] == 0).mean(),
                'long_ratio': (df['label_multiclass'] == 1).mean(),
                'short_ratio': (df['label_multiclass'] == 2).mean(),
            })

        return stats

    def filter_valid_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out rows with invalid labels (NaN future returns)."""
        valid_mask = df[f'future_return_{self.future_periods}'].notna()
        return df[valid_mask].copy()