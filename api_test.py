#!/usr/bin/env python3
import urllib.request
import json

print('🔍 Testing API Integration...')

# Test stocks endpoint
try:
    req = urllib.request.Request('http://localhost:8000/api/stocks?symbol=AAPL')
    req.add_header('Origin', 'http://localhost:8080')
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    print(f'✅ Stocks API: {len(data.get("data", []))} records returned')
except Exception as e:
    print(f'❌ Stocks API Error: {str(e)[:50]}')

# Test CORS
try:
    req = urllib.request.Request('http://localhost:8000/api/stocks?symbol=AAPL')
    req.add_header('Origin', 'http://localhost:8080')
    response = urllib.request.urlopen(req)
    headers = dict(response.headers)
    has_cors = 'access-control-allow-origin' in headers
    print(f'✅ CORS: {"Working" if has_cors else "Missing"}')
except Exception as e:
    print(f'❌ CORS Error: {str(e)[:50]}')

print('🎉 API Integration test complete!')