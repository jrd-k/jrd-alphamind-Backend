// Frontend API service for AlphaMind backend integration
// Place this in src/services/api.ts

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
});

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const token = localStorage.getItem('auth_token');

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication
  async login(credentials: { email: string; password: string }) {
    const response = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        username: credentials.email, // Backend uses username
        password: credentials.password,
      }),
    });

    // Store token
    localStorage.setItem('auth_token', response.access_token);
    return response;
  }

  async register(userData: { email: string; password: string }) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username: userData.email,
        password: userData.password,
      }),
    });
  }

  // User Profile
  async getUserProfile() {
    return this.request('/api/user/me');
  }

  // Stock Data
  async getStocks(symbol?: string, interval = 'daily') {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    params.append('interval', interval);

    return this.request(`/api/stocks?${params}`);
  }

  async getStockQuote(symbol: string) {
    return this.request(`/api/v1/marketdata/quote/${symbol}`);
  }

  // Generic Data Submission
  async submitData(data: any) {
    return this.request('/api/data', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Trading Features (Bonus - not in original frontend)
  async getBrainDecision(symbol: string, candles: any[], currentPrice: number) {
    return this.request('/api/v1/brain/decide', {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        candles,
        current_price: currentPrice,
      }),
    });
  }

  async trainMLModel(symbol: string, days = 365) {
    return this.request('/api/v1/ml/train', {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        days,
        force_retrain: true,
      }),
    });
  }

  async getMLPrediction(symbol: string, currentPrice: number) {
    return this.request('/api/v1/ml/predict', {
      method: 'POST',
      body: JSON.stringify({
        symbol,
        current_price: currentPrice,
      }),
    });
  }
}

export const api = new ApiService();