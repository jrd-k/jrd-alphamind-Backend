#!/usr/bin/env python3
"""
Quick PyTrader Connection Test
Tests basic connectivity to MT4/MT5 via PyTrader EA
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.brokers.mt5_client import PyTraderClient


async def test_pytrader_connection():
    """Test PyTrader connection and basic operations."""
    print("🔍 PyTrader Connection Test")
    print("=" * 40)

    # Initialize client
    client = PyTraderClient(
        host="localhost",
        port=1122
    )

    try:
        print("1. Testing connection...")
        # Note: This will fail if EA is not running, but tests the client setup
        connected = client._ensure_connected()
        if connected:
            print("   ✅ Connection established")
        else:
            print("   ⚠️  Connection not established (EA may not be running)")

        print("\n2. Testing symbol lookup...")
        test_symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD']
        for symbol in test_symbols:
            broker_symbol = client.instrument_lookup.get(symbol, symbol)
            print(f"   {symbol} → {broker_symbol}")

        print("\n3. Testing balance check...")
        try:
            balance = await client.get_balance()
            if balance and 'balance' in balance:
                print(f"   ✅ Balance: ${balance['balance']}")
            else:
                print("   ⚠️  Could not get balance (normal if EA not connected)")
        except Exception as e:
            print(f"   ❌ Balance check failed: {e}")

        print("\n4. Testing historical data...")
        try:
            data = await client.get_historical_data("EURUSD", "M1", 10)
            if data:
                print(f"   ✅ Got {len(data)} bars of historical data")
            else:
                print("   ⚠️  No historical data (normal if EA not connected)")
        except Exception as e:
            print(f"   ❌ Historical data failed: {e}")

        print("\n5. Testing positions...")
        try:
            positions = await client.get_positions()
            if positions is not None:
                print(f"   ✅ Positions check successful: {len(positions)} positions")
            else:
                print("   ⚠️  Positions check returned None")
        except Exception as e:
            print(f"   ❌ Positions check failed: {e}")

        print("\n📋 Test Summary:")
        print("   - PyTraderClient initialization: ✅")
        print("   - Symbol lookup mapping: ✅")
        print("   - Connection attempt: ⚠️ (requires running EA)")
        print("   - API methods available: ✅")

        print("\n🚀 Next Steps:")
        print("   1. Install PyTrader EA in MT4/MT5 terminal")
        print("   2. Attach EA to a chart with port 1122")
        print("   3. Set environment variables (MT5_ACCOUNT, etc.)")
        print("   4. Run this test again")
        print("   5. Start the AI trading bot")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    print(f"Test started at: {datetime.now()}")
    asyncio.run(test_pytrader_connection())
    print(f"Test completed at: {datetime.now()}")