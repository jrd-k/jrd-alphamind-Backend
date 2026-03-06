'use client';

import { Trade } from '@/types';

interface PerformanceMetricsProps {
  trades: Trade[];
}

export function PerformanceMetrics({ trades }: PerformanceMetricsProps) {
  const totalTrades = trades.length;
  const winningTrades = trades.filter(trade => (trade.pnl || 0) > 0).length;
  const losingTrades = totalTrades - winningTrades;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

  const totalPnL = trades.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
  const averageWin = winningTrades > 0
    ? trades.filter(t => (t.pnl || 0) > 0).reduce((sum, t) => sum + (t.pnl || 0), 0) / winningTrades
    : 0;
  const averageLoss = losingTrades > 0
    ? Math.abs(trades.filter(t => (t.pnl || 0) < 0).reduce((sum, t) => sum + (t.pnl || 0), 0) / losingTrades)
    : 0;

  const profitFactor = averageLoss > 0 ? averageWin / averageLoss : 0;

  const maxDrawdown = Math.min(...trades.reduce((acc, trade, index) => {
    const cumulative = trades.slice(0, index + 1).reduce((sum, t) => sum + (t.pnl || 0), 0);
    acc.push(cumulative);
    return acc;
  }, [0]));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Total P&L</h3>
        <p className={`text-3xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          ${totalPnL.toFixed(2)}
        </p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Win Rate</h3>
        <p className="text-3xl font-bold text-blue-600">{winRate.toFixed(1)}%</p>
        <p className="text-sm text-gray-600">{winningTrades}W / {losingTrades}L</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Profit Factor</h3>
        <p className="text-3xl font-bold text-purple-600">{profitFactor.toFixed(2)}</p>
        <p className="text-sm text-gray-600">Avg W/L Ratio</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Max Drawdown</h3>
        <p className="text-3xl font-bold text-red-600">${Math.abs(maxDrawdown).toFixed(2)}</p>
        <p className="text-sm text-gray-600">Peak to Valley</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Average Win</h3>
        <p className="text-3xl font-bold text-green-600">${averageWin.toFixed(2)}</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Average Loss</h3>
        <p className="text-3xl font-bold text-red-600">${averageLoss.toFixed(2)}</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Total Trades</h3>
        <p className="text-3xl font-bold text-gray-600">{totalTrades}</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Best Trade</h3>
        <p className="text-3xl font-bold text-green-600">
          ${Math.max(...trades.map(t => t.pnl || 0), 0).toFixed(2)}
        </p>
      </div>
    </div>
  );
}