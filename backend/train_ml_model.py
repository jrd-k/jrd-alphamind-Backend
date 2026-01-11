#!/usr/bin/env python3
"""
ML Model Training Script

Trains the ML trading model using historical data and validates performance.
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ml import MLTradingService, MLDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def train_ml_model():
    """Train the ML trading model."""
    print("🤖 Starting ML Model Training")
    print("=" * 50)

    try:
        # Initialize services
        print("📚 Initializing ML services...")
        data_loader = MLDataLoader()
        ml_service = MLTradingService()

        # Training configuration
        symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        timeframe = 'H1'
        training_days = 365  # 1 year of data

        trained_models = {}

        for symbol in symbols:
            print(f"\n🏗️  Training model for {symbol}")
            print("-" * 30)

            try:
                # Generate sample data (in production, load real data)
                print(f"📊 Generating {training_days} days of sample data...")
                historical_data = await data_loader.generate_sample_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    days=training_days
                )

                if historical_data.empty:
                    print(f"❌ No data available for {symbol}")
                    continue

                print(f"✓ Generated {len(historical_data)} data points")

                # Train the model
                print("🧠 Training ML model...")
                start_time = datetime.now()

                training_result = await ml_service.train_model(
                    historical_data=historical_data,
                    target_symbol=symbol,
                    force_retrain=True
                )

                training_time = datetime.now() - start_time

                # Store results
                trained_models[symbol] = training_result

                # Display results
                print("✅ Training completed!"                print(f"   ⏱️  Training time: {training_time.total_seconds():.1f}s")
                print(f"   📈 Best F1 Score: {training_result['training_results']['best_score']:.3f}")
                print(f"   🎯 Features used: {training_result['feature_count']}")
                print(f"   📊 Data points: {training_result['data_points']}")

                # Get detailed performance
                performance = await ml_service.get_model_performance(symbol)
                if 'training_metrics' in performance:
                    metrics = performance['training_metrics']
                    print("   📋 Cross-validation metrics:"                    print(".3f"                    print(".3f"                    print(".3f"                    print(".3f"
            except Exception as e:
                print(f"❌ Failed to train model for {symbol}: {e}")
                continue

        # Summary
        print(f"\n🎉 Training Summary")
        print("=" * 50)
        print(f"📊 Models trained: {len(trained_models)}/{len(symbols)}")

        if trained_models:
            print("🏆 Best performing models:")
            for symbol, result in trained_models.items():
                score = result['training_results']['best_score']
                print(".3f"
        # Save models
        print("💾 Saving trained models...")
        await ml_service.load_models()  # This will save them to disk

        # Service status
        status = ml_service.get_service_status()
        print("
📈 Service Status:"        print(f"   🤖 Live trading: {status['is_live']}")
        print(f"   📚 Trained models: {status['trained_models_count']}")
        print(f"   💰 Available symbols: {status['available_symbols']}")

        print("
✅ ML Training Pipeline Complete!"        print("🚀 Ready for live trading or further backtesting!")

        return trained_models

    except Exception as e:
        logger.error(f"Training failed: {e}")
        print(f"❌ Training failed: {e}")
        return None


async def quick_validation_test():
    """Run a quick validation test."""
    print("\n🧪 Running Quick Validation Test")
    print("-" * 40)

    try:
        from app.services.ml import MLFeatureEngineer, MLLabelGenerator

        # Create sample data
        import pandas as pd
        import numpy as np

        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)

        # Generate realistic price data
        base_price = 1.10
        returns = np.random.normal(0, 0.005, len(dates))
        prices = base_price * np.cumprod(1 + returns)

        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.normal(0, 0.001, len(dates))),
            'high': prices * (1 + np.random.normal(0, 0.002, len(dates))),
            'low': prices * (1 - np.random.normal(0, 0.002, len(dates))),
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        data.set_index('timestamp', inplace=True)

        # Test feature engineering
        print("🔧 Testing feature engineering...")
        fe = MLFeatureEngineer()
        featured_data = fe.create_features(data, 'EURUSD')
        print(f"✓ Created {len(featured_data.columns)} features")

        # Test label generation
        print("🏷️  Testing label generation...")
        lg = MLLabelGenerator()
        labeled_data = lg.create_labels(featured_data)
        labeled_data = lg.filter_valid_labels(labeled_data)

        label_stats = lg.get_label_stats(labeled_data)
        print("✓ Generated labels:"        print(".1%"        print(".3f"        print(".3f"
        return True

    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 ML Trading Model Training")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    async def main():
        # Quick validation first
        validation_passed = await quick_validation_test()

        if not validation_passed:
            print("❌ Validation failed, aborting training")
            sys.exit(1)

        # Full training
        trained_models = await train_ml_model()

        if trained_models:
            print("
🎯 Training completed successfully!"            sys.exit(0)
        else:
            print("
❌ Training failed"            sys.exit(1)

    asyncio.run(main())