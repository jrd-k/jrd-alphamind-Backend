'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Candle } from '@/types';

interface ChartComponentProps {
  data: Candle[];
}

export function ChartComponent({ data }: ChartComponentProps) {
  // Transform candle data for line chart (using close prices)
  const chartData = data.map((candle) => ({
    time: new Date(candle.timestamp).toLocaleTimeString(),
    price: candle.close,
    high: candle.high,
    low: candle.low,
    open: candle.open,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={['dataMin - 0.001', 'dataMax + 0.001']}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value: number | undefined) => value !== undefined ? [`$${value.toFixed(5)}`, 'Price'] : ['N/A', 'Price']}
          labelFormatter={(label) => `Time: ${label}`}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}