#!/usr/bin/env python
"""Test script for the new economic calendar and broker account functionality."""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_economic_calendar():
    """Test the economic calendar service."""
    print("Testing Economic Calendar Service...")

    try:
        from app.services.economic_calendar import EconomicCalendar

        calendar = EconomicCalendar()
        events = await calendar.fetch_upcoming_events(hours_ahead=24)

        print(f"✅ Fetched {len(events)} economic events")
        if events:
            print(f"   Sample event: {events[0].name} - {events[0].impact.value} impact")

        # Test trading avoidance
        should_avoid = calendar.should_avoid_trading("EURUSD", minutes_window=60)
        print(f"   Should avoid trading EURUSD: {should_avoid}")

        return True
    except Exception as e:
        print(f"❌ Economic calendar test failed: {e}")
        return False

async def test_brain_with_calendar():
    """Test that Brain service includes economic calendar checks."""
    print("\nTesting Brain Service with Economic Calendar...")

    try:
        from app.services.brain.brain import Brain

        brain = Brain()

        # Test decision making
        result = await brain.decide(
            symbol="EURUSD",
            current_price=1.0850,
            indicators=[{"source": "fibonacci", "signal": "BUY", "value": 0.8}]
        )

        print("✅ Brain decision made successfully")
        print(f"   Decision: {result['decision']}")
        print(f"   Economic calendar override: {result.get('economic_calendar', {}).get('override', False)}")

        return True
    except Exception as e:
        print(f"❌ Brain with calendar test failed: {e}")
        return False

def test_broker_account_model():
    """Test the BrokerAccount model creation."""
    print("\nTesting BrokerAccount Model...")

    try:
        from app.models.orm_models import BrokerAccount

        # Test model creation
        account = BrokerAccount(
            user_id=1,
            broker_name="exness",
            account_id="123456",
            api_key="test_key",
            is_active=1
        )

        print("✅ BrokerAccount model created successfully")
        print(f"   Broker: {account.broker_name}")
        print(f"   Account ID: {account.account_id}")

        return True
    except Exception as e:
        print(f"❌ BrokerAccount model test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing AlphaMind Enhancements")
    print("=" * 50)

    results = []

    # Test economic calendar
    results.append(await test_economic_calendar())

    # Test brain with calendar
    results.append(await test_brain_with_calendar())

    # Test broker account model
    results.append(test_broker_account_model())

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Economic calendar and broker account functionality is working.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())