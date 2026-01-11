#!/usr/bin/env python3
"""
Minimal ML Training Script

Quick training test with small dataset.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_minimal_data(symbol='EURUSD', points=100):
    """Create minimal test data."""
    print(f"📊 Creating {points} data points for {symbol}...")

    dates = pd.date_range('2023-01-01', periods=points, freq='H')
    np.random.seed(42)

    base_price = 1.10
    returns = np.random.normal(0, 0.005, points)
    prices = base_price * np.cumprod(1 + returns)

    data = []
    for ts, close in zip(dates, prices):
        noise = np.random.normal(0, 0.002, 4)
        ohlc = close * (1 + noise)

        data.append({
            'timestamp': ts,
            'open': ohlc[0],
            'high': max(ohlc),
            'low': min(ohlc),
            'close': close,
            'volume': np.random.randint(1000, 5000)
        })

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def main():
    """Minimal training test."""
    print("🚀 Minimal ML Training Test")
    print("=" * 40)

    # Create test data
    data = create_minimal_data(points=50)  # Very small dataset
    print(f"✓ Created {len(data)} data points")

    # Test feature engineering
    from app.services.ml.feature_engineering import MLFeatureEngineer
    fe = MLFeatureEngineer()
    featured_data = fe.create_features(data, 'EURUSD')
    print(f"✓ Feature engineering: {len(featured_data.columns)} features")

    # Test label generation
    from app.services.ml.label_generation import MLLabelGenerator
    lg = MLLabelGenerator()
    labeled_data = lg.create_labels(featured_data)
    labeled_data = lg.filter_valid_labels(labeled_data)
    print(f"✓ Label generation: {len(labeled_data)} labeled samples")

    # Quick training test
    print("🧠 Testing model training...")
    from app.services.ml.model_training import MLModelTrainer

    trainer = MLModelTrainer(n_splits=2)  # Minimal CV

    # Get feature columns
    feature_cols = [col for col in labeled_data.columns
                   if col.startswith(('price_', 'trend_', 'momentum_', 'volatility_',
                                    'candle_', 'market_'))]

    if len(feature_cols) > 5 and len(labeled_data) > 10:
        try:
            # Use only first 5 features for speed
            feature_cols = feature_cols[:5]

            results = trainer.train_walk_forward(
                df=labeled_data,
                feature_cols=feature_cols,
                label_col='label_binary'
            )

            print("✅ Training successful!"            print(".3f"            print(f"   📊 Features used: {len(feature_cols)}")

        except Exception as e:
            print(f"❌ Training failed: {e}")
    else:
        print("❌ Insufficient data for training")

    print("🎉 Test completed!")

if __name__ == "__main__":
    main()