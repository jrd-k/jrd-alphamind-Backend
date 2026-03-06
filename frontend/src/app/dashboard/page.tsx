'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';
import { AccountBalance } from '@/types';
import { Bot, TrendingUp, Zap, Target, Activity, BarChart3 } from 'lucide-react';

export default function DashboardPage() {
  const { user, isAuthenticated } = useAuthStore();
  const [balance, setBalance] = useState<AccountBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(false);
  const [botActive, setBotActive] = useState(true);

  // Mock data for demo mode
  const mockBalance: AccountBalance = {
    balance: 50000,
    currency: 'USD',
    available: 45000,
  };

  const mockStats = {
    todayPnL: 1250,
    winRate: 68,
    activePositions: 5,
    todayTrades: 12,
    monthlyReturn: 12.5,
    sharpeRatio: 1.85,
  };

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchBalance = async () => {
      try {
        const response = await api.get('/api/v1/accounts/balance');
        setBalance(response.data);
        setDemoMode(false);
      } catch (error: any) {
        const isNetworkError = !error.response || error.message === 'Network Error';
        const is404or422 = error.response?.status === 404 || error.response?.status === 422;
        
        if (isNetworkError || is404or422) {
          console.log('Using demo mode for dashboard');
          setBalance(mockBalance);
          setDemoMode(true);
        } else {
          console.error('Failed to fetch balance:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <div className="text-white">Please log in to access the dashboard.</div>;
  }

  return (
    <div className="space-y-6 pb-24 md:pb-8">
      {/* Header with Bot Status */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl md:text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
            Trading Bot
          </h1>
          <p className="text-xs md:text-sm text-slate-400">AI-Powered Trading</p>
        </div>
        <div className="flex items-center gap-3 bg-gradient-to-r from-slate-800 to-slate-900 px-4 md:px-6 py-3 rounded-lg border border-green-500/30 w-full">
          <div className="relative">
            <Bot className="h-6 md:h-8 w-6 md:w-8 text-green-400 animate-pulse" />
            <div className="absolute inset-0 bg-green-400/20 rounded-full animate-pulse"></div>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-slate-400">Status</p>
            <p className="text-base md:text-lg font-bold text-green-400">Active</p>
          </div>
        </div>
      </div>

      {demoMode && (
        <div className="bg-blue-500/10 border border-blue-500/30 text-blue-300 px-4 py-3 rounded-lg">
          <p className="text-sm">
            <strong>Demo Mode:</strong> Using mock data. Connect backend API to see real trading data.
          </p>
        </div>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-6">
        {/* Total Balance */}
        <div className="premium-card p-4 md:p-8 rounded-xl border-2 border-blue-500/20 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/20">
          <div className="flex items-center justify-between mb-2 md:mb-4">
            <h3 className="text-xs md:text-sm font-semibold text-slate-400 uppercase tracking-wider">Balance</h3>
            <Zap className="h-4 md:h-5 w-4 md:w-5 text-yellow-400" />
          </div>
          {loading ? (
            <div className="animate-pulse h-8 bg-slate-700 rounded"></div>
          ) : (
            <>
              <p className="text-xl md:text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                ${balance?.balance?.toFixed(0) || '0'}
              </p>
              <p className="text-xs text-slate-500 mt-1">USD</p>
            </>
          )}
        </div>

        {/* Available Funds */}
        <div className="premium-card p-4 md:p-8 rounded-xl border-2 border-purple-500/20 hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/20">
          <div className="flex items-center justify-between mb-2 md:mb-4">
            <h3 className="text-xs md:text-sm font-semibold text-slate-400 uppercase tracking-wider">Available</h3>
            <Target className="h-4 md:h-5 w-4 md:w-5 text-purple-400" />
          </div>
          {loading ? (
            <div className="animate-pulse h-8 bg-slate-700 rounded"></div>
          ) : (
            <>
              <p className="text-xl md:text-3xl font-bold text-purple-300">
                ${balance?.available?.toFixed(0) || '0'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Ready</p>
            </>
          )}
        </div>

        {/* Today's P&L */}
        <div className="premium-card p-4 md:p-8 rounded-xl border-2 border-green-500/20 hover:border-green-500/50 hover:shadow-lg hover:shadow-green-500/20 col-span-2 md:col-span-1">
          <div className="flex items-center justify-between mb-2 md:mb-4">
            <h3 className="text-xs md:text-sm font-semibold text-slate-400 uppercase tracking-wider">P&L</h3>
            <TrendingUp className="h-4 md:h-5 w-4 md:w-5 text-green-400" />
          </div>
          <p className="text-xl md:text-3xl font-bold text-green-400">
            +${mockStats.todayPnL.toFixed(0)}
          </p>
          <p className="text-xs text-green-400/70 mt-1">+2.5%</p>
        </div>
      </div>

      {/* AI Trading Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
        {/* Win Rate */}
        <div className="premium-card p-3 md:p-6 rounded-lg border border-blue-500/20 hover:border-blue-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">WIN RATE</p>
          <p className="text-xl md:text-2xl font-bold text-blue-400">{mockStats.winRate}%</p>
          <div className="mt-3 h-1 bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600" style={{ width: `${mockStats.winRate}%` }}></div>
          </div>
        </div>

        {/* Active Positions */}
        <div className="premium-card p-3 md:p-6 rounded-lg border border-purple-500/20 hover:border-purple-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">ACTIVE POS</p>
          <p className="text-xl md:text-2xl font-bold text-purple-400">{mockStats.activePositions}</p>
          <p className="text-xs text-slate-500 mt-3">Currently trading</p>
        </div>

        {/* Today's Trades */}
        <div className="premium-card p-3 md:p-6 rounded-lg border border-orange-500/20 hover:border-orange-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">TODAY TRADES</p>
          <p className="text-xl md:text-2xl font-bold text-orange-400">{mockStats.todayTrades}</p>
          <p className="text-xs text-slate-500 mt-3">AI executed</p>
        </div>

        {/* Monthly Return */}
        <div className="premium-card p-3 md:p-6 rounded-lg border border-green-500/20 hover:border-green-500/40">
          <p className="text-xs font-semibold text-slate-400 mb-2">MONTH RTN</p>
          <p className="text-xl md:text-2xl font-bold text-green-400">+{mockStats.monthlyReturn}%</p>
          <p className="text-xs text-slate-500 mt-3">YTD avg</p>
        </div>
      </div>

      {/* AI Performance Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 md:gap-6">
        {/* AI Performance */}
        <div className="lg:col-span-2 premium-card p-4 md:p-8 rounded-xl border border-blue-500/20">
          <div className="flex items-center gap-2 mb-4 md:mb-6">
            <Activity className="h-5 md:h-6 w-5 md:w-6 text-blue-400" />
            <h2 className="text-lg md:text-xl font-bold text-white">AI Performance</h2>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Win/Loss Ratio</span>
                <span className="text-sm font-bold text-blue-300">1.8:1</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full w-[72%] bg-gradient-to-r from-green-400 to-blue-400"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Sharpe Ratio</span>
                <span className="text-sm font-bold text-purple-300">{mockStats.sharpeRatio}</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full w-[85%] bg-gradient-to-r from-purple-400 to-pink-400"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Max Drawdown</span>
                <span className="text-sm font-bold text-yellow-300">-3.2%</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full w-[32%] bg-gradient-to-r from-yellow-400 to-orange-400"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="premium-card p-4 md:p-8 rounded-xl border border-purple-500/20">
          <h2 className="text-lg md:text-xl font-bold text-white mb-4 md:mb-6 flex items-center gap-2">
            <Zap className="h-5 md:h-6 w-5 md:w-6 text-purple-400" />
            Actions
          </h2>
          <div className="space-y-2 md:space-y-3">
            <button className="w-full py-3 px-4 rounded-lg font-semibold bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-500 hover:to-blue-600 transition-all">
              New Trade
            </button>
            <button className="w-full py-3 px-4 rounded-lg font-semibold bg-gradient-to-r from-purple-600 to-purple-700 text-white hover:from-purple-500 hover:to-purple-600 transition-all">
              AI Analysis
            </button>
            <button className="w-full py-3 px-4 rounded-lg font-semibold border border-slate-500 text-slate-300 hover:border-slate-400 hover:text-slate-100 transition-all">
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-6">
        <div className="premium-card p-4 md:p-8 rounded-xl border border-blue-500/20">
          <div className="flex items-center gap-2 md:gap-3 mb-3 md:mb-4">
            <BarChart3 className="h-5 md:h-6 w-5 md:w-6 text-blue-400" />
            <h3 className="text-base md:text-lg font-bold text-white">Risk Management</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Risk/Trade</span>
              <span className="text-white font-semibold">2%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Max Loss</span>
              <span className="text-white font-semibold">$1K</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Stop Loss</span>
              <span className="text-white font-semibold">Auto</span>
            </div>
          </div>
        </div>

        <div className="premium-card p-4 md:p-8 rounded-xl border border-purple-500/20">
          <div className="flex items-center gap-2 md:gap-3 mb-3 md:mb-4">
            <Target className="h-5 md:h-6 w-5 md:w-6 text-purple-400" />
            <h3 className="text-base md:text-lg font-bold text-white">Strategy</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Active</span>
              <span className="text-white font-semibold">3</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Performance</span>
              <span className="text-green-400 font-semibold">+18.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Rebalance</span>
              <span className="text-white font-semibold">2h</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}