#!/usr/bin/env python3
"""
AlphaMind App Testing Suite
Comprehensive testing of frontend-backend integration
"""
import urllib.request
import json
import sys

def test_backend_server():
    """Test backend server availability"""
    print("1. Testing Backend Server...")
    try:
        response = urllib.request.urlopen('http://localhost:8000/docs')
        return True, f"✅ Backend API Docs: {response.status}"
    except Exception as e:
        return False, f"❌ Backend API Docs: Error - {str(e)[:50]}"

def test_frontend_server():
    """Test frontend server availability"""
    print("2. Testing Frontend Server...")
    try:
        response = urllib.request.urlopen('http://localhost:8080')
        return True, f"✅ Frontend Server: {response.status}"
    except Exception as e:
        return False, f"❌ Frontend Server: Error - {str(e)[:50]}"

def test_api_endpoints():
    """Test key API endpoints"""
    print("3. Testing API Endpoints...")
    results = []

    endpoints = [
        ('http://localhost:8000/openapi.json', 'OpenAPI Schema', 200),
        ('http://localhost:8000/api/stocks?symbol=AAPL', 'Stocks API', 200),
        ('http://localhost:8000/api/user/me', 'User Profile', 401),  # Expected 401
    ]

    for url, desc, expected_status in endpoints:
        try:
            response = urllib.request.urlopen(url)
            status = response.status
            if status == expected_status:
                results.append((True, f"✅ {desc}: {status}"))
            else:
                results.append((False, f"⚠️  {desc}: {status} (expected {expected_status})"))
        except urllib.error.HTTPError as e:
            if e.code == expected_status:
                results.append((True, f"✅ {desc}: {e.code} (expected)"))
            else:
                results.append((False, f"❌ {desc}: {e.code}"))
        except Exception as e:
            results.append((False, f"❌ {desc}: Error - {str(e)[:50]}"))

    return results

def test_cors_integration():
    """Test CORS headers"""
    print("4. Testing CORS Integration...")
    try:
        req = urllib.request.Request('http://localhost:8000/api/stocks?symbol=AAPL')
        req.add_header('Origin', 'http://localhost:8080')
        response = urllib.request.urlopen(req)
        headers = dict(response.headers)
        has_cors = 'access-control-allow-origin' in headers
        return has_cors, f"✅ CORS: {'Working' if has_cors else 'Missing'}"
    except Exception as e:
        return False, f"❌ CORS: Error - {str(e)[:50]}"

def test_data_format():
    """Test data structure and format"""
    print("5. Testing Data Format...")
    try:
        req = urllib.request.Request('http://localhost:8000/api/stocks?symbol=AAPL')
        req.add_header('Origin', 'http://localhost:8080')
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())

        if 'data' in data and len(data['data']) > 0:
            sample = data['data'][0]
            required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
            has_fields = all(field in sample for field in required_fields)
            record_count = len(data['data'])
            return has_fields, f"✅ Data Format: {record_count} records, {'all fields present' if has_fields else 'missing fields'}"
        else:
            return False, "❌ Data Format: No data returned"
    except Exception as e:
        return False, f"❌ Data Format: Error - {str(e)[:50]}"

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("6. Testing Authentication...")
    try:
        # Test login endpoint (should accept POST but return error for invalid data)
        req = urllib.request.Request('http://localhost:8000/api/auth/login', method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Origin', 'http://localhost:8080')
        test_data = json.dumps({'username': 'test@example.com', 'password': 'test123'}).encode()
        response = urllib.request.urlopen(req, test_data)
        return True, "✅ Auth Login: Endpoint responding"
    except urllib.error.HTTPError as e:
        if e.code == 401:  # Unauthorized is expected for non-existent user
            return True, "✅ Auth Login: Properly rejecting invalid credentials"
        else:
            return False, f"❌ Auth Login: Unexpected error {e.code}"
    except Exception as e:
        return False, f"❌ Auth Login: Error - {str(e)[:50]}"

def main():
    print("🚀 AlphaMind App Testing Suite")
    print("=" * 50)

    all_passed = True
    total_tests = 0

    # Test backend server
    success, message = test_backend_server()
    print(f"   {message}")
    if not success:
        all_passed = False
    total_tests += 1

    # Test frontend server
    success, message = test_frontend_server()
    print(f"   {message}")
    if not success:
        all_passed = False
    total_tests += 1

    # Test API endpoints
    api_results = test_api_endpoints()
    for success, message in api_results:
        print(f"   {message}")
        if not success:
            all_passed = False
        total_tests += 1

    # Test CORS
    success, message = test_cors_integration()
    print(f"   {message}")
    if not success:
        all_passed = False
    total_tests += 1

    # Test data format
    success, message = test_data_format()
    print(f"   {message}")
    if not success:
        all_passed = False
    total_tests += 1

    # Test auth
    success, message = test_auth_endpoints()
    print(f"   {message}")
    if not success:
        all_passed = False
    total_tests += 1

    print("\n" + "=" * 50)

    if all_passed:
        print(f"🎉 ALL TESTS PASSED! ({total_tests}/{total_tests})")
        print("✅ AlphaMind app is fully functional!")
        print("🌐 Frontend: http://localhost:8080")
        print("🔧 Backend API: http://localhost:8000/docs")
        return 0
    else:
        print(f"⚠️  SOME TESTS FAILED - Check output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())