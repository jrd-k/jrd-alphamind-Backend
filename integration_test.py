#!/usr/bin/env python3
"""
Comprehensive test script for AlphaMind frontend-backend integration
"""
import urllib.request
import json
import time
import sys

def test_backend():
    """Test backend API endpoints"""
    print("🔍 Testing Backend API...")

    tests = [
        ("http://localhost:8000/docs", "API Documentation", 200),
        ("http://localhost:8000/openapi.json", "OpenAPI Schema", 200),
        ("http://localhost:8000/api/stocks?symbol=AAPL", "Stocks API", 200),
        ("http://localhost:8000/api/user/me", "User Profile (no auth)", 401),
    ]

    passed = 0
    for url, desc, expected_status in tests:
        try:
            response = urllib.request.urlopen(url)
            if response.status == expected_status:
                print(f"  ✅ {desc}: {response.status}")
                passed += 1
            else:
                print(f"  ❌ {desc}: Expected {expected_status}, got {response.status}")
        except urllib.error.HTTPError as e:
            if e.code == expected_status:
                print(f"  ✅ {desc}: {e.code} (expected)")
                passed += 1
            else:
                print(f"  ❌ {desc}: Expected {expected_status}, got {e.code}")
        except Exception as e:
            print(f"  ❌ {desc}: Error - {str(e)[:50]}")

    return passed, len(tests)

def test_frontend():
    """Test frontend server"""
    print("🔍 Testing Frontend Server...")

    try:
        response = urllib.request.urlopen("http://localhost:8080")
        if response.status == 200:
            print("  ✅ Frontend Server: 200")
            return 1, 1
        else:
            print(f"  ❌ Frontend Server: {response.status}")
            return 0, 1
    except Exception as e:
        print(f"  ❌ Frontend Server: Error - {str(e)[:50]}")
        return 0, 1

def test_integration():
    """Test frontend-backend integration"""
    print("🔍 Testing Frontend-Backend Integration...")

    # Test CORS
    try:
        req = urllib.request.Request("http://localhost:8000/api/stocks?symbol=AAPL")
        req.add_header("Origin", "http://localhost:8080")
        response = urllib.request.urlopen(req)
        headers = dict(response.headers)

        cors_ok = "access-control-allow-origin" in headers
        if cors_ok:
            print("  ✅ CORS: Properly configured")
        else:
            print("  ❌ CORS: Missing headers")

        return 1 if cors_ok else 0, 1
    except Exception as e:
        print(f"  ❌ CORS Test: Error - {str(e)[:50]}")
        return 0, 1

def main():
    print("🚀 AlphaMind Integration Test Suite")
    print("=" * 50)

    # Don't start servers - assume they're already running
    total_passed = 0
    total_tests = 0

    # Test Backend
    backend_passed, backend_total = test_backend()
    total_passed += backend_passed
    total_tests += backend_total

    print()

    # Test Frontend
    frontend_passed, frontend_total = test_frontend()
    total_passed += frontend_passed
    total_tests += frontend_total

    print()

    # Test Integration
    integration_passed, integration_total = test_integration()
    total_passed += integration_passed
    total_tests += integration_total

    print()
    print("=" * 50)
    print(f"📊 Test Results: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("🎉 All tests passed! Frontend-backend integration is working perfectly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())