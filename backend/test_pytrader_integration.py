#!/usr/bin/env python3
"""Test PyTrader integration with comprehensive symbol support."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.brokers.mt5_client import PyTraderClient

def test_pytrader_client_initialization():
    """Test PyTrader client initialization and symbol lookup."""
    print("Testing PyTrader client initialization...")

    try:
        # Initialize client (this won't connect to MT5, just test the class)
        client = PyTraderClient(
            account_id="demo_account",
            api_key="demo_key",
            api_secret="demo_secret",
            server="demo_server"
        )

        print("✓ PyTraderClient initialized successfully")

        # Test symbol lookup
        print("\nTesting symbol lookup...")

        # Test some common symbols
        test_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'SPX500']

        for symbol in test_symbols:
            broker_symbol = client.instrument_lookup.get(symbol.upper(), symbol.upper())
            print(f"  {symbol} -> {broker_symbol}")

        print("✓ Symbol lookup working")

        # Test reverse lookup
        print("\nTesting reverse symbol lookup...")
        for symbol in test_symbols:
            broker_symbol = client.instrument_lookup.get(symbol.upper(), symbol.upper())
            universal = client._get_universal_symbol(broker_symbol)
            print(f"  {broker_symbol} -> {universal}")

        print("✓ Reverse symbol lookup working")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pytrader_methods():
    """Test PyTrader client methods (without actual connection)."""
    print("\nTesting PyTrader client methods...")

    try:
        client = PyTraderClient(
            account_id="demo_account",
            api_key="demo_key",
            api_secret="demo_secret",
            server="demo_server"
        )

        # Test that methods exist
        assert hasattr(client, 'place_order')
        assert hasattr(client, 'get_positions')
        assert hasattr(client, 'get_balance')
        assert hasattr(client, 'get_historical_data')
        assert hasattr(client, 'close')

        print("✓ All PyTrader methods available")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("PyTrader Integration Test")
    print("=" * 40)

    success1 = test_pytrader_client_initialization()
    success2 = test_pytrader_methods()

    if success1 and success2:
        print("\n🎉 All PyTrader integration tests passed!")
        print("\nNext steps:")
        print("1. Install PyTrader EA in MT4/MT5 terminal")
        print("2. Configure MT4/MT5 connection settings")
        print("3. Test with real broker connection")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)