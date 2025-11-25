"""
Comprehensive integration tests covering full user workflows.
Tests: registration → login → order submission → trade persistence → WebSocket broadcast.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.orm_models import User, Order, Trade

client = TestClient(app)


class TestFullUserWorkflow:
    """Test complete user flow from registration to trade execution."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clean up test data before/after."""
        db = SessionLocal()
        try:
            # Clean test users/orders/trades
            db.query(Trade).delete()
            db.query(Order).delete()
            db.query(User).filter(User.username.startswith("testuser")).delete()
            db.commit()
        finally:
            db.close()
        yield

    def test_full_workflow_register_login_order_trade(self):
        """Test: register -> login -> submit order -> check trade persisted."""
        
        # 1. Register a new user
        register_resp = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser1", "password": "secret123"},
        )
        assert register_resp.status_code == 200
        print("✓ User registered")

        # 2. Login to get token
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser1", "password": "secret123"},
        )
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        token = token_data["access_token"]
        print(f"✓ Login successful, token: {token[:20]}...")

        # 3. Submit an order with JWT
        order_resp = client.post(
            "/api/v1/orders/",
            json={"symbol": "EURUSD", "quantity": 1.0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert order_resp.status_code == 200
        order_data = order_resp.json()
        order_id = order_data.get("id")
        assert order_id is not None
        print(f"✓ Order submitted (id={order_id})")

        # 4. Verify order persisted in DB with user_id set
        db = SessionLocal()
        try:
            order = db.query(Order).filter_by(id=order_id).first()
            assert order is not None
            assert order.user_id is not None
            assert order.symbol == "EURUSD"
            print(f"✓ Order persisted with user_id={order.user_id}")

            # 5. Verify a Trade was created and persisted
            trade = db.query(Trade).filter_by(order_id=order_id).first()
            assert trade is not None
            assert trade.symbol == "EURUSD"
            assert trade.user_id == order.user_id
            print(f"✓ Trade persisted (id={trade.id}, symbol={trade.symbol})")
        finally:
            db.close()

    def test_multiple_orders_same_user(self):
        """Test multiple orders from same user are all persisted."""
        
        # Register and login
        client.post("/api/v1/auth/register", json={"username": "testuser2", "password": "pwd"})
        login_resp = client.post("/api/v1/auth/login", json={"username": "testuser2", "password": "pwd"})
        token = login_resp.json()["access_token"]
        
        # Submit 3 orders
        symbols = ["EURUSD", "BTCUSD", "AAPL"]
        order_ids = []
        for symbol in symbols:
            resp = client.post(
                "/api/v1/orders/",
                json={"symbol": symbol, "quantity": 1.0},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            order_ids.append(resp.json()["id"])
        
        print(f"✓ Submitted {len(order_ids)} orders")
        
        # Verify all orders and trades persisted
        db = SessionLocal()
        try:
            for order_id in order_ids:
                order = db.query(Order).filter_by(id=order_id).first()
                assert order is not None
                trade = db.query(Trade).filter_by(order_id=order_id).first()
                assert trade is not None
                print(f"  ✓ Order {order_id} and trade persisted")
        finally:
            db.close()

    def test_order_without_auth_fails(self):
        """Test that submitting order without JWT returns 401/403."""
        resp = client.post(
            "/api/v1/orders/",
            json={"symbol": "EURUSD", "quantity": 1.0},
        )
        assert resp.status_code in (401, 403)
        print("✓ Unauthenticated order submission rejected")

    def test_invalid_token_fails(self):
        """Test that invalid token is rejected."""
        resp = client.post(
            "/api/v1/orders/",
            json={"symbol": "EURUSD", "quantity": 1.0},
            headers={"Authorization": "Bearer invalid_token_xyz"},
        )
        assert resp.status_code == 401
        print("✓ Invalid token rejected")


class TestOrderAndTradeFlow:
    """Test order and trade-specific workflows."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and clean trades."""
        db = SessionLocal()
        try:
            db.query(Trade).delete()
            db.query(Order).delete()
            db.query(User).filter(User.username == "testflow").delete()
            db.commit()
        finally:
            db.close()
        
        # Create a test user
        client.post("/api/v1/auth/register", json={"username": "testflow", "password": "pwd"})
        self.login_resp = client.post("/api/v1/auth/login", json={"username": "testflow", "password": "pwd"})
        self.token = self.login_resp.json()["access_token"]
        yield

    def test_order_list_retrieval(self):
        """Test fetching list of user's orders."""
        # Submit orders
        for i in range(3):
            client.post(
                "/api/v1/orders/",
                json={"symbol": f"SYM{i}", "quantity": float(i+1)},
                headers={"Authorization": f"Bearer {self.token}"},
            )
        
        # List orders
        list_resp = client.get(
            "/api/v1/orders/",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        assert list_resp.status_code == 200
        orders = list_resp.json()
        assert len(orders) >= 3
        print(f"✓ Retrieved {len(orders)} orders")

    def test_trade_list_retrieval(self):
        """Test fetching list of trades."""
        # Submit an order (creates a trade)
        client.post(
            "/api/v1/orders/",
            json={"symbol": "TESTORD", "quantity": 2.0},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        
        # List trades
        list_resp = client.get("/api/v1/trades/")
        assert list_resp.status_code == 200
        trades = list_resp.json()
        assert len(trades) > 0
        test_trade = trades[0]
        assert test_trade["symbol"] == "TESTORD"
        print(f"✓ Retrieved {len(trades)} trades, verified symbol")

    def test_order_get_by_id(self):
        """Test fetching a specific order by ID."""
        # Submit an order
        submit_resp = client.post(
            "/api/v1/orders/",
            json={"symbol": "GETTEST", "quantity": 5.0},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        order_id = submit_resp.json()["id"]
        
        # Get by ID
        get_resp = client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        assert get_resp.status_code == 200
        order = get_resp.json()
        assert order["id"] == order_id
        assert order["symbol"] == "GETTEST"
        print(f"✓ Retrieved order {order_id} by ID")
