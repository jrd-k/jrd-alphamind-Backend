#!/usr/bin/env python3
"""
Test script for ML Trading Service

Demonstrates the complete ML pipeline:
1. Generate sample market data
2. Create features and labels
3. Train XGBoost model
4. Validate performance
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml import (
    MLTradingService,
    MLDataLoader,
    MLFeatureEngineer,
    MLLabelGenerator
)


async def test_ml_pipeline():
    """Test the complete ML trading pipeline."""
    print("🚀 Testing ML Trading Pipeline")
    print("=" * 50)

    try:
        # Step 1: Initialize services
        print("1. Initializing ML services...")
        data_loader = MLDataLoader()
        ml_service = MLTradingService()

        print("✓ Services initialized")

        # Step 2: Generate sample data
        print("\n2. Generating sample market data...")
        sample_data = await data_loader.generate_sample_data(
            symbol='EURUSD',
            timeframe='H1',
            days=365
        )

        if sample_data.empty:
            print("❌ Failed to generate sample data")
            return

        print(f"✓ Generated {len(sample_data)} data points")

        # Step 3: Test feature engineering
        print("\n3. Testing feature engineering...")
        feature_engineer = MLFeatureEngineer()
        featured_data = feature_engineer.create_features(sample_data)

        feature_cols = [col for col in featured_data.columns
                       if col.startswith(('price_', 'trend_', 'momentum_', 'volatility_',
                                        'candle_', 'market_'))]

        print(f"✓ Created {len(feature_cols)} features: {feature_cols[:5]}...")

        # Step 4: Test label generation
        print("\n4. Testing label generation...")
        label_generator = MLLabelGenerator()
        labeled_data = label_generator.create_labels(featured_data)
        labeled_data = label_generator.filter_valid_labels(labeled_data)

        if labeled_data.empty:
            print("❌ No valid labeled data")
            return

        label_stats = label_generator.get_label_stats(labeled_data)
        print(f"✓ Generated labels: {label_stats}")

        # Step 5: Test model training
        print("\n5. Testing model training...")
        training_result = await ml_service.train_model(
            historical_data=sample_data,
            target_symbol='EURUSD',
            force_retrain=True
        )

        print("✓ Model training completed")
        print(f"  - Features: {training_result['feature_count']}")
        print(f"  - Data points: {training_result['data_points']}")
        print(f"  - Best F1 Score: {training_result['training_results']['best_score']:.3f}")

        # Step 6: Test performance metrics
        print("\n6. Testing performance metrics...")
        performance = await ml_service.get_model_performance('EURUSD')

        if 'training_metrics' in performance:
            metrics = performance['training_metrics']
            print("✓ Training metrics:"            print(".3f"            print(".3f"            print(".3f"
        # Step 7: Test service status
        print("\n7. Testing service status...")
        status = ml_service.get_service_status()
        print(f"✓ Service status: {status}")

        print("\n🎉 ML Pipeline Test Completed Successfully!")
        print("\n📊 Summary:")
        print(f"   • Sample data: {len(sample_data)} points")
        print(f"   • Features created: {len(feature_cols)}")
        print(f"   • Labeled data: {len(labeled_data)} points")
        print(".1%")
        print(f"   • Model trained: {training_result['symbol']}")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_loader():
    """Test data loader functionality."""
    print("\n🔍 Testing Data Loader")
    print("-" * 30)

    try:
        data_loader = MLDataLoader()

        # Test data info
        info = data_loader.get_data_info()
        print(f"✓ Supported symbols: {info['supported_symbols']}")
        print(f"✓ Supported timeframes: {info['supported_timeframes']}")

        # Test sample data generation
        sample_data = await data_loader.generate_sample_data('GBPUSD', 'H1', 30)
        print(f"✓ Generated sample data: {len(sample_data)} points")

        return True

    except Exception as e:
        print(f"❌ Data loader test failed: {e}")
        return False


if __name__ == "__main__":
    print("🤖 ML Trading Service Test Suite")
    print("=" * 50)

    async def main():
        # Test data loader
        data_test = await test_data_loader()

        # Test full pipeline
        pipeline_test = await test_ml_pipeline()

        if data_test and pipeline_test:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)

    asyncio.run(main())