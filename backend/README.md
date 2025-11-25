# jrd-alphamind-backend

A production-ready FastAPI trading backend with support for multiple broker integrations (Exness, JustMarkets, Paper Trading), JWT authentication, order management, and trade persistence.

## Features

- ✅ **User Authentication** — JWT-based register/login
- ✅ **Instruments** — Fetch available trading pairs
- ✅ **Orders** — Submit, list, retrieve order status
- ✅ **Trades** — Persistent trade history
- ✅ **Account Management** — Check balance, open positions
- ✅ **Broker Integration** — Pluggable broker clients (Exness, JustMarkets, Paper Trading)
- ✅ **Real-time WebSocket** — Stream trades live via `/ws/trades` + Redis pub/sub
- ✅ **Docker** — Full Docker Compose setup with Postgres + Redis

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local dev)

### 2. Clone and setup

```bash
cd backend/
cp .env.example .env
# Edit .env if needed (defaults are fine for dev with paper trading)
```

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

This starts:
- **FastAPI app** on http://127.0.0.1:8000
- **Postgres** on localhost:5432
- **Redis** on localhost:6379

### 4. Access interactive docs

Open http://127.0.0.1:8000/docs (Swagger UI)

## API Endpoints

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}'

# Login (get JWT token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Instruments

```bash
# List available trading pairs
curl http://localhost:8000/api/v1/instruments
```

### Orders

```bash
# Submit order (simulated execution or real broker order)
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","quantity":0.1}'

# List orders
curl http://localhost:8000/api/v1/orders

# Get specific order
curl http://localhost:8000/api/v1/orders/1
```

### Trades

```bash
# List all trades
curl http://localhost:8000/api/v1/trades

# Filter by symbol
curl "http://localhost:8000/api/v1/trades?symbol=EURUSD&limit=50"
```

### Account

```bash
# Check balance
curl http://localhost:8000/api/v1/accounts/balance

# Get open positions
curl http://localhost:8000/api/v1/accounts/positions
```

## WebSocket: Real-time Trade Streaming

### Connect to the trades stream

```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8000/ws/trades

# Or using websocat (Rust alternative)
websocat ws://localhost:8000/ws/trades
```

### Receive trade updates

When an order is executed, a trade message is published to Redis and broadcast to all connected WebSocket clients:

```json
{
  "id": 123,
  "symbol": "EURUSD",
  "side": "buy",
  "price": 1.0812,
  "qty": 0.1,
  "timestamp": "2025-11-17T10:05:00Z",
  "order_id": "order_123",
  "user_id": 1,
  "metadata": {}
}
```

### Test with the HTML client

1. Open the browser
2. Open `ws_trades_client.html` from the `backend/` folder (or serve it locally)
3. Click "Connect"
4. Submit an order via API or the Swagger UI
5. Watch the trade appear in real-time on the WebSocket client

### Example: Full end-to-end flow

```bash
# Terminal 1: Start backend
docker-compose up --build

# Terminal 2: Connect WebSocket client
wscat -c ws://localhost:8000/ws/trades

# Terminal 3: Register and submit an order
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | jq -r '.access_token')

curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","quantity":0.1}'

# Watch Terminal 2 — you should see the trade appear in real-time!
```

## Broker Configuration

### Paper Trading (Default)

Safest for testing. Simulates fills at random prices.

```bash
# .env
BROKER=paper
```

No credentials needed. Run locally or in Docker.

### Exness Integration

Real broker connections (demo or live).

1. Get API credentials from [Exness Dashboard](https://exness.com)
2. Update `.env`:

```
BROKER=exness
EXNESS_API_KEY=your_api_key
EXNESS_BASE_URL=https://api.exness-demo.com  # or live URL
```

3. Restart: `docker-compose restart web`

### JustMarkets Integration

(Stub implementation — follow same pattern as ExnessClient)

```
BROKER=justmarkets
JUSTMARKETS_API_KEY=your_api_key
JUSTMARKETS_BASE_URL=https://api.justmarkets-demo.com
```

## Local Development

### Setup virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

### Run locally (SQLite + no external services)

```bash
# .env with BROKER=paper and DATABASE_URL=sqlite:///./dev.db
uvicorn app.main:app --reload
```

Access at http://127.0.0.1:8000

### Run with PostgreSQL locally

```bash
# Start Postgres container only
docker-compose up db -d

# Update .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/alphamind

# Run app
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├─ api/
│  └─ v1/
│     ├─ auth.py          # Login / register
│     ├─ users.py         # User CRUD
│     ├─ orders.py        # Order submission / list
│     ├─ trades.py        # Trade history
│     ├─ instruments.py   # Trading pairs
│     ├─ accounts.py      # Balance / positions
│     └─ marketdata.py    # Quotes
├─ core/
│  ├─ config.py           # Settings (env, JWT, DB URLs)
│  ├─ security.py         # Password hashing, JWT helpers
│  └─ database.py         # SQLAlchemy engine, session
├─ models/
│  ├─ orm_models.py       # SQLAlchemy ORM (User, Order, Trade, etc.)
│  └─ pydantic_schemas.py # Request/response schemas
├─ services/
│  ├─ execution.py        # Order execution (broker routing)
│  ├─ risk.py             # Risk checks (placeholder)
│  ├─ market_data_ingest.py
│  └─ brokers/            # Broker clients
│     ├─ base.py          # Abstract BrokerClient
│     ├─ exness_client.py
│     ├─ justmarkets_client.py
│     └─ paper_client.py
├─ workers/
│  └─ worker.py           # Async tasks (coming soon)
└─ main.py               # FastAPI app entry
```

## Brain Decisions & AI Integration

### What is the Brain?

The `Brain` service fuses indicator signals with optional AI insights (DeepSeek search + OpenAI chat) to generate trading decisions (BUY/SELL/HOLD). Decisions are persisted to:
- **Redis** (transient, for real-time dashboard)
- **SQL Database** (long-term queryable history)

### Brain API Endpoints

#### Compute a Decision

```bash
POST /api/v1/brain/decide
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "symbol": "EURUSD",
  "candles": [
    {"t": "2025-11-24T10:00:00Z", "o": 1.08, "h": 1.085, "l": 1.075, "c": 1.08, "v": 1000},
    ...
  ],
  "current_price": 1.08
}
```

Response:
```json
{
  "symbol": "EURUSD",
  "decision": "BUY",
  "indicator": { "summary": "...", "signals": "STRONG BUY" },
  "deepseek": { "results": [...] },
  "openai": { "choices": [...] },
  "timestamp": "2025-11-24T10:05:00Z"
}
```

#### List Persisted Decisions

```bash
GET /api/v1/brain/decisions
  ?symbol=EURUSD
  &since=2025-11-24T00:00:00Z
  &limit=50
  &offset=0
Authorization: Bearer $TOKEN
```

Query parameters:
- `symbol` (optional): filter by exact symbol (e.g., `EURUSD`)
- `since` (optional): ISO datetime; returns decisions with `timestamp >= since`
- `limit` (optional): page size (default 50, max 200)
- `offset` (optional): pagination offset (default 0)

Response:
```json
{
  "total": 42,
  "count": 50,
  "items": [
    {
      "id": 1,
      "symbol": "EURUSD",
      "decision": "BUY",
      "indicator": {...},
      "deepseek": null,
      "openai": null,
      "timestamp": "2025-11-24T10:05:00Z",
      "created_at": "2025-11-24T10:05:05Z"
    },
    ...
  ]
}
```

#### Get Recent Decisions (Redis-backed)

```bash
GET /api/v1/brain/recent?limit=20
Authorization: Bearer $TOKEN
```

Returns the last 20 decisions from Redis (transient, not persisted).

### Setting up AI Integration (Optional)

If you want AI-powered decisions, add API keys to `.env`:

```bash
# DeepSeek (search context)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.ai/v1

# OpenAI (chat recommendations)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
```

If keys are missing, the Brain still works with indicators only (no AI enrichment).

### Database Schema

The `brain_decisions` table stores all decisions:

```sql
CREATE TABLE brain_decisions (
  id INTEGER PRIMARY KEY,
  symbol VARCHAR(255) NOT NULL,
  decision VARCHAR(50) NOT NULL,       -- BUY, SELL, HOLD
  indicator JSON,                      -- Indicator output (Fibonacci, etc.)
  deepseek JSON,                       -- DeepSeek search results
  openai JSON,                         -- OpenAI chat response
  timestamp DATETIME NOT NULL,         -- Decision timestamp
  created_at DATETIME DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_symbol ON brain_decisions(symbol);
CREATE INDEX idx_timestamp ON brain_decisions(timestamp);
```

### Running Migrations

Always run migrations before starting the app:

```bash
cd backend
python -m alembic upgrade head
```

This creates the `brain_decisions` table and any other pending schema changes.

### CI/CD with Migrations

The GitHub Actions workflow automatically runs:

```yaml
- name: Run Alembic migrations
  run: python -m alembic upgrade head
```

This ensures the test database includes all schema changes before running tests.

## Next Steps

- [x] WebSocket endpoint (`/ws/trades`) for real-time trade streaming
- [x] Brain decision service (indicator + AI fusion)
- [x] DB persistence for decisions (Alembic migrations)
- [ ] Async worker tasks (Celery/RQ) for background order processing
- [ ] TradingView chart integration to display orders/trades
- [ ] Account statement and P&L reports
- [ ] Risk management (position limits, stop-loss, etc.)

## Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when available)
pytest tests/
```

## Troubleshooting

### "Connection refused" on Postgres/Redis

Ensure Docker services are running:

```bash
docker-compose ps
```

Restart if needed:

```bash
docker-compose restart
```

### "Invalid credentials" on login

Make sure you registered a user first:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -d '{"username":"test","password":"test"}'
```

### Order not filling

Check the BROKER env var:

```bash
echo $BROKER  # Should print "paper" or "exness"
```

For paper trading, fills should be instant. For real brokers, ensure API credentials are valid.

## License

MIT
