import pytest
import hmac
import hashlib
import json

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.mark.parametrize("secret_set", [True, False])
def test_tradingview_webhook(secret_set, monkeypatch):
    client = TestClient(app)

    payload = {"action": "buy", "symbol": "EURUSD", "qty": 0.1}
    body = json.dumps(payload).encode()

    if secret_set:
        monkeypatch.setenv("CONFIRM_LIVE", "CONFIRM-LIVE")
        # Re-import settings to reflect env change if necessary
        sig = hmac.new("CONFIRM-LIVE".encode(), body, hashlib.sha256).hexdigest()
        headers = {"X-TradingView-Signature": sig}
    else:
        headers = {}

    resp = client.post("/api/v1/webhook/tradingview", data=body, headers=headers)
    assert resp.status_code == 200
    j = resp.json()
    assert "accepted" in j
