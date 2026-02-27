#!/usr/bin/env python3
"""Test broker account API endpoint."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.orm_models import User
from app.core.security import create_access_token

# Get existing test user
db = SessionLocal()
user = db.query(User).filter(User.username == "testuser").first()
if not user:
    print("Test user not found")
    sys.exit(1)

# Create token
token = create_access_token(data={"sub": user.username})
print(f"Token for user {user.username}: {token}")

db.close()</content>
<parameter name="filePath">c:\Users\USER\jrd-alphamind-Backend\backend\get_token.py