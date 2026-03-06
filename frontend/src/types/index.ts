// Auth types
export interface User {
  id: number;
  username: string;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Account types
export interface AccountBalance {
  balance: number;
  currency: string;
  available: number;
}

// Order types
export interface Order {
  id: number;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
  status: 'pending' | 'executed' | 'cancelled';
  created_at: string;
}

export interface OrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
}

// Trade types
export interface Trade {
  id: number;
  order_id: number;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  executed_at: string;
  pnl?: number;
}

// Market data types
export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Quote {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume: number;
}

// Brain decision types
export interface BrainDecision {
  id: number;
  symbol: string;
  decision: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  indicators: Record<string, any>;
  created_at: string;
  // optional extended fields used by UI/demo
  timestamp?: string;
  reasoning?: string;
  targetPrice?: number;
  stopLoss?: number;
}

// Economic calendar types
export interface EconomicEvent {
  id: number;
  title: string;
  country: string;
  date: string;
  impact: 'high' | 'medium' | 'low';
  forecast?: number;
  previous?: number;
  actual?: number;
}

// Position sizing types
export interface PositionSizeRequest {
  account_balance: number;
  risk_percentage: number;
  stop_loss_pips: number;
  symbol: string;
}

export interface PositionSizeResponse {
  position_size: number;
  lot_size: number;
  risk_amount: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  data: any;
}