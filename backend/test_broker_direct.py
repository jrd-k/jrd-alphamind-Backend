#!/usr/bin/env python3
"""Direct test of broker account creation function."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import init_db, SessionLocal
from app.models.orm_models import User, BrokerAccount
from app.api.v1.broker_accounts import BrokerAccountCreate

# Initialize database
init_db()

# Get or create test user
db = SessionLocal()
user = db.query(User).filter(User.username == "testuser").first()
if not user:
    user = User(username="testuser", hashed_password="hashedpass")
    db.add(user)
    db.commit()
    db.refresh(user)

print(f"Using user: {user.username} (ID: {user.id})")

# Test the broker account creation logic directly
try:
    account_data = BrokerAccountCreate(
        broker_name="exness",
        account_id="exness123",
        api_key="exness_key",
        api_secret="exness_secret"
    )

    # Check if user already has an account for this broker
    existing = db.query(BrokerAccount).filter(
        BrokerAccount.user_id == user.id,
        BrokerAccount.broker_name == account_data.broker_name
    ).first()

    if existing:
        print(f"User already has a {account_data.broker_name} account")
    else:
        # Create new broker account
        broker_account = BrokerAccount(
            user_id=user.id,
            broker_name=account_data.broker_name,
            account_id=account_data.account_id,
            api_key=account_data.api_key,
            api_secret=account_data.api_secret,
            base_url=account_data.base_url,
            mt5_path=account_data.mt5_path,
            mt5_password=account_data.mt5_password,
            is_active=1
        )

        print(f"Creating broker account: {broker_account.broker_name}")
        db.add(broker_account)
        db.commit()
        db.refresh(broker_account)

        print("✓ Broker account created successfully!")
        print(f"ID: {broker_account.id}")
        print(f"Broker: {broker_account.broker_name}")
        print(f"Account ID: {broker_account.account_id}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

db.close()