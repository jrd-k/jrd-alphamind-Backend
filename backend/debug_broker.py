import sys
sys.path.insert(0, '.')
from app.core.database import init_db, engine
from app.models.orm_models import BrokerAccount, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Initialize DB
init_db()

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check if table exists
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='broker_accounts'"))
    if result.fetchone():
        print("broker_accounts table exists")
    else:
        print("broker_accounts table does NOT exist")

    # Get existing user or create new one
    user = db.query(User).filter(User.username == "testuser7@example.com").first()
    if not user:
        user = User(username="testuser7@example.com", hashed_password="test")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user: {user.id}")
    else:
        print(f"Using existing user: {user.id}")

    # Try to create a test broker account
    broker_account = BrokerAccount(
        user_id=user.id,
        broker_name="paper",
        account_id="123456",
        is_active=1
    )

    db.add(broker_account)
    db.commit()
    db.refresh(broker_account)

    print(f"Successfully created broker account: {broker_account.id}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()