#!/usr/bin/env python3
"""Test paper trade creation."""

import urllib.request
import json

print('Testing Paper Trade Creation')
print('=' * 30)

# Check if server is running
try:
    response = urllib.request.urlopen('http://localhost:8001/docs', timeout=5)
    print('✓ Backend running')
except Exception as e:
    print(f'✗ Backend not running: {str(e)[:50]}')
    exit(1)

# Test paper trade creation (without auth for now)
try:
    data = json.dumps({
        'symbol': 'EURUSD',
        'side': 'buy',
        'price': 1.0850,
        'qty': 0.01
    }).encode('utf-8')

    req = urllib.request.Request(
        'http://localhost:8001/api/v1/trades/paper',
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    response = urllib.request.urlopen(req, timeout=10)
    result = json.loads(response.read().decode('utf-8'))
    print('✓ Paper trade created successfully!')
    print(f'  Trade ID: {result.get("id")}')
    print(f'  Symbol: {result.get("symbol")}')
    print(f'  Side: {result.get("side")}')
    print(f'  Quantity: {result.get("qty")}')

except Exception as e:
    print(f'✗ Paper trade creation failed: {str(e)}')
    if hasattr(e, 'read'):
        try:
            error_details = e.read().decode('utf-8')
            print(f'  Error details: {error_details}')
        except:
            pass