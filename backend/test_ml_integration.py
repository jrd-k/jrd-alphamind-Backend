#!/usr/bin/env python3
"""
Test script for ML integration with Brain service.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ml_integration():
    """Test ML service integration."""
    try:
        print("Testing ML integration...")

        # Import ML service
        from app.services.ml import MLTradingService
        print("✓ ML service imported successfully")

        # Create ML service instance
        ml_service = MLTradingService()
        print("✓ ML service initialized")

        # Load models
        loaded = await ml_service.load_models()
        print(f"✓ Models loaded: {loaded}")

        # Get service status
        status = ml_service.get_service_status()
        print(f"✓ Service status: {status}")

        # Test prediction with sample features
        sample_features = {
            'close': 1.0812,
            'volume': 1000,
            'rsi': 65.2,
            'macd': 0.0012,
            'bb_position': 0.3
        }

        prediction = await ml_service.predict('EURUSD', sample_features)
        if prediction:
            print(f"✓ Prediction successful: {prediction}")
        else:
            print("⚠ No prediction (no trained models)")

        print("ML integration test completed successfully!")

    except Exception as e:
        print(f"✗ Error during ML integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def test_brain_integration():
    """Test Brain service with ML integration."""
    try:
        print("\nTesting Brain integration...")

        # Import Brain service
        from app.services.brain.brain import Brain
        print("✓ Brain service imported successfully")

        # Create Brain instance
        brain = Brain()
        print("✓ Brain service initialized")

        # Test decision with sample data
        sample_candles = [
            {'timestamp': '2025-01-17T10:00:00Z', 'open': 1.0800, 'high': 1.0820, 'low': 1.0790, 'close': 1.0812, 'volume': 1000}
        ]

        sample_indicators = [
            {'source': 'rsi', 'name': 'rsi', 'value': 65.2},
            {'source': 'macd', 'name': 'macd', 'value': 0.0012},
            {'source': 'bollinger', 'name': 'bb_position', 'value': 0.3}
        ]

        decision = await brain.decide(
            symbol='EURUSD',
            candles=sample_candles,
            current_price=1.0812,
            indicators=sample_indicators
        )

        print(f"✓ Brain decision: {decision}")
        print("Brain integration test completed successfully!")

    except Exception as e:
        print(f"✗ Error during Brain integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def main():
    """Run all tests."""
    print("Starting ML integration tests...\n")

    ml_success = await test_ml_integration()
    brain_success = await test_brain_integration()

    if ml_success and brain_success:
        print("\n🎉 All tests passed! ML integration is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)