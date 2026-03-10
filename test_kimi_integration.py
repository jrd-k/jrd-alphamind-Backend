#!/usr/bin/env python3
"""
Test Kimi AI Integration
"""

import asyncio
import os

# Set test environment variables
os.environ["KIMI_API_KEY"] = "test_key"  # This will fail but test the integration

async def test_kimi_integration():
    """Test Kimi AI client integration"""
    try:
        from app.services.ai.kimi_client import KimiClient
        print("✓ KimiClient import successful")

        # Test client initialization (will fail due to invalid key, but tests import)
        try:
            client = KimiClient()
            print("✗ KimiClient initialized (should fail with test key)")
        except ValueError as e:
            if "Kimi API key" in str(e):
                print("✓ KimiClient properly validates API key")
            else:
                print(f"✗ Unexpected error: {e}")

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test Brain integration
    try:
        from app.services.brain.brain import Brain
        print("✓ Brain import successful")

        brain = Brain()
        if hasattr(brain, 'kimi'):
            print("✓ Brain has kimi attribute")
            if brain.kimi is None:
                print("✓ Kimi client not initialized (expected without API key)")
            else:
                print("✓ Kimi client initialized")
        else:
            print("✗ Brain missing kimi attribute")

    except Exception as e:
        print(f"✗ Brain integration failed: {e}")
        return False

    print("\n🎉 Kimi AI integration test completed!")
    print("\nTo use Kimi AI:")
    print("1. Get API key from Moonshot AI (https://platform.moonshot.cn/)")
    print("2. Set environment variable: KIMI_API_KEY=your_api_key")
    print("3. Optionally set: KIMI_BASE_URL=https://api.moonshot.cn/v1")
    print("\nSupported models: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k")

    return True

if __name__ == "__main__":
    asyncio.run(test_kimi_integration())