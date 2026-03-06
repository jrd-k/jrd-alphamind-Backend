'use client';

import { Trade } from '@/types';

interface TradeStatsProps {
  totalTrades: number;
  totalPnL: number;
  winRate: number;
  winningTrades: number;
}

export function TradeStats({ totalTrades, totalPnL, winRate, winningTrades }: TradeStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Total Trades</h3>
        <p className="text-3xl font-bold text-blue-600">{totalTrades}</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Total P&L</h3>
        <p className={`text-3xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          ${totalPnL.toFixed(2)}
        </p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Win Rate</h3>
        <p className="text-3xl font-bold text-purple-600">{winRate.toFixed(1)}%</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-2">Winning Trades</h3>
        <p className="text-3xl font-bold text-green-600">{winningTrades}</p>
      </div>
    </div>
  );
}