#!/usr/bin/env python3
"""
Comprehensive System Test Suite
Tests all components of the AI Trading System
"""

import asyncio
import os
import sys
import subprocess
import time
from datetime import datetime
import requests
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

class SystemTester:
    """Comprehensive system testing suite."""

    def __init__(self):
        self.results = {}
        self.backend_process = None
        self.frontend_process = None

    def log(self, message, status="INFO"):
        """Log test results."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icons = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️",
            "INFO": "ℹ️"
        }
        icon = status_icons.get(status, "ℹ️")
        print(f"{timestamp} {icon} {message}")

    async def test_database(self):
        """Test database initialization."""
        self.log("Testing database initialization...")
        try:
            from app.core.database import init_db
            init_db()
            self.results["database"] = "PASS"
            self.log("Database initialization: PASS")
            return True
        except Exception as e:
            self.results["database"] = "FAIL"
            self.log(f"Database initialization: FAIL - {e}")
            return False

    async def test_imports(self):
        """Test all critical imports."""
        self.log("Testing critical imports...")
        try:
            # Test core imports
            from app.main import create_app
            from app.services.brain.brain import Brain
            from app.services.brokers.mt5_client import PyTraderClient
            from app.services.brokers.paper_client import PaperTradingClient
            from app.services.execution import execute_order
            from app.services.position_sizing import PositionSizer
            from app.services.risk_manager import RiskManager

            self.results["imports"] = "PASS"
            self.log("Critical imports: PASS")
            return True
        except Exception as e:
            self.results["imports"] = "FAIL"
            self.log(f"Critical imports: FAIL - {e}")
            return False

    async def test_pytrader_client(self):
        """Test PyTrader client initialization."""
        self.log("Testing PyTrader client...")
        try:
            from app.services.brokers.mt5_client import PyTraderClient

            # Test client creation
            client = PyTraderClient()

            # Test symbol lookup
            symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD']
            for symbol in symbols:
                broker_symbol = client.instrument_lookup.get(symbol, symbol)
                assert broker_symbol, f"Symbol lookup failed for {symbol}"

            client.close()
            self.results["pytrader_client"] = "PASS"
            self.log("PyTrader client: PASS")
            return True
        except Exception as e:
            self.results["pytrader_client"] = "FAIL"
            self.log(f"PyTrader client: FAIL - {e}")
            return False

    async def test_brain_service(self):
        """Test AI brain service."""
        self.log("Testing AI brain service...")
        try:
            from app.services.brain.brain import Brain

            brain = Brain()

            # Test basic functionality (without real API calls)
            test_data = {
                "symbol": "EURUSD",
                "candles": [
                    {"open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 1000}
                ] * 10,
                "current_price": 1.05,
                "indicators": {},
                "account_balance": 10000,
                "risk_percent": 2.0
            }

            # This should not raise an exception - use the correct method name
            result = await brain.decide(**test_data)

            self.results["brain_service"] = "PASS"
            self.log("AI brain service: PASS")
            return True
        except Exception as e:
            self.results["brain_service"] = "FAIL"
            self.log(f"AI brain service: FAIL - {e}")
            return False

    def start_backend(self):
        """Start the backend server."""
        self.log("Starting backend server...")
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "start_server.py"],
                cwd=os.path.join(os.path.dirname(__file__), 'backend'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            time.sleep(5)

            # Test if server is responding
            try:
                response = requests.get("http://localhost:8000/docs", timeout=5)
                if response.status_code == 200:
                    self.results["backend_startup"] = "PASS"
                    self.log("Backend server: PASS")
                    return True
                else:
                    self.results["backend_startup"] = "FAIL"
                    self.log(f"Backend server: FAIL - Status {response.status_code}")
                    return False
            except requests.exceptions.RequestException:
                self.results["backend_startup"] = "FAIL"
                self.log("Backend server: FAIL - No response")
                return False

        except Exception as e:
            self.results["backend_startup"] = "FAIL"
            self.log(f"Backend server: FAIL - {e}")
            return False

    async def test_api_endpoints(self):
        """Test API endpoints."""
        self.log("Testing API endpoints...")
        try:
            base_url = "http://localhost:8000"

            # Test health endpoint
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Health endpoint failed: {response.status_code}")

            # Test API docs
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Docs endpoint failed: {response.status_code}")

            # Test OpenAPI spec
            response = requests.get(f"{base_url}/openapi.json", timeout=5)
            if response.status_code != 200:
                raise Exception(f"OpenAPI endpoint failed: {response.status_code}")

            self.results["api_endpoints"] = "PASS"
            self.log("API endpoints: PASS")
            return True

        except Exception as e:
            self.results["api_endpoints"] = "FAIL"
            self.log(f"API endpoints: FAIL - {e}")
            return False

    def test_frontend_build(self):
        """Test frontend build."""
        self.log("Testing frontend build...")
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=os.path.join(os.path.dirname(__file__), 'frontend'),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.results["frontend_build"] = "PASS"
                self.log("Frontend build: PASS")
                return True
            else:
                self.results["frontend_build"] = "FAIL"
                self.log(f"Frontend build: FAIL - {result.stderr}")
                return False

        except Exception as e:
            self.results["frontend_build"] = "FAIL"
            self.log(f"Frontend build: FAIL - {e}")
            return False

    async def test_trading_bot_components(self):
        """Test trading bot components."""
        self.log("Testing trading bot components...")
        try:
            # Test position sizing
            from app.services.position_sizing import PositionSizer, RiskStrategy

            sizer = PositionSizer(account_balance=10000)  # Required parameter
            result = sizer.calculate_position_size(
                account_balance=10000,
                risk_percent=2.0,
                stop_loss_pips=50,
                symbol="EURUSD",
                strategy=RiskStrategy.FIXED_RISK
            )

            assert result["quantity"] > 0, "Position sizing failed"

            # Test risk manager
            from app.services.risk_manager import RiskManager, RiskLevel

            risk_manager = RiskManager()
            # Basic instantiation test
            assert risk_manager is not None, "Risk manager creation failed"

            self.results["trading_bot"] = "PASS"
            self.log("Trading bot components: PASS")
            return True

        except Exception as e:
            self.results["trading_bot"] = "FAIL"
            self.log(f"Trading bot components: FAIL - {e}")
            return False

    async def run_all_tests(self):
        """Run all system tests."""
        print("🚀 Starting Comprehensive System Test Suite")
        print("=" * 50)

        # Test components that don't require server
        await self.test_database()
        await self.test_imports()
        await self.test_pytrader_client()
        await self.test_brain_service()
        await self.test_trading_bot_components()

        # Test frontend build
        self.test_frontend_build()

        # Start backend and test API
        if self.start_backend():
            await self.test_api_endpoints()
        else:
            self.results["api_endpoints"] = "SKIP"

        # Print results
        self.print_results()

        # Cleanup
        self.cleanup()

    def print_results(self):
        """Print test results summary."""
        print("\n📊 Test Results Summary")
        print("=" * 30)

        total_tests = len(self.results)
        passed = sum(1 for result in self.results.values() if result == "PASS")
        failed = sum(1 for result in self.results.values() if result == "FAIL")
        skipped = sum(1 for result in self.results.values() if result == "SKIP")

        for test, result in self.results.items():
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "SKIP": "⏭️"
            }.get(result, "❓")
            print(f"  {status_icon} {test.replace('_', ' ').title()}: {result}")

        print(f"\n📈 Overall: {passed}/{total_tests} tests passed")
        if failed > 0:
            print(f"❌ Failed: {failed}")
        if skipped > 0:
            print(f"⏭️ Skipped: {skipped}")

        if passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        elif failed == 0:
            print("\n⚠️ Some tests were skipped but no failures. Check configuration.")
        else:
            print("\n❌ Some tests failed. Please fix issues before deployment.")

    def cleanup(self):
        """Clean up running processes."""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
            self.log("Backend server stopped")

        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
            self.log("Frontend server stopped")


async def main():
    """Main test runner."""
    tester = SystemTester()
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        tester.cleanup()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())