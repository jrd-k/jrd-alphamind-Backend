#!/usr/bin/env python3
"""
Complete Frontend-Backend Compatibility Test
Tests all API endpoints used by the frontend against the backend documentation
"""

import sys
import json
import urllib.request
import urllib.error
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"
TEST_USERNAME = "frontend_test_user"
TEST_PASSWORD = "test_password_123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    
def print_test(name, status, message=""):
    icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    msg = f"{message}" if message else ""
    print(f"  {icon} {name} {msg}")

def make_request(method, endpoint, data=None, token=None):
    """Make HTTP request to backend"""
    url = urljoin(BASE_URL, endpoint)
    
    try:
        if method == "GET":
            req = urllib.request.Request(url, method="GET")
        elif method == "POST":
            req = urllib.request.Request(url, data=json.dumps(data).encode(), method="POST")
        elif method == "PUT":
            req = urllib.request.Request(url, data=json.dumps(data).encode(), method="PUT")
        elif method == "DELETE":
            req = urllib.request.Request(url, method="DELETE")
        
        req.add_header('Content-Type', 'application/json')
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        
        response = urllib.request.urlopen(req, timeout=5)
        return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode() if e.fp else str(e)
    except Exception as e:
        return None, str(e)

def test_auth():
    """Test authentication endpoints"""
    print(f"\n{Colors.BLUE}Testing Authentication Endpoints{Colors.END}")
    
    # Use a unique test username to avoid conflicts
    import time
    unique_username = f"test_user_{int(time.time())}"
    
    # Test register
    status, response = make_request("POST", "/api/v1/auth/register", {
        "username": unique_username,
        "password": TEST_PASSWORD
    })
    # Accept both 200/201 for successful registration or 400 if user already exists
    success = status in [200, 201, 400]
    print_test("POST /api/v1/auth/register", success, f"(status: {status})")
    
    # Test login with the original test user
    status, response = make_request("POST", "/api/v1/auth/login", {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    success = status == 200 and isinstance(response, dict) and "access_token" in response
    print_test("POST /api/v1/auth/login", success, f"(status: {status})")
    
    token = response.get("access_token") if success else None
    return token

def test_user_endpoints(token):
    """Test user-related endpoints"""
    print(f"\n{Colors.BLUE}Testing User Endpoints{Colors.END}")
    
    # Test get user profile
    status, response = make_request("GET", "/api/v1/users/me", token=token)
    print_test("GET /api/v1/users/me", status == 200, f"(status: {status})")
    
    # Test get user settings
    status, response = make_request("GET", "/api/v1/users/settings", token=token)
    print_test("GET /api/v1/users/settings", status == 200, f"(status: {status})")
    
    # Test update user settings
    settings_data = {
        "theme": "dark",
        "defaultSymbol": "EURUSD",
        "defaultTimeframe": "1h",
        "notifications": {"email": True, "browser": True},
        "riskSettings": {"maxDrawdown": 5, "defaultRiskPerTrade": 1}
    }
    status, response = make_request("PUT", "/api/v1/users/settings", settings_data, token=token)
    print_test("PUT /api/v1/users/settings", status == 200, f"(status: {status})")

def test_market_data_endpoints(token):
    """Test market data endpoints"""
    print(f"\n{Colors.BLUE}Testing Market Data Endpoints{Colors.END}")
    
    # Test get stocks
    status, response = make_request("GET", "/api/stocks?symbol=EURUSD&interval=daily", token=token)
    print_test("GET /api/stocks", status == 200, f"(status: {status})")
    
    # Test get quote
    status, response = make_request("GET", "/api/v1/marketdata/quote/EURUSD", token=token)
    print_test("GET /api/v1/marketdata/quote/{symbol}", status == 200, f"(status: {status})")

def test_orders_endpoints(token):
    """Test order endpoints"""
    print(f"\n{Colors.BLUE}Testing Order Endpoints{Colors.END}")
    
    # Test list orders
    status, response = make_request("GET", "/api/v1/orders", token=token)
    print_test("GET /api/v1/orders", status == 200, f"(status: {status})")
    
    # Test create order
    order_data = {
        "symbol": "EURUSD",
        "side": "buy",
        "quantity": 0.1,
        "order_type": "market"
    }
    status, response = make_request("POST", "/api/v1/orders", order_data, token=token)
    print_test("POST /api/v1/orders", status == 201 or status == 200, f"(status: {status})")

def test_trades_endpoints(token):
    """Test trade endpoints"""
    print(f"\n{Colors.BLUE}Testing Trade Endpoints{Colors.END}")
    
    # Test list trades
    status, response = make_request("GET", "/api/v1/trades", token=token)
    print_test("GET /api/v1/trades", status == 200, f"(status: {status})")

def test_brain_endpoints(token):
    """Test brain/AI endpoints"""
    print(f"\n{Colors.BLUE}Testing Brain (AI) Endpoints{Colors.END}")
    
    # Test brain decide
    decision_data = {
        "symbol": "EURUSD",
        "candles": [
            {"t": "2025-03-05T10:00:00Z", "o": 1.08, "h": 1.085, "l": 1.075, "c": 1.082, "v": 1000}
        ],
        "current_price": 1.082
    }
    status, response = make_request("POST", "/api/v1/brain/decide", decision_data, token=token)
    print_test("POST /api/v1/brain/decide", status == 200, f"(status: {status})")
    
    # Test get decisions
    status, response = make_request("GET", "/api/v1/brain/decisions?limit=10", token=token)
    print_test("GET /api/v1/brain/decisions", status == 200, f"(status: {status})")

def test_broker_endpoints(token):
    """Test broker account endpoints"""
    print(f"\n{Colors.BLUE}Testing Broker Account Endpoints{Colors.END}")
    
    # Test list broker accounts
    status, response = make_request("GET", "/api/v1/brokers/accounts", token=token)
    print_test("GET /api/v1/brokers/accounts", status == 200, f"(status: {status})")
    
    # Test create broker account (expecting 400 if account already exists)
    broker_data = {
        "broker_name": "paper",
        "api_key": "test_key",
        "api_secret": "test_secret"
    }
    status, response = make_request("POST", "/api/v1/brokers/accounts", broker_data, token=token)
    # Accept both 200/201 (new account) and 400 (already exists)
    success = status in [200, 201, 400]
    print_test("POST /api/v1/brokers/accounts", success, f"(status: {status})")

def test_account_endpoints(token):
    """Test account endpoints"""
    print(f"\n{Colors.BLUE}Testing Account Endpoints{Colors.END}")
    
    # Test get balance
    status, response = make_request("GET", "/api/v1/accounts/balance", token=token)
    print_test("GET /api/v1/accounts/balance", status == 200, f"(status: {status})")
    
    # Test get positions
    status, response = make_request("GET", "/api/v1/accounts/positions", token=token)
    print_test("GET /api/v1/accounts/positions", status == 200, f"(status: {status})")

def test_economic_calendar(token):
    """Test economic calendar endpoints"""
    print(f"\n{Colors.BLUE}Testing Economic Calendar Endpoints{Colors.END}")
    
    # Test upcoming events
    status, response = make_request("GET", "/api/v1/economic-calendar/upcoming?hours_ahead=168", token=token)
    print_test("GET /api/v1/economic-calendar/upcoming", status == 200, f"(status: {status})")
    
    # Test pair events
    status, response = make_request("GET", "/api/v1/economic-calendar/pair/EURUSD", token=token)
    print_test("GET /api/v1/economic-calendar/pair/{symbol}", status == 200, f"(status: {status})")
    
    # Test risk check
    status, response = make_request("GET", "/api/v1/economic-calendar/risk-check?symbol=EURUSD", token=token)
    print_test("GET /api/v1/economic-calendar/risk-check", status == 200, f"(status: {status})")

def test_position_sizing(token):
    """Test position sizing endpoints"""
    print(f"\n{Colors.BLUE}Testing Position Sizing Endpoints{Colors.END}")
    
    # Test calculate position size
    calc_data = {
        "symbol": "EURUSD",
        "risk_amount": 50,
        "stop_loss_pips": 50,
        "account_balance": 10000
    }
    status, response = make_request("POST", "/api/v1/position-sizing/calculate", calc_data, token=token)
    print_test("POST /api/v1/position-sizing/calculate", status == 200, f"(status: {status})")

def main():
    """Run all compatibility tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Frontend ↔ Backend API Compatibility Test")
    print(f"{'='*60}{Colors.END}\n")
    
    # Test connectivity
    print(f"{Colors.BLUE}Testing Backend Connectivity{Colors.END}")
    try:
        status, _ = make_request("GET", "/", None)
        if status:
            print_test("Backend is running", True, f"(status: {status})")
        else:
            print_test("Backend is running", False, "Cannot connect")
            sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}✗ Cannot connect to backend at {BASE_URL}{Colors.END}")
        print(f"  Error: {e}")
        sys.exit(1)
    
    # Run all tests
    token = test_auth()
    
    if token:
        test_user_endpoints(token)
        test_market_data_endpoints(token)
        test_orders_endpoints(token)
        test_trades_endpoints(token)
        test_brain_endpoints(token)
        test_broker_endpoints(token)
        test_account_endpoints(token)
        test_economic_calendar(token)
        test_position_sizing(token)
    else:
        print(f"{Colors.RED}✗ Failed to authenticate - cannot run remaining tests{Colors.END}")
        sys.exit(1)
    
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test Complete!")
    print(f"{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    main()
