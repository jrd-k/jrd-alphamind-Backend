from fastapi.testclient import TestClient
from app.main import app
from app.core import config
from datetime import datetime, timedelta, timezone

client = TestClient(app)


def _make_candles(n=30, start_price=100.0):
    candles = []
    t = datetime.now(timezone.utc)
    p = float(start_price)
    for i in range(n):
        o = p
        h = p * 1.001
        l = p * 0.999
        c = p * (1.0005)
        v = 100 + i
        candles.append({
            "t": (t + timedelta(minutes=i)).isoformat(),
            "o": o,
            "h": h,
            "l": l,
            "c": c,
            "v": v,
        })
        p = c
    return candles

payload = {"ind": {"symbol": "TEST", "source": "supertrend_ai", "signal": True, "value": {}}, "candles": _make_candles(30)}

config.settings.indicator_api_key = ""
resp = client.post("/api/v1/indicators/compute", json=payload)
print('status', resp.status_code)
try:
    print(resp.json())
except Exception as e:
    print('no json', e)
