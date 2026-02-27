#!/usr/bin/env python3
"""Comprehensive test of broker account API."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import create_app
from app.core.database import init_db

# Initialize database
init_db()

# Create test client
app = create_app()
client = TestClient(app)

# Test 1: Register user
print("Testing user registration...")
response = client.post("/api/v1/auth/register", json={
    "username": "testuser2",
    "password": "testpass123"
})
print(f"Register response: {response.status_code}")
if response.status_code == 200:
    print("✓ User registered successfully")
else:
    print(f"✗ Registration failed: {response.text}")

# Test 2: Login
print("\nTesting login...")
response = client.post("/api/v1/auth/login", json={
    "username": "testuser2",
    "password": "testpass123"
})
print(f"Login response: {response.status_code}")
if response.status_code == 200:
    token = response.json()["access_token"]
    print("✓ Login successful, got token")
    headers = {"Authorization": f"Bearer {token}"}

    # Test 3: Create broker account
    print("\nTesting broker account creation...")
    response = client.post("/api/v1/brokers/accounts", json={
        "broker_name": "paper",
        "account_id": "test123",
        "api_key": "test_key",
        "api_secret": "test_secret"
    }, headers=headers)
    print(f"Broker account creation response: {response.status_code}")
    if response.status_code == 200:
        print("✓ Broker account created successfully!")
        print(f"Response: {response.json()}")
    else:
        print(f"✗ Broker account creation failed: {response.text}")

    # Test 4: Get broker accounts
    print("\nTesting get broker accounts...")
    response = client.get("/api/v1/brokers/accounts", headers=headers)
    print(f"Get broker accounts response: {response.status_code}")
    if response.status_code == 200:
        print("✓ Broker accounts retrieved successfully!")
        print(f"Response: {response.json()}")
    else:
        print(f"✗ Get broker accounts failed: {response.text}")

else:
    print(f"✗ Login failed: {response.text}")

print("\nTest completed!")