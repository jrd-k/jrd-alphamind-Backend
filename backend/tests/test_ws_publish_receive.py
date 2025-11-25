import asyncio
from contextlib import asynccontextmanager
import pytest

from starlette.testclient import TestClient
from app.main import app
from app.services.websocket_manager import get_ws_manager
from app.core.config import settings


@pytest.mark.parametrize("msg_bytes", [
    b'{"id":1,"symbol":"EURUSD","side":"buy","price":1.2345,"qty":0.1,"timestamp":"2025-11-17T12:00:00Z","order_id":"1","user_id":1,"metadata":{}}'
])
def test_ws_receives_published_message(monkeypatch, msg_bytes):
    manager = get_ws_manager(settings.redis_url)

    # create an asynccontextmanager that ignores the channel and yields a pubsub
    @asynccontextmanager
    async def fake_subscribe(channel: str):
        class FakePubSub:
            async def listen(self):
                yield {"type": "message", "data": msg_bytes}

        yield FakePubSub()

    # patch the manager's subscribe method
    monkeypatch.setattr(manager, "subscribe", fake_subscribe)

    # use TestClient to connect to the websocket endpoint
    with TestClient(app) as client:
        with client.websocket_connect("/ws/trades") as ws:
            data = ws.receive_text()
            assert "EURUSD" in data
            assert '"price":1.2345' in data
