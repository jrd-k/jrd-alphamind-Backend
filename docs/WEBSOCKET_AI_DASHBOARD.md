# Secure WebSocket & AI Dashboard Guide

Complete implementation of JWT-authenticated WebSocket connections and real-time AI decision visualization dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AIDecisionDashboard Component                            │  │
│  │  ├─ Real-time decision charts (Recharts)                 │  │
│  │  ├─ Confidence metrics                                   │  │
│  │  ├─ Time series analysis                                 │  │
│  │  └─ Recent signals list                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  useSecureWebSocket Hook                                 │  │
│  │  ├─ JWT token management                                 │  │
│  │  ├─ Auto-reconnect with exponential backoff              │  │
│  │  ├─ Heartbeat ping/pong                                  │  │
│  │  └─ Message routing                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
└───────────────┬───────────┴──────────────┬──────────────────────┘
                │ WebSocket (JWT Token)    │ HTTP (JWT Token)
                ▼                          ▼
┌────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /ws/trades (Secure WebSocket)                           │  │
│  │  ├─ JWT token verification                               │  │
│  │  ├─ ConnectionManager (user tracking)                    │  │
│  │  ├─ Redis pubsub listener                                │  │
│  │  ├─ Trade stream forwarding                              │  │
│  │  ├─ Brain signal forwarding                              │  │
│  │  └─ Heartbeat/ping-pong                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/v1/brain/analytics (REST)                          │  │
│  │  ├─ Decision statistics (BUY/SELL/HOLD ratios)           │  │
│  │  ├─ Confidence distribution analysis                     │  │
│  │  ├─ Time series aggregation                              │  │
│  │  ├─ Indicator performance metrics                        │  │
│  │  └─ Recent signals list                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/v1/brain/symbols (REST)                            │  │
│  │  └─ List available trading symbols                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
└───────────────┬───────────┴──────────────┬──────────────────────┘
                │                          │
                ▼                          ▼
        ┌──────────────┐         ┌──────────────────┐
        │ PostgreSQL   │         │ Redis (pub/sub)  │
        │ BrainDecisions│        └──────────────────┘
        └──────────────┘
```

## Features

### 1. JWT-Authenticated WebSocket

**Security Features:**
- Mandatory JWT token in query parameter
- Auto-reconnect with exponential backoff
- Connection limits per user
- Heartbeat mechanism to detect stale connections
- Cleanup on disconnect

**Message Types:**

Client → Server:
```json
{"action": "ping"}
{"action": "subscribe_symbol", "symbol": "EURUSD"}
{"action": "stats"}
```

Server → Client:
```json
{"type": "trade", "data": {...}, "timestamp": "2026-02-27T..."}
{"type": "brain_signal", "data": {...}, "timestamp": "2026-02-27T..."}
{"type": "heartbeat", "timestamp": "2026-02-27T..."}
{"type": "pong", "timestamp": "2026-02-27T..."}
{"type": "subscribed", "symbol": "EURUSD", "timestamp": "2026-02-27T..."}
{"type": "error", "message": "..."}
```

### 2. AI Decision Analytics

**Endpoints:**

```bash
# Get analytics for dashboard
GET /api/v1/brain/analytics?symbol=EURUSD&days=30

# Get available symbols
GET /api/v1/brain/symbols
```

**Response Structure:**
```json
{
  "summary": {
    "total_decisions": 150,
    "buy_ratio": 0.40,
    "sell_ratio": 0.35,
    "hold_ratio": 0.25,
    "avg_confidence": 0.68
  },
  "confidence_distribution": {
    "high": 95,
    "medium": 42,
    "low": 13
  },
  "avg_confidence_by_type": {
    "BUY": 0.71,
    "SELL": 0.65,
    "HOLD": 0.58
  },
  "time_series": [
    {
      "date": "2026-02-20",
      "buy": 8,
      "sell": 5,
      "hold": 2,
      "avg_confidence": 0.67
    }
  ],
  "indicator_performance": {
    "RSI_OVERSOLD": {"count": 12, "avg_confidence": 0.72},
    "MACD_CROSSOVER": {"count": 8, "avg_confidence": 0.65}
  },
  "recent_decisions": [
    {
      "id": 42,
      "symbol": "EURUSD",
      "decision": "BUY",
      "confidence": 0.85,
      "timestamp": "2026-02-27T14:30:00",
      "indicator_summary": "RSI oversold + MACD bullish",
      "rsi": 28.5,
      "macd": "bullish_cross"
    }
  ]
}
```

## Frontend Implementation

### Hook Usage

```typescript
import { useSecureWebSocket } from '@/hooks/useSecureWebSocket';
import { AIDecisionDashboard } from '@/components/AIDecisionDashboard';

export function TradingPage() {
  const { isConnected, lastMessage } = useSecureWebSocket({
    onTrade: (trade) => console.log('New trade:', trade),
    onBrainSignal: (signal) => console.log('New signal:', signal),
    onError: (error) => console.error('WebSocket error:', error),
    reconnectInterval: 3000,
    maxReconnects: 5
  });

  return (
    <div>
      <AIDecisionDashboard />
    </div>
  );
}
```

### Dashboard Features

**Tabs:**
1. **Decision Distribution** - Pie chart (BUY/SELL/HOLD) + confidence by type
2. **Timeline** - 30-day stacked area chart with daily signal counts
3. **Confidence Analysis** - Distribution histogram + confidence trend line
4. **Recent Signals** - Scrollable list of latest 20 decisions with metrics

**Key Metrics:**
- Total Decisions (30-day)
- Average Confidence (with progress bar)
- Buy Signal Ratio
- Sell Signal Ratio

## Backend Implementation

### WebSocket Endpoint

Located in `app/api/v1/websockets_secure.py`:

```python
from fastapi import WebSocket, Query
from app.api.v1.websockets_secure import (
    ConnectionManager, 
    verify_token,
    websocket_trades,
    websocket_market_data
)

# Registered in main.py:
app.websocket("/ws/trades")(websocket_trades)
app.websocket("/ws/market-data")(websocket_market_data)
```

**ConnectionManager Features:**
- Track connections per user
- Send messages to specific users
- Broadcast to all users
- Get connection statistics
- Auto-cleanup on disconnect

### Brain Analytics Endpoint

Located in `app/api/v1/brain.py`:

```python
@router.get("/analytics")
async def get_brain_analytics(
    symbol: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive AI decision analytics for visualization."""
    # Aggregates BrainDecision records and calculates metrics
```

## Real-Time Data Flow

### Trade Streaming

1. **Order Execution** triggers `trade_created` webhook
2. **Orchestrator** publishes to `trades:user:{user_id}` Redis channel
3. **WebSocket listener** receives and forwards to connected client
4. **Dashboard** updates in real-time

### AI Signal Streaming

1. **Brain Service** makes decision
2. **Brain Decision** record created in database
3. **Orchestrator** publishes to `brain:signals:{user_id}` Redis channel
4. **WebSocket listener** receives and forwards to connected client
5. **Dashboard** refreshes analytics
6. **Recent Signals** list updates immediately

## Deployment

### Kubernetes Ingress Configuration

```yaml
# WebSocket path requires special headers
nginx.ingress.kubernetes.io/websocket-services: backend
nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
```

### Environment Variables

```bash
FRONTEND_ORIGINS=https://alphamind.yourdomain.com,https://your-app.lovable.app
JWT_SECRET=<random-hex-32>
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60
```

## Security Considerations

### Token Lifecycle

1. **Login** returns `access_token` (JWT)
2. **Store** in `localStorage` (or secure HTTP-only cookie)
3. **Include** in WebSocket URL: `/ws/trades?token=<JWT>`
4. **Validate** on server using JWT secret
5. **Expire** after configured duration (default 60 min)
6. **Refresh** via `/api/v1/auth/refresh` endpoint

### Connection Limits

- Max connections per user: unlimited (configurable)
- Idle timeout: server sends heartbeat every 30s
- Client timeout: if no message for 90s, reconnect
- Reconnect backoff: 3s → 4.5s → 6.75s (exponential)

### Data Privacy

- Only return data for authenticated user
- Brain decisions filtered by user context
- Connection manager tracks user_id, not anonymous
- All Redis channels are user-scoped

## Error Handling

### Client-Side

```typescript
const { isConnected } = useSecureWebSocket({
  onError: (error) => {
    toast({
      title: 'Connection Error',
      description: 'Check your authentication token',
      variant: 'destructive'
    });
  }
});

if (!isConnected) {
  return <div>Connecting to live feed...</div>;
}
```

### Server-Side

```python
try:
    # Process WebSocket message
except WebSocketDisconnect:
    manager.disconnect(websocket)
except JWTError:
    await websocket.close(code=4001, reason="Invalid authentication")
except Exception as e:
    logger.error(f"WebSocket error: {e}")
    manager.disconnect(websocket)
```

## Testing

### Manual Testing

```bash
# Get authentication token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token'

# Test WebSocket with token
wscat -c "ws://localhost:8000/ws/trades?token=YOUR_TOKEN"

# Send ping
> {"action": "ping"}
< {"type":"pong","timestamp":"..."}
```

### Load Testing

```bash
# Generate multiple WebSocket connections
for i in {1..100}; do
  wscat -c "ws://api.example.com/ws/trades?token=$TOKEN" &
done

# Monitor connection manager stats
curl http://localhost:8000/health
```

## Monitoring

### Prometheus Metrics

Add to backend:
```python
from prometheus_client import Counter, Gauge, Histogram

ws_connections = Gauge('websocket_connections_total', 'Total active WebSocket connections')
ws_messages = Counter('websocket_messages_total', 'Total WebSocket messages sent')
brain_decisions = Counter('brain_decisions_total', 'Total AI decisions made')
```

### Grafana Dashboards

Create dashboard with:
- Real-time connection count
- Messages per second (by type)
- Average decision confidence
- Error rate by endpoint
- Redis pubsub lag

## Performance Tips

1. **Batch Updates**: Group decisions by symbol before sending
2. **Compression**: Enable WebSocket compression
3. **Caching**: Cache analytics response for 10-30 seconds
4. **Pagination**: Limit recent_decisions to 20 items
5. **Debouncing**: Don't send updates faster than 1/sec

## Troubleshooting

### WebSocket Not Connecting

- [ ] Token present in localStorage
- [ ] Token not expired (check `exp` claim)
- [ ] WebSocket URL correct (wss:// for HTTPS)
- [ ] Firewall allows WebSocket traffic
- [ ] Server logs show no JWT errors

### No Real-Time Updates

- [ ] Redis pubsub listener started
- [ ] Brain decisions being created (check DB)
- [ ] Redis publish working (`redis-cli PUBLISH...`)
- [ ] Channel names match (e.g., `trades:user:123`)

### High Latency

- [ ] Check network tab for slow messages
- [ ] Reduce analytics refresh interval
- [ ] Batch multiple updates
- [ ] Scale backend replicas with HPA
