# Complete Step-by-Step Application Flow

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Startup Sequence](#startup-sequence)
3. [User Registration & Authentication](#user-registration--authentication)
4. [Placing an Order (End-to-End)](#placing-an-order-end-to-end)
5. [Brain Decision Making](#brain-decision-making)
6. [Economic Calendar Integration](#economic-calendar-integration)
7. [WebSocket Real-time Streaming](#websocket-real-time-streaming)
8. [Database Persistence](#database-persistence)
9. [Error Handling & Fallbacks](#error-handling--fallbacks)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Web)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP + WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ API Endpoints (v1)                                         │ │
│  │ ├─ /auth (register, login)                                │ │
│  │ ├─ /orders (place, list, status)                          │ │
│  │ ├─ /brain/decide (AI + indicators)                        │ │
│  │ ├─ /brain/decisions (persistence query)                   │ │
│  │ ├─ /trades (executed trades)                              │ │
│  │ ├─ /marketdata (candles, quotes)                          │ │
│  │ ├─ /indicators (RSI, MACD, Fibonacci)                     │ │
│  │ ├─ /economic-calendar/* (event checking)                  │ │
│  │ └─ /ws (WebSocket for live updates)                       │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
│                    │                                             │
│  ┌─────────────────┴──────────────────────────────────────────┐ │
│  │ Core Services Layer                                        │ │
│  │ ├─ Brain (Fibonacci + AI fusion)                          │ │
│  │ ├─ Execution (Order → Broker)                            │ │
│  │ ├─ EconomicCalendar (Event fetching)                     │ │
│  │ ├─ Brokers (Paper, Exness, JustMarkets, MT5)            │ │
│  │ ├─ Indicators (Technical analysis)                       │ │
│  │ └─ WebSocket Manager (Redis pub/sub)                    │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
│                    │                                             │
└────────┬───────────┼───────────────────────────────────┬──────────┘
         │           │                                   │
         ▼           ▼                                   ▼
    ┌─────────┐ ┌─────────┐                        ┌──────────┐
    │ Redis   │ │Database │                        │  Brokers │
    │(Pub/Sub)│ │(Postgres)                        │ (Live)   │
    └─────────┘ └─────────┘                        └──────────┘
```

---

## Startup Sequence

### Step 1: Application Initialization (`app/main.py`)

```python
# 1. Create FastAPI app
app = FastAPI(title="jrd-alphamind-backend")

# 2. Configure CORS middleware
app.add_middleware(CORSMiddleware, 
    allow_origins=["http://localhost:3000", ...],  # from .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 3. Register all routers (API endpoints)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(brain.router, prefix="/api/v1/brain", tags=["brain"])
app.include_router(economic_calendar.router, prefix="/api/v1", tags=["economic-calendar"])
# ... more routers ...
```

### Step 2: Database Initialization

```python
@app.on_event("startup")
def on_startup():
    # 1. Initialize database tables (if they don't exist)
    init_db()  # Creates all SQLAlchemy models as tables
    
    # 2. Start the scheduler for automated orchestration
    scheduler = get_scheduler()
    if scheduler.enabled:
        # Scheduler runs in background, checks for trade signals
        asyncio.create_task(scheduler.start())
    
    # 3. Connect to Redis (if available)
    # Used for pub/sub trade updates and caching
```

### Step 3: Connection Pool Setup

**Database Connection** (`app/core/database.py`):
```python
engine = create_engine(settings.database_url, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Redis Connection** (on-demand in services):
```python
r = redis.asyncio.from_url(settings.redis_url)
await r.publish("trades", json.dumps(trade_data))
```

**Result:** ✅ App is ready to handle requests

---

## User Registration & Authentication

### Step 1: User Registers

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "trader123",
  "password": "SecurePass!2025"
}
```

### Step 2: Backend Process

```python
# app/api/v1/auth.py

@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    
    # 1. Check if username already exists
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="username already exists")
    
    # 2. Hash password using Argon2 (one-way, salted)
    hashed_pwd = get_password_hash(user_in.password)
    
    # 3. Create user record in database
    user = User(username=user_in.username, hashed_password=hashed_pwd)
    db.add(user)
    db.commit()  # ← Saved to PostgreSQL/SQLite
    db.refresh(user)
    
    # 4. Return user info (NOT password)
    return user
```

### Step 3: User Logs In

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "trader123",
  "password": "SecurePass!2025"
}
```

### Step 4: Backend Authenticates

```python
@router.post("/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    
    # 1. Find user by username
    user = db.query(User).filter(User.username == user_in.username).first()
    
    # 2. Verify password
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    
    # 3. Generate JWT token (valid for 30 days)
    token = create_access_token(subject=str(user.id))
    
    # 4. Return token to client
    return {
        "access_token": token,
        "token_type": "bearer"
    }
```

### Step 5: Client Stores Token

Client saves token to localStorage/sessionStorage:
```javascript
// Frontend
localStorage.setItem("token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...");
```

### Step 6: All Future Requests Use Token

```http
GET /api/v1/orders
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Backend validates token via dependency:
```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate JWT token and return authenticated user"""
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    user_id = payload.get("sub")
    
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user
```

**Result:** ✅ User authenticated, can access protected endpoints

---

## Placing an Order (End-to-End)

### Step 1: User Submits Order Request

```http
POST /api/v1/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "EURUSD",
  "quantity": 0.1
}
```

### Step 2: FastAPI Route Handler (`app/api/v1/orders.py`)

```python
@router.post("/", response_model=OrderRead)
def submit_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)  # ← Validates JWT
):
    # 1. Create Order record in database (status="new")
    o = Order(
        user_id=current_user.id,
        symbol=order_in.symbol,
        quantity=order_in.quantity,
        status="new"
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    
    # 2. Prepare execution payload
    exec_payload = {
        "symbol": o.symbol,
        "side": "buy",
        "qty": o.quantity,
        "price": 0.0,  # Market order
        "order_id": str(o.id),
        "user_id": o.user_id,
    }
    
    # 3. Call execution service (async)
    try:
        execution.execute_order(exec_payload)
        
        # 4. Update order status to "filled"
        o.status = "filled"
        db.add(o)
        db.commit()
        db.refresh(o)
    except Exception as e:
        # On error, leave order as "new" and log
        logger.error(f"Execution failed: {e}")
    
    # 5. Return updated order to client
    return o
```

### Step 3: Execution Service (`app/services/execution.py`)

```python
async def execute_order(order: Dict[str, Any]) -> Dict[str, Any]:
    
    # 1. Select broker based on BROKER environment variable
    broker = os.getenv("BROKER", "paper").lower()
    
    if broker == "paper":
        client = PaperTradingClient()
    elif broker == "exness":
        client = ExnessClient()
    elif broker == "mt5":
        client = MT5Client(
            mt5_path=os.getenv("MT5_PATH"),
            account=os.getenv("MT5_ACCOUNT"),
            password=os.getenv("MT5_PASSWORD")
        )
    # ...
    
    # 2. Check if live trading is enabled
    if not (settings.enable_live_trading and settings.confirm_live_token == "CONFIRM-LIVE"):
        # SIMULATION MODE (default)
        broker_result = {
            "order_id": f"sim-{uuid.uuid4().hex}",
            "price": 1.05234,  # Simulated fill price
            "status": "simulated"
        }
    else:
        # LIVE MODE (only if explicitly enabled)
        broker_result = await client.place_order(
            symbol=order["symbol"],
            side=order["side"],
            qty=order["qty"],
            price=order["price"],
            order_type="market"
        )
        # Returns real broker fill confirmation
    
    # 3. Save Trade to Database
    db = SessionLocal()
    trade_payload = {
        "symbol": order["symbol"],
        "side": order["side"],
        "price": broker_result["price"],
        "qty": order["qty"],
        "order_id": order["order_id"],
        "user_id": order["user_id"],
        "metadata": {
            "broker_order_id": broker_result.get("order_id"),
            "simulated": broker_result.get("status") == "simulated"
        }
    }
    
    trade = Trade(**trade_payload)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    db.close()
    
    # 4. Publish Trade to Redis (real-time updates)
    if redis_async is not None:
        try:
            r = redis_async.from_url(settings.redis_url)
            pub_data = {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "price": trade.price,
                "qty": trade.qty,
                "timestamp": trade.timestamp.isoformat(),
                "order_id": trade.order_id,
                "user_id": trade.user_id,
                "metadata": trade.metadata
            }
            await r.publish("trades", json.dumps(pub_data))
            # ← All WebSocket clients subscribed to "trades" channel receive update
        except Exception as e:
            logger.warning(f"Redis publish failed: {e}")
    
    # 5. Return confirmation
    return {
        "order_id": trade.id,
        "status": broker_result.get("status", "filled")
    }
```

### Step 4: Broker Execution (Example: Paper Trading)

```python
# app/services/brokers/paper_client.py

class PaperTradingClient(BrokerClient):
    
    async def place_order(self, symbol: str, side: str, qty: float, 
                         price: Optional[float] = None, order_type: str = "market") -> Dict[str, Any]:
        
        # 1. Simulate market conditions
        import random
        
        # Get a "market price" (you could fetch from real data source)
        market_price = self.get_market_price(symbol)
        
        # 2. Simulate realistic fill (±0.5%)
        deviation = random.uniform(-0.005, 0.005)
        fill_price = market_price * (1 + deviation)
        
        # 3. Return broker-like response
        return {
            "order_id": f"paper-{uuid.uuid4().hex}",
            "price": fill_price,
            "qty": qty,
            "status": "filled",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
```

### Step 5: Client Receives Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 42,
  "user_id": 1,
  "symbol": "EURUSD",
  "quantity": 0.1,
  "status": "filled",
  "created_at": "2025-11-26T14:23:45.123Z"
}
```

**Flow Summary:**
```
User Request
    ↓
Validate JWT (get user)
    ↓
Create Order record (DB)
    ↓
Execute Order (Execution Service)
    ├─ Select Broker
    ├─ Place Order (Broker)
    └─ Get Fill Price
        ↓
Create Trade record (DB)
    ↓
Publish Trade to Redis
    ├─ WebSocket clients notified
    └─ Real-time streaming
        ↓
Return Response to Client
```

**Result:** ✅ Order placed, executed, persisted, and broadcast in real-time

---

## Brain Decision Making

### Step 1: Request Brain Decision

```http
POST /api/v1/brain/decide
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "EURUSD",
  "candles": [
    {"t": 1700000000, "o": 1.0800, "h": 1.0820, "l": 1.0790, "c": 1.0815, "v": 10000},
    {"t": 1700003600, "o": 1.0815, "h": 1.0840, "l": 1.0810, "c": 1.0835, "v": 12000},
    ...
  ],
  "current_price": 1.0835
}
```

### Step 2: Brain Service Analysis (`app/services/brain/brain.py`)

The Brain processes decisions through 3 stages:

#### **Stage 1: Technical Indicators**

```python
class Brain:
    async def decide(self, symbol: str, candles: List[Dict], current_price: float):
        
        # 1. Compute Fibonacci levels from price action
        fib = compute_fibonacci(candles, lookback=50)
        
        # Returns:
        fib = {
            "summary": "Price at 0.618 retracement; momentum strong; RSI 72",
            "signals": "STRONG_BUY",
            "fib_levels": [1.0750, 1.0775, 1.0800, 1.0825, 1.0850],
            "rsi": 72.5,
            "macd_signal": "bullish_crossover",
            ...
        }
```

#### **Stage 2: Market Context (DeepSeek AI Search)**

```python
        # 2. If DeepSeek API key configured, get market news
        if self.deepseek:
            query = f"Market context for {symbol}. Indicator: STRONG_BUY"
            ds_res = await self.deepseek.search(query, top_k=3)
            
            # Returns web search results about EUR/USD
            ds_res = {
                "query": "Market context for EURUSD. Indicator: STRONG_BUY",
                "results": [
                    {
                        "title": "ECB holds rates; market eyes inflation data",
                        "snippet": "European Central Bank decided to maintain policy rates...",
                        "url": "..."
                    },
                    ...
                ]
            }
```

#### **Stage 3: Trading Recommendation (OpenAI GPT)**

```python
        # 3. If OpenAI API key configured, get AI recommendation
        if self.openai:
            messages = [
                {"role": "system", "content": "You are a trading assistant. Respond with BUY, SELL, or HOLD."},
                {"role": "user", "content": f"Symbol: EURUSD\nIndicators: STRONG_BUY\nNews: ECB holds rates...\nPrice: 1.0835"}
            ]
            openai_res = await self.openai.chat(messages)
            
            # Returns GPT recommendation
            openai_res = {
                "model": "gpt-4",
                "choices": [
                    {
                        "message": {
                            "content": "BUY - Technical setup strong, no major headwinds from ECB decision"
                        }
                    }
                ]
            }
```

#### **Stage 4: Signal Fusion (Confidence-Weighted Voting)**

```python
        # 4. Merge all signals with confidence weights
        
        # Conversion function: BUY → +1, SELL → -1, HOLD → 0
        def sig_to_score(signal: str) -> float:
            if "BUY" in signal.upper():
                return 1.0
            elif "SELL" in signal.upper():
                return -1.0
            return 0.0
        
        # Confidence weights (tunable)
        weights = {
            "indicator": 0.60,      # 60% — most reliable, based on math
            "deepseek": 0.10,       # 10% — context, lower confidence
            "openai": 0.30          # 30% — AI model, moderate confidence
        }
        
        # Weighted average
        indicator_score = sig_to_score("STRONG_BUY") × 0.60 = 0.60
        deepseek_score = sig_to_score("BULLISH") × 0.10 = 0.10
        openai_score = sig_to_score("BUY") × 0.30 = 0.30
        
        total_score = 0.60 + 0.10 + 0.30 = 1.0
        confidence = total_score / (0.60 + 0.10 + 0.30) = 1.0 / 1.0 = 1.0
        
        # Convert score back to decision
        final_decision = "BUY"  # (score > 0.3)
```

### Step 3: Persist Decision to Database

```python
        # 5. Save decision to database
        db = SessionLocal()
        brain_decision = BrainDecision(
            symbol=symbol,
            decision=final_decision,  # "BUY" | "SELL" | "HOLD"
            confidence=confidence,
            indicator=fib,
            deepseek=ds_res,
            openai=openai_res,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(brain_decision)
        db.commit()
        db.refresh(brain_decision)
        db.close()
```

### Step 4: Return Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "symbol": "EURUSD",
  "decision": "BUY",
  "confidence": 0.85,
  "indicator": {
    "summary": "Fibonacci retracement at 0.618; strong momentum",
    "signals": "STRONG_BUY",
    "fib_levels": [1.0750, 1.0775, 1.0800, 1.0825],
    "rsi": 72.5,
    "macd_signal": "bullish_crossover"
  },
  "deepseek": {
    "query": "Market context for EURUSD...",
    "results": [...]
  },
  "openai": {
    "model": "gpt-4",
    "choices": [{
      "message": {
        "content": "BUY - Technical setup strong..."
      }
    }]
  },
  "timestamp": "2025-11-26T14:25:00Z"
}
```

**Brain Flow:**
```
Candles + Price
    ↓
Fibonacci Analysis
    ↓
DeepSeek News Search (optional)
    ↓
OpenAI Chat (optional)
    ↓
Confidence-Weighted Fusion
    ↓
BUY/SELL/HOLD + Confidence Score
    ↓
Save to Database
    ↓
Return to Client
```

**Result:** ✅ AI-powered trading signal with full reasoning

---

## Economic Calendar Integration

### Step 1: Check Upcoming Economic Events

```http
GET /api/v1/economic-calendar/upcoming?hours_ahead=168&min_impact=high
Authorization: Bearer {token}
```

### Step 2: EconomicCalendar Service

```python
# app/services/economic_calendar.py

class EconomicCalendar:
    
    async def fetch_upcoming_events(self, hours_ahead=168, currencies=None, min_impact=None):
        
        # 1. Check cache (60-minute TTL)
        if self._last_fetch and (now - self._last_fetch).total_seconds() < 3600:
            events = self.events  # ← Cache hit!
        else:
            # 2. Fetch fresh events
            if self.api_key:
                # Use Trading Economics API (real data)
                events = await self._fetch_trading_economics(hours_ahead)
            else:
                # Use mock data (fallback)
                events = self._generate_mock_events(hours_ahead)
            
            self._last_fetch = now
            self.events = events
        
        # 3. Filter by currency and impact
        filtered = []
        for event in events:
            if currencies and event.currency not in currencies:
                continue
            if min_impact and event.impact.value < min_impact.value:
                continue
            filtered.append(event)
        
        # 4. Sort by time
        filtered.sort(key=lambda e: e.scheduled_time)
        
        return filtered
```

### Step 3: Check if Trading is Safe

```python
        # Alternative: Quick risk check for specific pair
        
        events = calendar.get_events_for_pair("EURUSD", minutes_ahead=120)
        # Maps EURUSD → ["EUR", "USD"] → finds events affecting those currencies
        
        should_avoid = calendar.should_avoid_trading("EURUSD", minutes_window=60)
        # Returns True if high-impact event in next 60 minutes
```

### Step 4: Integration with Brain

The Brain can use this before making decisions:

```python
# Before returning a BUY signal
from app.services.economic_calendar import EconomicCalendar

calendar = EconomicCalendar(api_key=settings.trading_economics_key)

# Check safety
if calendar.should_avoid_trading("EURUSD", minutes_window=120):
    return {
        "decision": "HOLD",
        "reason": "High-impact economic event (NFP) in 90 minutes"
    }

# Safe to proceed with normal analysis
...
```

**Result:** ✅ Trading prevented during risky economic events

---

## WebSocket Real-time Streaming

### Step 1: Client Connects

```javascript
// Frontend (React)

const ws = new WebSocket("ws://localhost:8000/ws/trades");

ws.onopen = () => console.log("Connected to trade stream");

ws.onmessage = (event) => {
    const trade = JSON.parse(event.data);
    console.log("New trade:", trade);
    // Update UI with real-time trade
};

ws.onerror = (error) => console.error("WebSocket error:", error);
```

### Step 2: Backend WebSocket Manager

```python
# app/api/v1/websockets.py

@router.websocket("/ws/trades")
async def websocket_endpoint(websocket: WebSocket):
    
    # 1. Accept connection
    await websocket.accept()
    
    # 2. Subscribe to Redis "trades" channel
    redis_client = redis.asyncio.from_url(settings.redis_url)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("trades")
    
    try:
        # 3. Listen for messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                # 4. Forward to WebSocket client
                await websocket.send_text(message["data"])
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        # 5. Clean up on disconnect
        await pubsub.unsubscribe("trades")
        await websocket.close()
```

### Step 3: Trade Execution Publishes Update

When an order is executed (from earlier flow):

```python
# Step 4 of execution.py

await r.publish("trades", json.dumps({
    "id": 42,
    "symbol": "EURUSD",
    "side": "buy",
    "price": 1.0835,
    "qty": 0.1,
    "timestamp": "2025-11-26T14:23:45Z",
    ...
}))
```

### Step 4: Broadcasting to All Connected Clients

```
Redis Channel "trades"
    ├─ Connected Client 1 ← receives update
    ├─ Connected Client 2 ← receives update
    └─ Connected Client 3 ← receives update
```

Each client sees the trade in real-time without polling.

**Result:** ✅ Live trade updates to all connected traders

---

## Database Persistence

### Tables Created on Startup

```python
# app/models/orm_models.py

class User(Base):
    __tablename__ = "user"
    id: int
    username: str (unique)
    hashed_password: str
    created_at: datetime

class Order(Base):
    __tablename__ = "order"
    id: int
    user_id: int (FK → user.id)
    symbol: str
    quantity: float
    status: str ("new" | "filled" | "cancelled")
    created_at: datetime

class Trade(Base):
    __tablename__ = "trade"
    id: int
    symbol: str
    side: str ("buy" | "sell")
    price: float
    qty: float
    order_id: str (FK → order.id)
    user_id: int (FK → user.id)
    metadata: dict
    timestamp: datetime
    created_at: datetime

class BrainDecision(Base):
    __tablename__ = "brain_decisions"
    id: int
    symbol: str
    decision: str ("BUY" | "SELL" | "HOLD")
    confidence: float (0.0 - 1.0)
    indicator: dict
    deepseek: dict
    openai: dict
    timestamp: datetime
    created_at: datetime
```

### Migration with Alembic

```bash
# On first setup
alembic upgrade head

# After changing models
alembic revision --autogenerate -m "add new_column"
alembic upgrade head

# View history
alembic history
```

### Query Examples

```python
# Get all trades for user
db.query(Trade).filter(Trade.user_id == 1).all()

# Get recent decisions for EURUSD
db.query(BrainDecision)\
    .filter(BrainDecision.symbol == "EURUSD")\
    .order_by(BrainDecision.timestamp.desc())\
    .limit(50)\
    .all()

# Get orders in last 24 hours
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)
db.query(Order).filter(Order.created_at >= yesterday).all()
```

**Result:** ✅ Persistent trade history and audit trail

---

## Error Handling & Fallbacks

### Broker Connection Failure

```python
try:
    broker_result = await client.place_order(...)
except BrokerConnectionError as e:
    logger.error(f"Broker connection failed: {e}")
    
    # Fallback: Use simulation mode
    broker_result = {
        "order_id": f"sim-{uuid.uuid4().hex}",
        "price": market_price,
        "status": "simulated"
    }
    # Trade still persists with metadata indicating simulation
```

### API Key Missing

```python
class Brain:
    def __init__(self):
        # DeepSeek optional
        if settings.deepseek_api_key:
            self.deepseek = DeepSeekClient()
        else:
            self.deepseek = None  # Falls back to just indicators
        
        # OpenAI optional
        if settings.openai_api_key:
            self.openai = OpenAIClient()
        else:
            self.openai = None  # Falls back to indicators + deepseek
```

**Graceful degradation:**
```
Decision = Indicators + DeepSeek + OpenAI
    ↓
If OpenAI fails:
    Decision = Indicators + DeepSeek
    ↓
If DeepSeek fails:
    Decision = Indicators only
```

### Redis Connection Failure

```python
try:
    await r.publish("trades", json.dumps(trade_data))
except Exception as e:
    logger.warning(f"Redis publish failed (non-blocking): {e}")
    # Trade already persisted to DB; WebSocket clients just won't get instant update
    # They can still query /api/v1/trades for history
```

### Database Connection Failure

```python
try:
    db = SessionLocal()
    trade = Trade(**trade_payload)
    db.add(trade)
    db.commit()
except Exception as e:
    logger.error(f"Database error: {e}")
    raise  # ← Block execution; don't lose trade record
```

**Result:** ✅ Robust system with graceful degradation

---

## Complete Request Lifecycle Example

**Scenario:** Trader places a BUY order for EURUSD at 2:00 PM

```
┌─────────────────────────────────────────────────────────────────┐
│ T=0s                                                            │
│ User clicks BUY on EURUSD in frontend                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=1ms                                                           │
│ POST /api/v1/orders with JWT token                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=2ms                                                           │
│ FastAPI validates JWT → get user_id = 42                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=3ms                                                           │
│ Create Order record (status="new") → DB                         │
│ Order ID = 1001 assigned by database                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=4ms                                                           │
│ Call execution service with order details                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=5ms                                                           │
│ Select broker (BROKER=paper)                                   │
│ Create PaperTradingClient                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=6ms                                                           │
│ Simulate fill (Price: 1.0835 ± 0.5%) → 1.08374               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=7ms                                                           │
│ Create Trade record in database                                 │
│ Trade ID = 5423 assigned                                       │
│ Status: filled, Price: 1.08374, Qty: 0.1                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=8ms                                                           │
│ Publish to Redis "trades" channel:                             │
│ {id: 5423, symbol: EURUSD, side: buy, price: 1.08374, ...}   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=9ms                                                           │
│ All WebSocket clients receive update                            │
│ Frontend UI updates in real-time                               │
│ Trader sees: "EURUSD BUY executed @ 1.08374"                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ T=10ms                                                          │
│ HTTP response sent to original request:                         │
│ {id: 1001, user_id: 42, status: filled, ...}                  │
└─────────────────────────────────────────────────────────────────┘

Total Time: ~10ms end-to-end
```

---

## Summary

The **jrd-alphamind Backend** is a **multi-layered trading automation system**:

1. **API Layer** — FastAPI endpoints for all operations
2. **Authentication** — JWT tokens + Argon2 password hashing
3. **Business Logic** — Brain (indicators + AI), Execution (broker selection), Economic Calendar
4. **Persistence** — PostgreSQL/SQLite for all data
5. **Real-time** — Redis pub/sub + WebSocket streaming
6. **Brokers** — Paper (default), Exness, JustMarkets, MetaTrader 5
7. **Resilience** — Graceful fallbacks, error handling, caching

All components work together to provide traders with **AI-powered signals, risk management, and real-time execution**.

