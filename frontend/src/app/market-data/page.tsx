'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';
import { Candle, EconomicEvent } from '@/types';
import { Button } from '@/components/ui/Button';
import { TradingViewChart } from '@/components/market-data/TradingViewChart';
import { SymbolSearch } from '@/components/market-data/SymbolSearch';
import { QuoteDisplay } from '@/components/market-data/QuoteDisplay';
import { EconomicEventCard } from '@/components/economic-calendar/EconomicEventCard';

const TIMEFRAMES = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1d', value: '1d' },
];

export default function MarketDataPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [candles, setCandles] = useState<Candle[]>([]);
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [economicEvents, setEconomicEvents] = useState<EconomicEvent[]>([]);
  const { socket, isConnected } = useWebSocketContext();

  // Mock data
  const mockCandles: Candle[] = [
    { timestamp: Date.now() - 3600000 * 4, open: 1.0800, high: 1.0850, low: 1.0750, close: 1.0820, volume: 1000 },
    { timestamp: Date.now() - 3600000 * 3, open: 1.0820, high: 1.0900, low: 1.0800, close: 1.0880, volume: 1200 },
    { timestamp: Date.now() - 3600000 * 2, open: 1.0880, high: 1.0920, low: 1.0850, close: 1.0900, volume: 1100 },
    { timestamp: Date.now() - 3600000, open: 1.0900, high: 1.0950, low: 1.0880, close: 1.0920, volume: 950 },
  ];

  const mockQuote = {
    symbol: selectedSymbol,
    bid: 1.0918,
    ask: 1.0920,
    last: 1.0919,
    change: 0.0050,
    changePercent: 0.46,
  };

  const fetchCandles = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/stocks', {
        params: {
          symbol: selectedSymbol,
          interval: selectedTimeframe,
          limit: 100,
        },
      });
      setCandles(response.data.data || response.data);
      setDemoMode(false);
    } catch (error: any) {
      const isNetworkError = !error.response || error.message === 'Network Error';
      const is404or422 = error.response?.status === 404 || error.response?.status === 422;
      
      if (isNetworkError || is404or422) {
        console.log('Using demo mode for market data');
        setCandles(mockCandles);
        setDemoMode(true);
      } else {
        console.error('Failed to fetch candles:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchQuote = async () => {
    try {
      const response = await api.get(`/api/v1/marketdata/quote/${selectedSymbol}`);
      setQuote(response.data);
      setDemoMode(false);
    } catch (error: any) {
      const isNetworkError = !error.response || error.message === 'Network Error';
      const is404or422 = error.response?.status === 404 || error.response?.status === 422;
      
      if (isNetworkError || is404or422) {
        setQuote(mockQuote);
        setDemoMode(true);
      } else {
        console.error('Failed to fetch quote:', error);
      }
    }
  };

  const fetchEconomicEvents = async () => {
    try {
      const response = await api.get('/api/v1/economic-calendar/upcoming', {
        params: { hours_ahead: 24, limit: 5 }
      });
      setEconomicEvents(response.data.items || response.data);
    } catch (error) {
      console.error('Failed to fetch economic events:', error);
      // Use mock events if API fails
      setEconomicEvents([
        {
          id: 1,
          title: 'Non-Farm Payrolls',
          country: 'US',
          date: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
          impact: 'high',
          forecast: 200,
          previous: 150,
        },
        {
          id: 2,
          title: 'GDP Growth',
          country: 'EU',
          date: new Date(Date.now() + 7200000).toISOString(), // 2 hours from now
          impact: 'medium',
          forecast: 0.3,
          previous: 0.2,
        },
      ]);
    }
  };

  useEffect(() => {
    if (selectedSymbol) {
      fetchCandles();
      fetchQuote();
    }
    fetchEconomicEvents();
  }, [selectedSymbol, selectedTimeframe]);

  // WebSocket real-time updates
  useEffect(() => {
    if (!socket || !isConnected) return;

    const handlePriceUpdate = (data: any) => {
      if (data.symbol === selectedSymbol) {
        setQuote((prev: any) => prev ? { ...prev, ...data } : data);
      }
    };

    const handleCandleUpdate = (data: any) => {
      if (data.symbol === selectedSymbol && data.timeframe === selectedTimeframe) {
        setCandles(prev => {
          const newCandles = [...prev];
          const lastCandle = newCandles[newCandles.length - 1];
          if (lastCandle && lastCandle.timestamp === data.timestamp) {
            // Update last candle
            newCandles[newCandles.length - 1] = data;
          } else {
            // Add new candle
            newCandles.push(data);
            // Keep only last 100 candles
            if (newCandles.length > 100) {
              newCandles.shift();
            }
          }
          return newCandles;
        });
      }
    };

    socket.on('price_update', handlePriceUpdate);
    socket.on('candle_update', handleCandleUpdate);

    // Subscribe to symbol updates
    socket.emit('subscribe_symbol', { symbol: selectedSymbol, timeframe: selectedTimeframe });

    return () => {
      socket.off('price_update', handlePriceUpdate);
      socket.off('candle_update', handleCandleUpdate);
      socket.emit('unsubscribe_symbol', { symbol: selectedSymbol, timeframe: selectedTimeframe });
    };
  }, [socket, isConnected, selectedSymbol, selectedTimeframe]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Market Data</h1>
        <SymbolSearch onSymbolSelect={setSelectedSymbol} />
      </div>

      {demoMode && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded">
          <p className="text-sm">
            <strong>Demo Mode:</strong> Using mock data. Connect backend API to see real market data.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">
                {selectedSymbol} - {selectedTimeframe}
              </h2>
              <div className="flex space-x-2">
                {TIMEFRAMES.map((tf) => (
                  <Button
                    key={tf.value}
                    variant={selectedTimeframe === tf.value ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedTimeframe(tf.value)}
                  >
                    {tf.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="h-96">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <TradingViewChart symbol={selectedSymbol} timeframe={selectedTimeframe} height="100%" />
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <QuoteDisplay quote={quote} symbol={selectedSymbol} />

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Watchlist</h3>
            <div className="space-y-2">
              {['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'].map((symbol) => (
                <button
                  key={symbol}
                  onClick={() => setSelectedSymbol(symbol)}
                  className={`w-full text-left p-2 rounded ${
                    selectedSymbol === symbol
                      ? 'bg-blue-100 text-blue-800'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {symbol}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Upcoming Economic Events</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {economicEvents.length > 0 ? (
                economicEvents.map((event, index) => (
                  <EconomicEventCard 
                    key={event.id ? `event-${event.id}` : `event-${event.title}-${event.date}-${index}`} 
                    event={event} 
                  />
                ))
              ) : (
                <p className="text-gray-500 text-sm">No upcoming events</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}