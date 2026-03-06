'use client';

import { Trade } from '@/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PnLChartProps {
  trades: Trade[];
}

export function PnLChart({ trades }: PnLChartProps) {
  // Calculate cumulative P&L over time
  const sortedTrades = [...trades].sort((a, b) =>
    new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
  );

  let cumulativePnL = 0;
  const chartData = sortedTrades.map((trade) => {
    cumulativePnL += trade.pnl || 0;
    return {
      date: new Date(trade.executed_at).toLocaleDateString(),
      pnl: cumulativePnL,
    };
  });

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">P&L Over Time</h2>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip
              formatter={(value: number | undefined) => value !== undefined ? [`$${value.toFixed(2)}`, 'Cumulative P&L'] : ['N/A', 'Cumulative P&L']}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="pnl"
              stroke={cumulativePnL >= 0 ? '#10b981' : '#ef4444'}
              strokeWidth={2}
              dot={{ fill: cumulativePnL >= 0 ? '#10b981' : '#ef4444', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}