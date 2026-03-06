'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Trade } from '@/types';
import { Button } from '@/components/ui/Button';
import { PnLChart } from '@/components/analytics/PnLChart';
import { PerformanceMetrics } from '@/components/analytics/PerformanceMetrics';
import { TradeDistribution } from '@/components/analytics/TradeDistribution';

export default function AnalyticsPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  // sample mock trades for offline/demo mode
  const mockTrades: Trade[] = [
    { id: 1, order_id: 101, symbol: 'EURUSD', side: 'buy', quantity: 1, price: 1.0850, executed_at: new Date(Date.now() - 3600000 * 5).toISOString(), pnl: 25 },
    { id: 2, order_id: 102, symbol: 'GBPUSD', side: 'sell', quantity: 2, price: 1.2850, executed_at: new Date(Date.now() - 3600000 * 3).toISOString(), pnl: -40 },
    { id: 3, order_id: 103, symbol: 'USDJPY', side: 'buy', quantity: 1, price: 110.50, executed_at: new Date(Date.now() - 3600000).toISOString(), pnl: 75 },
  ];

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/trades', {
        params: {
          start_date: dateRange.start,
          end_date: dateRange.end,
        },
      });
      setTrades(response.data);
      setDemoMode(false);
    } catch (error: any) {
      const isNetworkError = !error.response || error.message === 'Network Error';
      const is404or422 = error.response?.status === 404 || error.response?.status === 422;
      if (isNetworkError || is404or422) {
        console.log('Using demo mode for analytics');
        setTrades(mockTrades);
        setDemoMode(true);
      } else {
        console.error('Failed to fetch analytics:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange]);

  const exportData = () => {
    const csvContent = [
      ['Date', 'Symbol', 'Side', 'Quantity', 'Price', 'P&L'],
      ...trades.map(trade => [
        new Date(trade.executed_at).toLocaleDateString(),
        trade.symbol,
        trade.side,
        trade.quantity.toString(),
        trade.price.toString(),
        (trade.pnl || 0).toString(),
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades-${dateRange.start}-to-${dateRange.end}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Analytics & Reporting</h1>
        <Button onClick={exportData} variant="outline">
          Export CSV
        </Button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Date Range</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <Button onClick={fetchAnalytics} className="w-full">
              Apply Filter
            </Button>
          </div>
        </div>
      </div>

      {demoMode && (
        <div className="bg-blue-500/10 border border-blue-500/30 text-blue-300 px-4 py-3 rounded-lg">
          <p className="text-sm">
            <strong>Demo Mode:</strong> Using mock analytics data. Connect backend API for live metrics.
          </p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          <PerformanceMetrics trades={trades} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PnLChart trades={trades} />
            <TradeDistribution trades={trades} />
          </div>
        </>
      )}
    </div>
  );
}