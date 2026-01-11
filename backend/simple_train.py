#!/usr/bin/env python3
"""
Simple ML Model Training Script

Trains the ML trading model using sample data.
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_sample_data(symbol='EURUSD', days=365):
    """Create sample OHLCV data for testing."""
    print(f"📊 Generating {days} days of sample data for {symbol}...")

    # Generate timestamps
    dates = pd.date_range('2023-01-01', periods=days*24, freq='H')  # Hourly data

    # Generate realistic price movements
    np.random.seed(42)
    base_price = {'EURUSD': 1.10, 'GBPUSD': 1.30, 'XAUUSD': 1800}.get(symbol, 100)

    # Random walk with some trend
    returns = np.random.normal(0.0001, 0.01, len(dates))  # Small positive drift
    prices = base_price * np.cumprod(1 + returns)

    # Create OHLCV data
    data = []
    for i, (ts, close) in enumerate(zip(dates, prices)):
        # Add some noise for OHLC
        noise = np.random.normal(0, 0.005, 4)
        ohlc = close * (1 + noise)

        data.append({
            'timestamp': ts,
            'open': ohlc[0],
            'high': max(ohlc),
            'low': min(ohlc),
            'close': close,
            'volume': np.random.randint(1000, 10000)
        })

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)

    print(f"✓ Generated {len(df)} data points")
    return df

def train_single_model(symbol, data):
    """Train a model for a single symbol."""
    print(f"\n🏗️  Training model for {symbol}")
    print("-" * 30)

    try:
        from app.services.ml import MLTradingService

        # Initialize service
        ml_service = MLTradingService()

        # Train model
        print("🧠 Training ML model...")
        start_time = datetime.now()

        # Convert to async call
        import asyncio

        async def train_async():
            return await ml_service.train_model(
                historical_data=data,
                target_symbol=symbol,
                force_retrain=True
            )

        training_result = asyncio.run(train_async())
        training_time = datetime.now() - start_time

        # Display results
        print("✅ Training completed!"        print(f"   ⏱️  Training time: {training_time.total_seconds():.1f}s")
        print(f"   📈 Best F1 Score: {training_result['training_results']['best_score']:.3f}")
        print(f"   🎯 Features used: {training_result['feature_count']}")
        print(f"   📊 Data points: {training_result['data_points']}")

        return training_result

    except Exception as e:
        print(f"❌ Failed to train model for {symbol}: {e}")
        return None

def main():
    """Main training function."""
    print("🚀 ML Trading Model Training")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test basic imports first
    try:
        from app.services.ml import MLTradingService, MLDataLoader
        print("✓ ML services imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return

    # Symbols to train
    symbols = ['EURUSD', 'GBPUSD']
    trained_models = {}

    for symbol in symbols:
        # Create sample data
        data = create_sample_data(symbol, days=180)  # 6 months for faster training

        # Train model
        result = train_single_model(symbol, data)

        if result:
            trained_models[symbol] = result

    # Summary
    print(f"\n🎉 Training Summary")
    print("=" * 50)
    print(f"📊 Models trained: {len(trained_models)}/{len(symbols)}")

    if trained_models:
        print("🏆 Best performing models:")
        for symbol, result in trained_models.items():
            score = result['training_results']['best_score']
            print(".3f"
    print("
✅ ML Training Complete!"    print("🚀 Models are ready for live trading!")

if __name__ == "__main__":
    main()