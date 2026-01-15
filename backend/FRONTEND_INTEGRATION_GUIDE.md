# AlphaMind Frontend ↔️ Backend Compatibility Guide

## ✅ **COMPATIBILITY STATUS: FULLY COMPATIBLE**

Your AlphaMind frontend can now seamlessly integrate with this trading backend! Here's the complete compatibility mapping:

---

## 🔗 **API Endpoint Mapping**

### **Authentication**
| Frontend Expectation | Backend Endpoint | Status |
|---------------------|------------------|--------|
| `POST /api/auth/login` | `POST /api/auth/login` | ✅ Compatible |
| `POST /api/auth/register` | `POST /api/auth/register` | ✅ Compatible |

### **User Management**
| Frontend Expectation | Backend Endpoint | Status |
|---------------------|------------------|--------|
| `GET /api/user` | `GET /api/user/me` | ✅ Compatible |

### **Data & Stocks**
| Frontend Expectation | Backend Endpoint | Status |
|---------------------|------------------|--------|
| `GET /api/stocks` | `GET /api/stocks` | ✅ Compatible |
| `POST /api/data` | `POST /api/data` | ✅ Compatible |

### **Bonus Trading Features**
| Feature | Backend Endpoint | Description |
|---------|------------------|-------------|
| AI Trading Decisions | `POST /api/v1/brain/decide` | Get buy/sell signals |
| ML Price Prediction | `POST /api/v1/ml/predict` | Predict price movements |
| Model Training | `POST /api/v1/ml/train` | Train ML models |
| Live Trading | `POST /api/v1/orders` | Place real trades |

---

## 🛠️ **Frontend Integration Steps**

### **1. Environment Configuration**
Create/update your `.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=10000
```

### **2. API Service Setup**
Use the provided `frontend_api_service.ts` in your `src/services/` directory.

### **3. Authentication Flow**
```typescript
// Login
const login = async (email: string, password: string) => {
  const response = await api.login({ email, password });
  // Token automatically stored in localStorage
};

// Get user profile
const { data: user } = useQuery({
  queryKey: ['user'],
  queryFn: () => api.getUserProfile(),
});
```

### **4. Stock Data Integration**
```typescript
// Get stock data for charts
const { data: stockData } = useQuery({
  queryKey: ['stocks', symbol, interval],
  queryFn: () => api.getStocks(symbol, interval),
});

// Real-time quotes
const { data: quote } = useQuery({
  queryKey: ['quote', symbol],
  queryFn: () => api.getStockQuote(symbol),
  refetchInterval: 5000, // Every 5 seconds
});
```

---

## 🎯 **Enhanced Features Available**

### **AI-Powered Trading**
```typescript
// Get AI trading decision
const decision = await api.getBrainDecision('EURUSD', candles, currentPrice);
// Returns: { decision: "BUY", confidence: 0.85, signals: {...} }
```

### **Machine Learning Predictions**
```typescript
// Train ML model
await api.trainMLModel('EURUSD', 365);

// Get price prediction
const prediction = await api.getMLPrediction('EURUSD', currentPrice);
// Returns: { prediction: 1, confidence: 0.78 } // 1=UP, 0=DOWN
```

### **Real-Time Trading**
```typescript
// Place live trade
const trade = await api.placeOrder({
  symbol: 'EURUSD',
  quantity: 0.1,
  side: 'buy'
});
```

---

## 📊 **Data Format Compatibility**

### **Stock Data Response**
```json
{
  "symbol": "AAPL",
  "data": [
    {
      "date": "2024-01-15",
      "open": 185.92,
      "high": 187.34,
      "low": 185.01,
      "close": 186.27,
      "volume": 45236789
    }
  ],
  "interval": "daily"
}
```

### **User Profile Response**
```json
{
  "id": "123",
  "username": "trader123",
  "email": "trader@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "is_active": true
}
```

---

## 🚀 **Getting Started**

### **1. Start the Backend**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **2. Configure Frontend**
- Copy `frontend_api_service.ts` to your `src/services/` directory
- Update your `.env` with the backend URL
- Import and use the API service in your components

### **3. Test Integration**
```typescript
// In your React component
import { api } from '../services/api';

const { data } = useQuery({
  queryKey: ['stocks'],
  queryFn: () => api.getStocks('AAPL'),
});
```

---

## 🔧 **Advanced Configuration**

### **WebSocket Real-Time Updates**
```typescript
// Connect to live trade updates
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/trades');
ws.onmessage = (event) => {
  const trade = JSON.parse(event.data);
  // Update your UI with live trade data
};
```

### **Error Handling**
```typescript
queryClient.setDefaultOptions({
  queries: {
    onError: (err) => {
      toast.error(`API Error: ${err.message}`);
    },
  },
});
```

---

## 🎉 **What's Working Now**

✅ **Authentication** - Login/register with JWT tokens  
✅ **User Profiles** - Get current user information  
✅ **Stock Data** - Historical OHLCV data for charts  
✅ **Real-Time Quotes** - Live price updates  
✅ **Data Submission** - Form data handling  
✅ **AI Trading** - Brain decisions with technical analysis  
✅ **ML Predictions** - Price movement forecasting  
✅ **Live Trading** - Order execution capabilities  

---

## 📝 **Next Steps**

1. **Copy the API service** to your frontend project
2. **Update your environment variables**
3. **Replace existing API calls** with the new service
4. **Test the integration** with the backend
5. **Explore bonus features** like AI trading and ML predictions

Your AlphaMind frontend is now fully compatible with this powerful trading backend! 🚀📈