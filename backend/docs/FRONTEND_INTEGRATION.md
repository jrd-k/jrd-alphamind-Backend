# Frontend Integration Guide

This guide shows how to integrate the frontend app with the jrd-alphamind-backend API.

## Backend URL

The backend API is served at:

```
http://localhost:8000       (local development)
https://api.example.com     (production — update as needed)
```

## Prerequisites

1. Backend running (see `../README.md` for setup)
2. Frontend app (e.g., React, Next.js, Vue.js)
3. Node.js + npm/yarn

## Setup

### 1. Frontend Environment Variables

Create a `.env` file in your frontend repository with:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
# Or for production:
# VITE_API_BASE_URL=https://api.example.com/api/v1
```

(Replace `VITE_` prefix with your framework's convention — e.g., `REACT_APP_` for Create React App.)

### 2. Allowed Origins

The backend allows CORS requests from:

- `http://localhost:3000` (default React/Next.js)
- `http://localhost:5173` (default Vite)

To allow other origins, update the backend `.env`:

```env
FRONTEND_ORIGINS=http://localhost:3000,http://localhost:5173,https://myapp.com
```

Then restart the backend.

## API Usage

### Authentication Flow

#### 1. Register a User

```javascript
const response = await fetch(`${process.env.VITE_API_BASE_URL}/auth/register`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "alice", password: "secret123" })
});
const data = await response.json();
// → { "id": 1, "username": "alice" }
```

#### 2. Login (Get JWT Token)

```javascript
const response = await fetch(`${process.env.VITE_API_BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "alice", password: "secret123" })
});
const { access_token } = await response.json();
// → { "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "token_type": "bearer" }

// Store token (e.g., localStorage, sessionStorage, or a cookie)
localStorage.setItem("jwtToken", access_token);
```

#### 3. Use Token in Subsequent Requests

```javascript
const token = localStorage.getItem("jwtToken");

const response = await fetch(`${process.env.VITE_API_BASE_URL}/brain/decisions`, {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
});
const data = await response.json();
```

### Brain Decisions API

#### Compute a Decision

```javascript
const token = localStorage.getItem("jwtToken");

const payload = {
  symbol: "EURUSD",
  candles: [
    { t: "2025-11-24T10:00:00Z", o: 1.08, h: 1.085, l: 1.075, c: 1.08, v: 1000 },
    { t: "2025-11-24T10:01:00Z", o: 1.08, h: 1.086, l: 1.076, c: 1.082, v: 1100 },
    // ... more candles
  ],
  current_price: 1.082
};

const response = await fetch(`${process.env.VITE_API_BASE_URL}/brain/decide`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
});

const decision = await response.json();
console.log(decision);
// → {
//   "symbol": "EURUSD",
//   "decision": "BUY",
//   "indicator": { "summary": "...", "signals": "STRONG BUY" },
//   "deepseek": null,
//   "openai": null,
//   "timestamp": "2025-11-24T10:05:00Z"
// }
```

#### List Brain Decisions (DB-backed)

```javascript
const token = localStorage.getItem("jwtToken");

// List all decisions for a symbol
const response = await fetch(
  `${process.env.VITE_API_BASE_URL}/brain/decisions?symbol=EURUSD&limit=50&offset=0`,
  {
    method: "GET",
    headers: { "Authorization": `Bearer ${token}` }
  }
);

const data = await response.json();
console.log(data);
// → {
//   "total": 42,
//   "count": 50,
//   "items": [
//     { "id": 1, "symbol": "EURUSD", "decision": "BUY", ... },
//     ...
//   ]
// }
```

#### Filter by Timestamp

```javascript
const since = new Date("2025-11-24T00:00:00Z").toISOString();

const response = await fetch(
  `${process.env.VITE_API_BASE_URL}/brain/decisions?symbol=EURUSD&since=${encodeURIComponent(since)}&limit=50`,
  {
    method: "GET",
    headers: { "Authorization": `Bearer ${token}` }
  }
);
const data = await response.json();
```

### Other Endpoints

#### List Instruments (Trading Pairs)

```javascript
const response = await fetch(`${process.env.VITE_API_BASE_URL}/instruments`, {
  method: "GET"
});
const instruments = await response.json();
// → [{ "id": 1, "symbol": "EURUSD", "name": "EUR / USD" }, ...]
```

#### Submit an Order

```javascript
const token = localStorage.getItem("jwtToken");

const response = await fetch(`${process.env.VITE_API_BASE_URL}/orders`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    symbol: "EURUSD",
    quantity: 0.1
  })
});
const order = await response.json();
// → { "id": 1, "user_id": 1, "symbol": "EURUSD", "quantity": 0.1, "status": "new" }
```

#### List Trades

```javascript
const token = localStorage.getItem("jwtToken");

const response = await fetch(`${process.env.VITE_API_BASE_URL}/trades?limit=50`, {
  method: "GET",
  headers: { "Authorization": `Bearer ${token}` }
});
const trades = await response.json();
// → [{ "id": 1, "symbol": "EURUSD", "side": "buy", "price": 1.08, ... }, ...]
```

### WebSocket: Real-time Trades

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/trades");

ws.onopen = () => {
  console.log("Connected to trades stream");
};

ws.onmessage = (event) => {
  const trade = JSON.parse(event.data);
  console.log("New trade:", trade);
  // → { "id": 1, "symbol": "EURUSD", "side": "buy", "price": 1.08, ... }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from trades stream");
};
```

## Example: React Integration

```javascript
// useAuth.js — manage JWT token
import { useState, useEffect } from "react";

export const useAuth = () => {
  const [token, setToken] = useState(() => localStorage.getItem("jwtToken"));

  const login = async (username, password) => {
    const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const { access_token } = await response.json();
    localStorage.setItem("jwtToken", access_token);
    setToken(access_token);
  };

  const logout = () => {
    localStorage.removeItem("jwtToken");
    setToken(null);
  };

  return { token, login, logout };
};

// useBrainDecisions.js — fetch decisions
import { useState, useEffect } from "react";

export const useBrainDecisions = (symbol, token) => {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token || !symbol) return;

    setLoading(true);
    fetch(
      `${process.env.REACT_APP_API_BASE_URL}/brain/decisions?symbol=${symbol}&limit=50`,
      {
        headers: { "Authorization": `Bearer ${token}` }
      }
    )
      .then((res) => res.json())
      .then((data) => setDecisions(data.items))
      .finally(() => setLoading(false));
  }, [symbol, token]);

  return { decisions, loading };
};

// Dashboard.jsx — use the hooks
import { useAuth } from "./useAuth";
import { useBrainDecisions } from "./useBrainDecisions";

export const Dashboard = () => {
  const { token, login, logout } = useAuth();
  const [symbol, setSymbol] = useState("EURUSD");
  const { decisions, loading } = useBrainDecisions(symbol, token);

  if (!token) {
    return <LoginForm onLogin={login} />;
  }

  return (
    <div>
      <h1>Brain Decisions for {symbol}</h1>
      {loading ? <p>Loading...</p> : null}
      <ul>
        {decisions.map((d) => (
          <li key={d.id}>
            {d.timestamp}: {d.decision}
          </li>
        ))}
      </ul>
      <button onClick={logout}>Logout</button>
    </div>
  );
};
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200` — Success
- `400` — Bad request (invalid payload)
- `401` — Unauthorized (missing or invalid token)
- `403` — Forbidden (user not allowed)
- `404` — Not found
- `500` — Server error

Example error response:

```json
{
  "detail": "Could not validate credentials"
}
```

## Debugging

### Enable CORS Logging

If you see CORS errors in the browser console, check:

1. **Frontend origin** is in `FRONTEND_ORIGINS` env var on the backend.
2. **Preflight request** is allowed (browser sends `OPTIONS` before `POST/GET`).
3. **Credentials** — if using cookies, include `credentials: "include"` in fetch calls.

Example with credentials:

```javascript
const response = await fetch(url, {
  method: "GET",
  credentials: "include",  // Send cookies if any
  headers: { "Authorization": `Bearer ${token}` }
});
```

### Check Backend Logs

```bash
cd backend
docker-compose logs -f web
```

Look for CORS errors or validation failures.

## Next Steps

1. Clone the frontend repo: `https://github.com/jrd-k/jrd-alphamind`
2. Update its `.env` to point to this backend
3. Implement the integration examples above
4. Test in a browser and check network requests

## Questions?

See the backend `README.md` for more API details or open an issue in the frontend repo.

