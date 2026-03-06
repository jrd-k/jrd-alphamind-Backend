'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';
import { Trade } from '@/types';
import { Button } from '@/components/ui/Button';
import { TradeList } from '@/components/trades/TradeList';
import { TradeStats } from '@/components/trades/TradeStats';
import { DataTable, Column } from '@/components/ui/DataTable';

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'open' | 'closed'>('all');
  const [viewMode, setViewMode] = useState<'list' | 'table'>('table');
  const [demoMode, setDemoMode] = useState(false);
  const { socket, isConnected } = useWebSocketContext();

  const mockTrades: Trade[] = [
    { id: 1, order_id: 1, symbol: 'EURUSD', side: 'buy', quantity: 1, price: 1.0850, executed_at: new Date(Date.now() - 3600000 * 2).toISOString(), pnl: 50 },
    { id: 2, order_id: 2, symbol: 'GBPUSD', side: 'sell', quantity: 1, price: 1.2850, executed_at: new Date(Date.now() - 3600000).toISOString(), pnl: -25 },
    { id: 3, order_id: 3, symbol: 'USDJPY', side: 'buy', quantity: 1, price: 110.50, executed_at: new Date(Date.now() - 1800000).toISOString(), pnl: 100 },
  ];

  const fetchTrades = async () => {
    try {
      const response = await api.get('/api/v1/trades');
      setTrades(response.data);
      setDemoMode(false);
    } catch (error: any) {
      const isNetworkError = !error.response || error.message === 'Network Error';
      const is404or422 = error.response?.status === 404 || error.response?.status === 422;
      
      if (isNetworkError || is404or422) {
        console.log('Using demo mode for trades');
        setTrades(mockTrades);
        setDemoMode(true);
      } else {
        console.error('Failed to fetch trades:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrades();
  }, []);

  // WebSocket real-time trade updates
  useEffect(() => {
    if (!socket || !isConnected) return;

    const handleNewTrade = (trade: Trade) => {
      setTrades(prev => [trade, ...prev]);
    };

    const handleTradeUpdate = (updatedTrade: Trade) => {
      setTrades(prev => prev.map(trade =>
        trade.id === updatedTrade.id ? updatedTrade : trade
      ));
    };

    socket.on('new_trade', handleNewTrade);
    socket.on('trade_update', handleTradeUpdate);

    return () => {
      socket.off('new_trade', handleNewTrade);
      socket.off('trade_update', handleTradeUpdate);
    };
  }, [socket, isConnected]);

  const filteredTrades = trades.filter((trade) => {
    if (filter === 'all') return true;
    // For now, assume all trades are closed. In a real app, you'd have an 'open' field
    return filter === 'closed';
  });

  const totalPnL = trades.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
  const winningTrades = trades.filter(trade => (trade.pnl || 0) > 0).length;
  const winRate = trades.length > 0 ? (winningTrades / trades.length) * 100 : 0;

  const tradeColumns: Column<Trade>[] = [
    {
      key: 'symbol',
      header: 'Symbol',
      sortable: true,
    },
    {
      key: 'side',
      header: 'Side',
      sortable: true,
      render: (value) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          value === 'buy' ? 'bg-green-500/20 text-green-300 border border-green-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30'
        }`}>
          {value?.toUpperCase()}
        </span>
      ),
    },
    {
      key: 'quantity',
      header: 'Quantity',
      sortable: true,
    },
    {
      key: 'price',
      header: 'Price',
      sortable: true,
      render: (value) => `$${value?.toFixed(5)}`,
    },
    {
      key: 'pnl',
      header: 'P&L',
      sortable: true,
      render: (value) => (
        <span className={value >= 0 ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold'}>
          {value >= 0 ? '+' : ''}${value?.toFixed(2)}
        </span>
      ),
    },
    {
      key: 'executed_at',
      header: 'Time',
      sortable: true,
      render: (value) => new Date(value).toLocaleString(),
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent mb-2">
            📊 Executed Trades
          </h1>
          <p className="text-slate-400">Live trade history and performance</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={fetchTrades}
            className="border border-slate-500 text-slate-300 hover:border-slate-400"
            variant="outline"
          >
            Refresh
          </Button>
          <div className="flex border border-slate-500 rounded-lg overflow-hidden bg-slate-800/50">
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 text-sm font-medium transition-all ${
                viewMode === 'table'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                  : 'text-slate-300 hover:text-slate-100'
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 text-sm font-medium transition-all ${
                viewMode === 'list'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                  : 'text-slate-300 hover:text-slate-100'
              }`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {demoMode && (
        <div className="bg-blue-500/10 border border-blue-500/30 text-blue-300 px-4 py-3 rounded-lg">
          <p className="text-sm">
            <strong>Demo Mode:</strong> Using mock trade data. Connect backend API to see real trades.
          </p>
        </div>
      )}

      {/* Trade Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="premium-card p-6 rounded-lg border border-blue-500/20 hover:border-blue-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">TOTAL TRADES</p>
          <p className="text-3xl font-bold text-blue-400">{trades.length}</p>
          <p className="text-xs text-slate-500 mt-2">All time</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-green-500/20 hover:border-green-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">TOTAL P&L</p>
          <p className={`text-3xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
          </p>
          <p className="text-xs text-slate-500 mt-2">Profit/Loss</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-purple-500/20 hover:border-purple-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">WIN RATE</p>
          <p className="text-3xl font-bold text-purple-400">{winRate.toFixed(1)}%</p>
          <p className="text-xs text-slate-500 mt-2">{winningTrades} winning</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-yellow-500/20 hover:border-yellow-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">AVG P&L</p>
          <p className="text-3xl font-bold text-yellow-400">
            ${trades.length > 0 ? (totalPnL / trades.length).toFixed(2) : '0.00'}
          </p>
          <p className="text-xs text-slate-500 mt-2">Per trade</p>
        </div>
      </div>

      {/* Trade Filters */}
      <div className="flex gap-2">
        <Button
          size="sm"
          variant={filter === 'all' ? 'primary' : 'outline'}
          onClick={() => setFilter('all')}
          className={filter === 'all' ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 'border border-slate-500 text-slate-300'}
        >
          All Trades
        </Button>
        <Button
          size="sm"
          variant={filter === 'open' ? 'primary' : 'outline'}
          onClick={() => setFilter('open')}
          className={filter === 'open' ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 'border border-slate-500 text-slate-300'}
        >
          Open
        </Button>
        <Button
          size="sm"
          variant={filter === 'closed' ? 'primary' : 'outline'}
          onClick={() => setFilter('closed')}
          className={filter === 'closed' ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 'border border-slate-500 text-slate-300'}
        >
          Closed
        </Button>
      </div>

      {/* Trades Display */}
      <div className="premium-card p-8 rounded-xl border border-blue-500/20">
        <h2 className="text-xl font-bold text-white mb-6">Trade History</h2>

        {viewMode === 'table' ? (
          <DataTable
            data={filteredTrades}
            columns={tradeColumns}
            loading={loading}
            pageSize={15}
            emptyMessage="No trades found"
          />
        ) : (
          loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
            </div>
          ) : (
            <TradeList trades={filteredTrades} />
          )
        )}
      </div>
    </div>
  );
}