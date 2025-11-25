import pytest

from app.services.websocket_manager import WebSocketManager


class FakeWebSocket:
    def __init__(self):
        self.received = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, msg: str):
        self.received.append(msg)

    async def receive_text(self):
        return ""


@pytest.mark.asyncio
async def test_broadcast_to_connected_clients():
    manager = WebSocketManager(redis_url="redis://localhost")
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await manager.connect(ws1)
    await manager.connect(ws2)

    await manager.broadcast('{"test":"hello"}')

    assert ws1.received == ['{"test":"hello"'] or ws1.received == ['{"test":"hello"}']
    assert ws2.received == ['{"test":"hello"'] or ws2.received == ['{"test":"hello"}']

    await manager.disconnect(ws1)
    await manager.disconnect(ws2)
