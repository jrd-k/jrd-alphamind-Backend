# jrd-alphamind Backend — Complete Documentation

A production-ready FastAPI trading automation platform with **intelligent decision-making**, **multi-broker support**, **real-time trade streaming**, and **comprehensive persistence**. Built for traders who want AI-powered signals fused with technical indicators.

---

## Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
5. [API Reference](#api-reference)
6. [Brain Service (AI + Indicators)](#brain-service-ai--indicators)
7. [Broker Integration](#broker-integration)
8. [Database & Migrations](#database--migrations)
9. [Real-time WebSocket](#real-time-websocket)
10. [Development](#development)
11. [Deployment](#deployment)
12. [Testing](#testing)
13. [Troubleshooting](#troubleshooting)

---

## Overview

**jrd-alphamind Backend** is a comprehensive trading system that automates order execution, real-time decision-making, and trade management. It combines:

- **Technical Indicators** (Fibonacci, RSI, MACD, etc.) for market analysis
- **AI Services** (DeepSeek search + OpenAI chat) for market intelligence
- **Multiple Brokers** (Exness, JustMarkets, Paper Trading) for execution
- **WebSocket Streaming** for real-time trade updates
- **Persistent Storage** (PostgreSQL + SQLite) for trade history and decisions
- **JWT Authentication** for secure API access

The system is designed to be:
- **Modular** — Easy to swap brokers or add new indicators
- **Production-Ready** — Full test coverage, migrations, CI/CD
- **Scalable** — Redis for pub/sub, background task scheduling
- **Safe** — Live trading guards, risk checks, HMAC webhook verification

---

## Core Features

| Feature | Status | Details |
|---------|--------|---------|
| **User Authentication** | ✅ | JWT-based register/login with Argon2 hashing |
| **Broker Integration** | ✅ | Paper (default), Exness, JustMarkets, MT5 (extensible) |
| **Order Management** | ✅ | Submit, list, track, retrieve status |
| **Trade Persistence** | ✅ | Full trade history (SQLAlchemy ORM + Alembic migrations) |
| **Account Management** | ✅ | Balance, open positions, account info |
| **Real-time WebSocket** | ✅ | `/ws/trades` endpoint via Redis pub/sub |
| **Brain Decisions** | ✅ | Indicator + AI fusion → BUY/SELL/HOLD signals |
| **Decision Persistence** | ✅ | `brain_decisions` table with time-series queries |
| **Orchestrator** | ✅ | Automated decision → order flow (optional scheduler) |
| **Market Data Ingestion** | ✅ | Candle aggregation, quote streaming |
| **Risk Management** | ⏳ | Position limits, stop-loss (foundation ready) |
| **CORS Support** | ✅ | Configurable frontend origins |
| **CI/CD** | ✅ | GitHub Actions with migrations, tests |
| **Docker** | ✅ | Full Docker Compose setup (Postgres + Redis) |

---

## Tech Stack

### Core
- **FastAPI** 0.95.0+ — Modern async web framework
- **SQLAlchemy** 2.0+ — ORM with registry pattern (non-deprecated)
- **Pydantic** 2.0+ — Data validation with ConfigDict
- **Alembic** 1.12.0+ — Database migrations (auto-generate)

### Databases & Caching
- **PostgreSQL** 15 — Production database (dev: SQLite)
- **Redis** 7 — Pub/sub, transient cache, scheduler

### Authentication & Security
- **PyJWT** 2.6.0+ — JWT token generation & verification
- **Passlib + Argon2** — Password hashing
- **HMAC** — Webhook signature verification

### Async & Background Tasks
- **Uvicorn** 0.22.0+ — ASGI server
- **Gunicorn** — Production WSGI wrapper
- **asyncio** — Native async/await
- **APScheduler** — Scheduled decision execution (optional)

### Testing
- **pytest** 7.0+ — Test framework
- **pytest-asyncio** — Async test support
- **pytest-cov** — Coverage reporting
- **httpx** — Async HTTP client for tests
- **respx** — HTTP mocking

### HTTP Clients
- **httpx** — Async HTTP (broker API calls)
- **requests** — Sync HTTP (fallback)

### Optional AI Services
- **DeepSeek** API — Web search for market context
- **OpenAI** API — GPT chat for trading recommendations

---

## Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Git**

### 1. Clone & Setup

```bash
git clone https://github.com/jrd-k/jrd-alphamind-Backend.git
cd jrd-alphamind-Backend/backend
cp .env.example .env
```

### 2. Environment Configuration

Edit `.env` for your setup. **Defaults work for local development:**

```bash
# Database
DATABASE_URL=sqlite:///./dev.db          # SQLite for dev; PostgreSQL for prod
REDIS_URL=redis://localhost:6379/0

# JWT & Security
JWT_SECRET=your-secret-key-change-me
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60

# Broker (paper = simulated, exness = real)
BROKER=paper

# Frontend CORS
FRONTEND_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional: AI Services (leave empty to disable)
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...

# Optional: Live Trading (requires CONFIRM_LIVE="CONFIRM-LIVE" to enable)
ENABLE_LIVE_TRADING=False
CONFIRM_LIVE=

# Scheduler
SCHEDULER_ENABLED=True
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_AUTO_EXECUTE=False
```

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

Services start on:
- **API**: http://127.0.0.1:8000
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Verify Setup

```bash
# Check API health
curl http://localhost:8000/docs

# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' | jq -r '.access_token')

# Test endpoint (requires auth)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/accounts/balance
```

---

## API Reference

All endpoints are **versioned** (`/api/v1/`). Authentication required (JWT token) except where noted.

### Authentication

#### Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "alice",
  "password": "secure_password"
}
```

**Response** (201):
```json
{
  "id": 1,
  "username": "alice",
  "created_at": "2025-11-25T10:00:00Z"
}
```

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "alice",
  "password": "secure_password"
}
```

**Response** (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Instruments

#### List Available Trading Pairs

```http
GET /api/v1/instruments
```

**Response** (200):
```json
{
  "instruments": [
    {
      "symbol": "EURUSD",
      "name": "Euro vs US Dollar",
      "type": "forex"
    },
    ...
  ]
}
```

### Orders

#### Submit Order

```http
POST /api/v1/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "EURUSD",
  "side": "buy",
  "quantity": 0.1,
  "order_type": "market",
  "price": null
}
```

**Response** (201):
```json
{
  "id": "order_123",
  "symbol": "EURUSD",
  "side": "buy",
  "quantity": 0.1,
  "status": "filled",
  "fill_price": 1.0812,
  "timestamp": "2025-11-25T10:05:00Z"
}
```

#### List Orders

```http
GET /api/v1/orders?symbol=EURUSD&limit=50&offset=0
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "total": 42,
  "items": [
    {
      "id": "order_123",
      "symbol": "EURUSD",
      "side": "buy",
      "quantity": 0.1,
      "status": "filled",
      "timestamp": "2025-11-25T10:05:00Z"
    },
    ...
  ]
}
```

#### Get Order Details

```http
GET /api/v1/orders/{order_id}
Authorization: Bearer {token}
```

### Trades

#### List Trades

```http
GET /api/v1/trades?symbol=EURUSD&limit=50&offset=0
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "total": 123,
  "items": [
    {
      "id": 123,
      "symbol": "EURUSD",
      "side": "buy",
      "qty": 0.1,
      "price": 1.0812,
      "timestamp": "2025-11-25T10:05:00Z",
      "order_id": "order_123",
      "user_id": 1,
      "metadata": {}
    },
    ...
  ]
}
```

#### Get Trade Details

```http
GET /api/v1/trades/{trade_id}
Authorization: Bearer {token}
```

### Account

#### Check Balance

```http
GET /api/v1/accounts/balance
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "currency": "USD",
  "balance": 10000.50,
  "available": 9500.25,
  "used": 500.25
}
```

#### Get Open Positions

```http
GET /api/v1/accounts/positions
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "positions": [
    {
      "symbol": "EURUSD",
      "side": "long",
      "qty": 0.5,
      "entry_price": 1.0800,
      "current_price": 1.0815,
      "unrealized_pnl": 7.50
    },
    ...
  ]
}
```

---

## Brain Service (AI + Indicators)

### What is the Brain?

The **Brain** is an intelligent decision-making system that:

1. **Analyzes** candles using technical indicators (Fibonacci, RSI, MACD, etc.)
2. **Enriches** analysis with optional AI (DeepSeek search for news, OpenAI for recommendations)
3. **Generates** a trading decision: **BUY**, **SELL**, or **HOLD**
4. **Persists** decisions to Redis (transient) + PostgreSQL (long-term queryable)

**Signal Flow:**
```
Candles + Price → Indicator Analysis → Optional AI → Confidence-weighted Vote → Decision
                                                           (60% indicator)
                                                           (10% DeepSeek)
                                                           (30% OpenAI)
```

### Brain API Endpoints

#### Compute Decision

Compute a single decision for a symbol + candles.

```http
POST /api/v1/brain/decide
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "EURUSD",
  "candles": [
    {
      "t": "2025-11-25T10:00:00Z",
      "o": 1.0800,
      "h": 1.0850,
      "l": 1.0790,
      "c": 1.0820,
      "v": 10000
    },
    {
      "t": "2025-11-25T10:05:00Z",
      "o": 1.0820,
      "h": 1.0860,
      "l": 1.0810,
      "c": 1.0840,
      "v": 12000
    }
  ],
  "current_price": 1.0840
}
```

**Response** (200):
```json
{
  "symbol": "EURUSD",
  "decision": "BUY",
  "confidence": 0.72,
  "indicator": {
    "summary": "Fibonacci retracement at 0.618; strong momentum",
    "signals": "STRONG_BUY",
    "fib_levels": [1.0750, 1.0775, 1.0800, 1.0825],
    "rsi": 68.5,
    "macd_signal": "bullish_crossover"
  },
  "deepseek": {
    "query": "EUR/USD market news 2025-11-25",
    "results": [
      {
        "title": "ECB decides on rate hold",
        "snippet": "European Central Bank..."
      }
    ]
  },
  "openai": {
    "model": "gpt-4",
    "choices": [
      {
        "message": {
          "content": "Current technical setup favors buyers. Watch 1.0850 resistance."
        }
      }
    ]
  },
  "timestamp": "2025-11-25T10:05:00Z"
}
```

#### List Persisted Decisions

Query all historical decisions with filtering and pagination.

```http
GET /api/v1/brain/decisions
  ?symbol=EURUSD
  &since=2025-11-24T00:00:00Z
  &limit=50
  &offset=0
Authorization: Bearer {token}
```

**Query Parameters:**
- `symbol` (string, optional): Filter by exact symbol (e.g., `EURUSD`)
- `since` (ISO datetime, optional): Return decisions with `timestamp >= since`
- `limit` (integer, default 50, max 200): Page size
- `offset` (integer, default 0): Pagination offset

**Response** (200):
```json
{
  "total": 127,
  "count": 50,
  "items": [
    {
      "id": 42,
      "symbol": "EURUSD",
      "decision": "BUY",
      "confidence": 0.75,
      "indicator": {
        "summary": "...",
        "signals": "STRONG_BUY"
      },
      "deepseek": null,
      "openai": null,
      "timestamp": "2025-11-25T10:05:00Z",
      "created_at": "2025-11-25T10:05:05Z"
    },
    ...
  ]
}
```

#### Get Recent Decisions (Redis-backed)

Fetch the last N decisions from Redis cache (transient, fast).

```http
GET /api/v1/brain/recent?limit=20
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "decisions": [
    {
      "symbol": "EURUSD",
      "decision": "BUY",
      "timestamp": "2025-11-25T10:05:00Z"
    },
    ...
  ]
}
```

### Brain Configuration

#### Enable AI Services (Optional)

To enrich decisions with AI insights, add API keys to `.env`:

```bash
# DeepSeek: Web search for market context
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.ai/v1

# OpenAI: GPT chat for recommendations
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
```

**If keys are missing**, the Brain still works with indicators only (no AI enrichment).

#### Confidence Threshold

The Brain enforces a minimum confidence threshold to prevent low-confidence trades. Configure via environment variable:

```bash
# Minimum confidence required for BUY/SELL decisions (default: 0.5)
BRAIN_MIN_CONFIDENCE=0.5
```

- **Range**: 0.0 to 1.0
- **Behavior**: If confidence < threshold, decision becomes "HOLD"
- **Purpose**: Risk management - prevents trades with insufficient signal strength

#### Indicator Configuration

Indicators are computed server-side. Key indicators include:

- **Fibonacci Retracement** — Support/resistance levels
- **RSI (Relative Strength Index)** — Momentum (0-100)
- **MACD (Moving Average Convergence Divergence)** — Trend strength
- **Bollinger Bands** — Volatility

### Brain Database Schema

The `brain_decisions` table persists all decisions for historical analysis:

```sql
CREATE TABLE brain_decisions (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  symbol VARCHAR(255) NOT NULL,
  decision VARCHAR(50) NOT NULL,     -- 'BUY', 'SELL', 'HOLD'
  confidence FLOAT DEFAULT 0.0,      -- Confidence score (0.0-1.0)
  indicator JSON,                    -- Full indicator output
  deepseek JSON,                     -- DeepSeek API response
  openai JSON,                       -- OpenAI API response
  timestamp DATETIME NOT NULL,       -- Decision timestamp (UTC)
  created_at DATETIME DEFAULT NOW()  -- Row creation time
);

-- Indexes for fast queries
CREATE INDEX idx_symbol ON brain_decisions(symbol);
CREATE INDEX idx_timestamp ON brain_decisions(timestamp);
CREATE INDEX idx_symbol_timestamp ON brain_decisions(symbol, timestamp);
```

---

## Broker Integration

### Architecture

Brokers are pluggable via the `BrokerClient` interface. The system routes orders to the configured broker.

```
Order Request → Execution Service → Broker Selector → BrokerClient → Broker API
                                          ↓
                                    (paper / exness / justmarkets)
```

### Paper Trading (Default)

**Best for development and testing.** Simulates fills at realistic prices.

```bash
# .env
BROKER=paper
```

**Features:**
- ✅ No API keys required
- ✅ Instant fills
- ✅ Randomized prices (±0.5% of market)
- ✅ Full order state tracking

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","quantity":0.1}'

# Response: Filled immediately at a simulated price
```

### Exness Integration

**Real broker connection** (demo or live accounts).

#### 1. Get API Credentials

- Log in to [Exness Dashboard](https://exness.com)
- Navigate to **Settings → API Integrations**
- Generate an API key
- Note the **Base URL** (demo or live)

#### 2. Configure .env

```bash
BROKER=exness
EXNESS_API_KEY=your_api_key_here
EXNESS_BASE_URL=https://api.exness-demo.com
# For live trading (requires confirmation):
# EXNESS_BASE_URL=https://api.exness.com
```

#### 3. Restart Backend

```bash
docker-compose restart web
```

#### 4. Submit Order

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","quantity":0.1}'

# Order routed to Exness; response includes live fill price
```

### JustMarkets Integration

**Stub implementation** (follow same pattern as ExnessClient).

```bash
BROKER=justmarkets
JUSTMARKETS_API_KEY=your_api_key_here
JUSTMARKETS_BASE_URL=https://api.justmarkets-demo.com
```

### MetaTrader 5 (MT5) Integration

**Direct connection to MT5 terminal** (demo or live accounts) for direct order execution.

#### 1. Prerequisites

- MetaTrader 5 terminal installed and running
- Python package: Install via `pip install MetaTrader5`

#### 2. Configure .env

```bash
# Choose MT5 as broker
BROKER=mt5

# MT5 Configuration (all optional)
# MT5_PATH: Path to MT5 terminal executable (auto-detect if not specified)
MT5_PATH=C:\Program Files\MetaTrader 5\terminal.exe

# MT5_ACCOUNT: Account number/login
MT5_ACCOUNT=1234567

# MT5_PASSWORD: Account password
MT5_PASSWORD=your_mt5_password
```

#### 3. Start MT5 Terminal

- Open MetaTrader 5
- Log in to your account (demo or live)
- Keep the terminal running (the backend will connect to it)

#### 4. Install MetaTrader5 Package

```bash
pip install MetaTrader5
```

#### 5. Submit Orders

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","quantity":0.1}'

# Order routed to MT5; executed directly on the terminal's account
```

#### MT5 Features

| Feature | Status | Details |
|---------|--------|---------|
| Order Placement | ✅ | Market and limit orders |
| Account Info | ✅ | Balance, equity, margin, leverage |
| Open Positions | ✅ | Query all active positions |
| Order History | ⏳ | Can be added if needed |
| Stop-Loss/Take-Profit | ⏳ | Manual implementation required |

#### MT5 Troubleshooting

**"MT5 not connected" error:**
- Ensure MetaTrader 5 terminal is running
- Check that the terminal is logged in
- Verify `MT5_ACCOUNT` and `MT5_PASSWORD` match the logged-in account

**"Symbol not found" error:**
- Symbol must exist in the MT5 terminal
- Check symbol format (e.g., `EURUSD` not `EUR/USD`)
- Add symbol to Market Watch if missing

**Connection issues on non-Windows:**
- MT5 Python package requires Windows
- Consider using WSL 2 or Wine on macOS/Linux
- Or use Exness/JustMarkets integrations instead

### Adding a New Broker

1. Create `app/services/brokers/mybroker_client.py`:
   ```python
   from app.services.brokers.base import BrokerClient

   class MyBrokerClient(BrokerClient):
       def __init__(self, api_key: str, base_url: str):
           self.api_key = api_key
           self.base_url = base_url

       async def place_order(self, symbol: str, side: str, qty: float, price: Optional[float] = None, order_type: str = "market") -> Dict[str, Any]:
           # Call MyBroker API
           pass

       async def get_balance(self) -> Dict[str, Any]:
           pass

       async def get_positions(self) -> List[Dict[str, Any]]:
           pass
   ```

2. Register in `app/services/execution.py`:
   ```python
   elif broker == "mybroker":
       return MyBrokerClient(api_key, base_url)
   ```

3. Update `.env`:
   ```bash
   BROKER=mybroker
   MYBROKER_API_KEY=...
   MYBROKER_BASE_URL=...
   ```

---

## Economic Calendar

### Overview

The Economic Calendar service tracks **major economic events** that affect currency pairs. Use it to:
- ✅ Check for high-impact events before trading
- ✅ Query events affecting specific pairs (e.g., EURUSD)
- ✅ Get quick trading safety checks
- ✅ Avoid trading during major data releases

### Architecture

```
EconomicCalendar Service
    ↓
Trading Economics API (requires optional API key)
    ↓
Mock Data Fallback (for development/demo)
```

### Configuration

#### Optional: Trading Economics API Key

For real economic data, register at [Trading Economics](https://tradingeconomics.com) and get an API key:

```bash
# .env
TRADING_ECONOMICS_KEY=your_api_key_here
```

If not provided, the service uses realistic mock data automatically.

### API Endpoints

#### 1. List Upcoming Events

Get upcoming economic events with filtering.

```http
GET /api/v1/economic-calendar/upcoming
  ?hours_ahead=168
  &currencies=USD,EUR
  &min_impact=high
Authorization: Bearer {token}
```

**Query Parameters:**
- `hours_ahead` (integer, 1-720, default 168): Look ahead N hours
- `currencies` (string, comma-separated, optional): Filter by currency (e.g., `USD,EUR,GBP`)
- `min_impact` (string, `low|medium|high`, default `low`): Minimum impact level

**Response** (200):
```json
{
  "total": 42,
  "items": [
    {
      "name": "Non-Farm Payroll",
      "country": "United States",
      "currency": "USD",
      "impact": "high",
      "scheduled_time": "2025-12-05T13:30:00Z",
      "forecast_value": "227,000",
      "previous_value": "226,500",
      "actual_value": null,
      "source": "mock"
    },
    {
      "name": "ECB Interest Rate Decision",
      "country": "Euro Area",
      "currency": "EUR",
      "impact": "high",
      "scheduled_time": "2025-12-18T13:45:00Z",
      "forecast_value": "3.0%",
      "previous_value": "3.5%",
      "actual_value": null,
      "source": "mock"
    }
  ]
}
```

#### 2. Events for Specific Pair

Get events that affect a specific trading pair.

```http
GET /api/v1/economic-calendar/pair/EURUSD
  ?minutes_ahead=1440
Authorization: Bearer {token}
```

**Query Parameters:**
- `minutes_ahead` (integer, 1-1440, default 1440): Look ahead N minutes

**Response** (200):
```json
{
  "symbol": "EURUSD",
  "high_impact_events": 3,
  "should_avoid_trading": true,
  "events": [
    {
      "name": "ECB Interest Rate Decision",
      "country": "Euro Area",
      "currency": "EUR",
      "impact": "high",
      "scheduled_time": "2025-12-18T13:45:00Z"
    },
    {
      "name": "US CPI Report",
      "country": "United States",
      "currency": "USD",
      "impact": "high",
      "scheduled_time": "2025-12-11T13:30:00Z"
    }
  ]
}
```

#### 3. Quick Trading Safety Check

Get a quick yes/no answer on whether it's safe to trade a pair.

```http
GET /api/v1/economic-calendar/risk-check
  ?symbol=EURUSD
  &minutes_ahead=120
Authorization: Bearer {token}
```

**Query Parameters:**
- `symbol` (string, required): Trading pair (e.g., `EURUSD`)
- `minutes_ahead` (integer, 1-1440, default 60): Look ahead N minutes

**Response** (200):
```json
{
  "symbol": "EURUSD",
  "safe_to_trade": false,
  "reason": "High-impact ECB decision in next 2 hours",
  "events_count": 1,
  "events": [
    {
      "name": "ECB Interest Rate Decision",
      "impact": "high",
      "minutes_until": 95
    }
  ]
}
```

### Major Economic Indicators Tracked

| Event | Currency | Impact | Typical Release Time |
|-------|----------|--------|----------------------|
| **Non-Farm Payroll (NFP)** | USD | HIGH | 1st Friday, 13:30 UTC |
| **CPI (Inflation)** | USD | HIGH | Mid-month, 13:30 UTC |
| **ECB Interest Rate** | EUR | HIGH | 6 weeks, 13:45 UTC |
| **Fed Interest Rate** | USD | HIGH | ~8 weeks, 18:00 UTC |
| **PMI (Manufacturing)** | Multiple | HIGH | End of month, morning |
| **Retail Sales** | Multiple | MEDIUM | Monthly, morning |
| **Unemployment Rate** | Multiple | MEDIUM | Monthly, 13:30 UTC |
| **GDP (Preliminary)** | Multiple | MEDIUM | Quarterly |

### Integration with Brain Service

To avoid trading during high-impact events, integrate the Economic Calendar into your Brain service:

```python
from app.services.economic_calendar import EconomicCalendar

calendar = EconomicCalendar(api_key=settings.trading_economics_key)

# Before making a decision
should_avoid = calendar.should_avoid_trading(symbol="EURUSD", minutes_window=120)

if should_avoid:
    # Return HOLD instead of BUY/SELL
    return {"decision": "HOLD", "reason": "High-impact event scheduled"}

# Otherwise, proceed with normal analysis
# ...
```

### Caching

The service caches events for **60 minutes** to minimize API calls:

```python
calendar = EconomicCalendar(api_key=settings.trading_economics_key)

# First call → fetches from API (or mock)
events = await calendar.fetch_upcoming_events(hours_ahead=168)

# Subsequent calls within 60 minutes → uses cache
events = await calendar.fetch_upcoming_events(hours_ahead=168)
```

---

## Database & Migrations

### Architecture

The system uses **SQLAlchemy 2.0** (modern registry pattern) with **Alembic** for version control.

```
SQLAlchemy Models → Alembic autogenerate → .py migration files → alembic upgrade head
    ↓
Database Schema
```

### Key Tables

| Table | Purpose |
|-------|---------|
| `user` | Users (username, password hash) |
| `order` | Order history |
| `trade` | Executed trades |
| `brain_decisions` | AI decisions (symbol, decision, timestamp) |

### Running Migrations

#### First Time Setup

```bash
cd backend
python -m alembic upgrade head
```

This applies all pending migrations to the database.

#### After Model Changes

1. Update `app/models/orm_models.py`
2. Auto-generate migration:
   ```bash
   python -m alembic revision --autogenerate -m "add new column"
   ```
3. Review the generated file in `alembic/versions/`
4. Apply:
   ```bash
   python -m alembic upgrade head
   ```

#### View Migration History

```bash
python -m alembic history
```

**Output:**
```
<base> -> 4975dd530ef4 (head), initial db schema
```

#### Rollback to Previous Version

```bash
python -m alembic downgrade -1
```

### Production Database

For production, use **PostgreSQL 15+**:

```bash
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/alphamind
```

Run migrations:
```bash
python -m alembic upgrade head
```

### Development Database

For development, **SQLite** is default and zero-config:

```bash
DATABASE_URL=sqlite:///./dev.db
```

Migrations work identically.

---

## Real-time WebSocket

### Connect to Trade Stream

The `/ws/trades` endpoint broadcasts all executed trades in real-time via Redis pub/sub.

#### Using wscat (Node.js)

```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/trades
```

#### Using websocat (Rust)

```bash
cargo install websocat
websocat ws://localhost:8000/ws/trades
```

#### Using Python

```python
import asyncio
import websockets

async def stream_trades():
    async with websockets.connect("ws://localhost:8000/ws/trades") as ws:
        while True:
            message = await ws.recv()
            print(f"Trade: {message}")

asyncio.run(stream_trades())
```

### Message Format

When an order is executed, a trade event is published:

```json
{
  "id": 123,
  "symbol": "EURUSD",
  "side": "buy",
  "price": 1.0812,
  "qty": 0.1,
  "timestamp": "2025-11-25T10:05:00Z",
  "order_id": "order_abc123",
  "user_id": 1,
  "metadata": {}
}
```

### End-to-End Example

**Terminal 1 — Start Backend:**
```bash
docker-compose up --build
```

**Terminal 2 — Connect WebSocket Client:**
```bash
wscat -c ws://localhost:8000/ws/trades
# Connected. Waiting for trades...
```

**Terminal 3 — Execute Orders:**
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -d '{"username":"trader1","password":"secret"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"username":"trader1","password":"secret"}' | jq -r '.access_token')

# Submit order
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"symbol":"EURUSD","quantity":0.1}'
```

**Terminal 2 Output:**
```json
{
  "id": 123,
  "symbol": "EURUSD",
  "side": "buy",
  "price": 1.0812,
  "qty": 0.1,
  "timestamp": "2025-11-25T10:05:00Z"
}
```

### HTML Client

A test client is included: `ws_trades_client.html`

1. Open in browser
2. Click "Connect"
3. Submit an order via Swagger UI (http://localhost:8000/docs)
4. Watch trades appear in real-time

---

## Development

### Local Setup (No Docker)

#### 1. Create Virtual Environment

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
source .venv/bin/activate          # macOS/Linux
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure .env

```bash
cp .env.example .env
# Edit .env:
# DATABASE_URL=sqlite:///./dev.db    (SQLite for dev)
# BROKER=paper                        (Paper trading)
```

#### 4. Run App

```bash
uvicorn app.main:app --reload
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### 5. Test

```bash
curl http://localhost:8000/docs
```

### Local Setup (With PostgreSQL)

If you prefer PostgreSQL locally:

#### 1. Start PostgreSQL Container

```bash
docker-compose up db -d
```

#### 2. Update .env

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/alphamind
```

#### 3. Run Migrations

```bash
python -m alembic upgrade head
```

#### 4. Run App

```bash
uvicorn app.main:app --reload
```

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py              # POST /auth/register, /auth/login
│   │       ├── orders.py            # POST /orders, GET /orders
│   │       ├── trades.py            # GET /trades
│   │       ├── accounts.py          # GET /accounts/balance, /positions
│   │       ├── instruments.py       # GET /instruments
│   │       ├── brain.py             # POST /brain/decide, GET /brain/decisions
│   │       ├── orchestrator.py      # Automated decision → order flow
│   │       ├── indicators.py        # Indicator computation
│   │       ├── websockets.py        # WS /ws/trades
│   │       ├── webhook.py           # POST /webhook/* (external events)
│   │       └── marketdata.py        # GET /marketdata
│   ├── core/
│   │   ├── config.py                # Settings (env vars)
│   │   ├── security.py              # JWT, password hashing
│   │   └── database.py              # SQLAlchemy setup
│   ├── models/
│   │   ├── orm_models.py            # SQLAlchemy models (User, Order, Trade, etc.)
│   │   └── pydantic_schemas.py      # Pydantic request/response schemas
│   ├── services/
│   │   ├── execution.py             # Order execution (broker routing)
│   │   ├── risk.py                  # Risk checks
│   │   ├── market_data_ingest.py    # Candle aggregation
│   │   ├── brokers/
│   │   │   ├── base.py              # Abstract BrokerClient
│   │   │   ├── paper_client.py      # Paper trading (simulated)
│   │   │   ├── exness_client.py     # Exness integration
│   │   │   └── justmarkets_client.py # JustMarkets integration
│   │   └── brain/
│   │       ├── brain.py             # Decision logic (indicator + AI)
│   │       └── store.py             # Persistence (Redis + DB)
│   ├── workers/
│   │   ├── scheduler.py             # Background task scheduler
│   │   └── worker.py                # Async job execution
│   └── main.py                      # FastAPI app entry
├── alembic/
│   ├── versions/                    # Migration files
│   └── env.py                       # Alembic config
├── tests/
│   ├── test_auth.py                 # Auth tests
│   ├── test_orders.py               # Order tests
│   ├── test_brain*.py               # Brain tests
│   └── ...
├── .env.example                     # Example environment file
├── .env                             # Actual env (git-ignored)
├── requirements.txt                 # Python dependencies
├── alembic.ini                      # Alembic config
├── docker-compose.yml               # Docker services
├── Dockerfile                       # Docker image
├── pytest.ini                       # Pytest config
└── README.md                        # Documentation
```

### Code Style & Linting

The project follows PEP 8. Recommended tools:

```bash
pip install black flake8 isort

# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Check style
flake8 app/ tests/
```

---

## Deployment

### Docker Deployment (Recommended)

#### 1. Configure Production .env

```bash
# Database (use managed PostgreSQL service)
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/alphamind

# Redis (use managed Redis service)
REDIS_URL=redis://:password@prod-redis.example.com:6379/0

# Security
JWT_SECRET=your-very-secure-random-string-here
JWT_EXP_MINUTES=60

# Broker
BROKER=exness
EXNESS_API_KEY=your_production_key

# Optional: AI Services
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...

# Frontend CORS
FRONTEND_ORIGINS=https://app.example.com

# Live Trading Guard
ENABLE_LIVE_TRADING=True
CONFIRM_LIVE=CONFIRM-LIVE
```

#### 2. Build Image

```bash
docker build -t jrd-alphamind-backend:latest .
```

#### 3. Push to Registry

```bash
docker tag jrd-alphamind-backend:latest registry.example.com/jrd-alphamind-backend:latest
docker push registry.example.com/jrd-alphamind-backend:latest
```

#### 4. Deploy to Kubernetes (Example)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jrd-alphamind-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: registry.example.com/jrd-alphamind-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: jwt-secret
        # ... other env vars
```

### Gunicorn Deployment

For production ASGI deployment without Docker:

```bash
pip install gunicorn

gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  app.main:app
```

### Pre-deployment Checklist

- [ ] Run migrations: `alembic upgrade head`
- [ ] Run tests: `pytest -v`
- [ ] Check database connectivity
- [ ] Verify Redis connectivity
- [ ] Set `JWT_SECRET` to a secure value
- [ ] Set `ENABLE_LIVE_TRADING` appropriately
- [ ] Configure `FRONTEND_ORIGINS` for your domain
- [ ] Set up SSL/TLS (HTTPS)
- [ ] Configure logging & monitoring
- [ ] Set up backup strategy for PostgreSQL
- [ ] Test broker API keys on demo account first

---

## Testing

### Run All Tests

```bash
cd backend
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_auth.py -v
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

Opens `htmlcov/index.html` with coverage details.

### Run Tests in Watch Mode

```bash
pip install pytest-watch
ptw
```

### Test Structure

```
tests/
├── test_auth.py              # Authentication tests
├── test_orders.py            # Order submission & retrieval
├── test_trades.py            # Trade history
├── test_brain*.py            # Brain decision logic
├── test_websockets.py        # WebSocket streaming
└── conftest.py               # Pytest fixtures
```

### Example Test

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "secret"}
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"
```

---

## Troubleshooting

### "Connection refused" on PostgreSQL/Redis

**Problem:** Docker services not running.

**Solution:**
```bash
docker-compose ps
docker-compose up -d
```

### "Invalid token" on API calls

**Problem:** JWT token expired or incorrect.

**Solution:**
```bash
# Re-login to get a fresh token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | jq -r '.access_token')

echo $TOKEN
```

### "Order not filling"

**Problem:** Broker not configured correctly.

**Solution:**
```bash
# Check broker setting
echo $BROKER

# For paper trading
export BROKER=paper

# For Exness, verify API key
echo $EXNESS_API_KEY
```

### "Migration failed"

**Problem:** Alembic can't connect to database.

**Solution:**
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# For Docker, ensure services are running
docker-compose ps

# Check database logs
docker-compose logs db
```

### "WebSocket connection refused"

**Problem:** Redis pub/sub not configured.

**Solution:**
```bash
# Verify Redis is running
docker-compose ps redis

# Check Redis connection
redis-cli -h localhost ping
# Should respond: PONG
```

### "CORS error" from frontend

**Problem:** Frontend origin not whitelisted.

**Solution:**
```bash
# Update .env
FRONTEND_ORIGINS=https://your-frontend.com,http://localhost:3000

# Restart backend
docker-compose restart web
```

### Performance Issues

**Problem:** Slow query responses.

**Solution:**
```bash
# Add database indexes
# Check app/models/orm_models.py for __table_args__ with indexes

# For large datasets, use pagination
curl "http://localhost:8000/api/v1/trades?limit=50&offset=0"

# Monitor Redis memory
redis-cli info memory
```

---

## License

MIT

---

## Support

For issues, feature requests, or questions:

- 📧 **GitHub Issues**: [jrd-alphamind-Backend/issues](https://github.com/jrd-k/jrd-alphamind-Backend/issues)
- 📚 **Docs**: [Frontend Integration Guide](./docs/FRONTEND_INTEGRATION.md)

---

**Made with ❤️ for traders who code**
