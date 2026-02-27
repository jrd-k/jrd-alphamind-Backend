#!/usr/bin/env python3
"""Test broker account creation."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import init_db
from app.models.orm_models import BrokerAccount, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Initialize database
init_db()

# Create test user and broker account
engine = create_engine("sqlite:///./dev.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# Create test user
test_user = User(username="testuser", hashed_password="hashedpass")
db.add(test_user)
db.commit()

# Create broker account
broker_account = BrokerAccount(
    user_id=test_user.id,
    broker_name="paper",
    account_id="test123",
    api_key="test_key",
    api_secret="test_secret"
)
db.add(broker_account)
db.commit()

print("Test broker account created successfully!")
print(f"User ID: {test_user.id}")
print(f"Broker Account ID: {broker_account.id}")

db.close()