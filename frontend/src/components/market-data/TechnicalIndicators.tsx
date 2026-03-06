'use client';

import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';

interface IndicatorDataPoint {
  timestamp: number;
  rsi: number;
  macd: number;
  macdSignal: number;
  macdHistogram: number;
  sma20: number;
  sma50: number;
  sma200: number;
}

interface TechnicalIndicatorsProps {
  data: IndicatorDataPoint[];
  selectedIndicators: {
    rsi: boolean;
    macd: boolean;
    sma: boolean;
  };
  onIndicatorToggle: (indicator: 'rsi' | 'macd' | 'sma') => void;
}

export function TechnicalIndicators({ data, selectedIndicators, onIndicatorToggle }: TechnicalIndicatorsProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <p className="text-gray-500">No indicator data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Indicator Controls */}
      <div className="bg-white p-4 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-3">Technical Indicators</h3>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={selectedIndicators.rsi}
              onChange={() => onIndicatorToggle('rsi')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">RSI (Relative Strength Index)</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={selectedIndicators.macd}
              onChange={() => onIndicatorToggle('macd')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">MACD (Moving Average Convergence)</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={selectedIndicators.sma}
              onChange={() => onIndicatorToggle('sma')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">Moving Averages (20, 50, 200)</span>
          </label>
        </div>
      </div>

      {/* RSI Indicator */}
      {selectedIndicators.rsi && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h4 className="text-lg font-semibold mb-4">RSI (Relative Strength Index)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorRsi" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value).toLocaleTimeString()}
              />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value: any) => value?.toFixed(2)}
                labelFormatter={(label) => new Date(label).toLocaleString()}
              />
              <Area 
                type="monotone" 
                dataKey="rsi" 
                stroke="#8884d8" 
                fillOpacity={1} 
                fill="url(#colorRsi)"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200 text-sm text-gray-700">
            <p><strong>RSI Usage:</strong> Values above 70 indicate overbought conditions, below 30 indicate oversold conditions. Range: 0-100</p>
          </div>
        </div>
      )}

      {/* MACD Indicator */}
      {selectedIndicators.macd && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h4 className="text-lg font-semibold mb-4">MACD (Moving Average Convergence Divergence)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={data}>
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value).toLocaleTimeString()}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: any) => value?.toFixed(4)}
                labelFormatter={(label) => new Date(label).toLocaleString()}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="macd" 
                stroke="#8884d8" 
                dot={false}
                name="MACD"
              />
              <Line 
                type="monotone" 
                dataKey="macdSignal" 
                stroke="#82ca9d" 
                dot={false}
                name="Signal Line"
              />
              <Area 
                type="monotone" 
                dataKey="macdHistogram" 
                fill="#ffc658" 
                stroke="none"
                name="Histogram"
              />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200 text-sm text-gray-700">
            <p><strong>MACD Usage:</strong> A momentum indicator showing relationship between two moving averages. Crossovers signal buy/sell opportunities.</p>
          </div>
        </div>
      )}

      {/* Moving Averages */}
      {selectedIndicators.sma && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h4 className="text-lg font-semibold mb-4">Simple Moving Averages</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data}>
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value).toLocaleTimeString()}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: any) => value?.toFixed(5)}
                labelFormatter={(label) => new Date(label).toLocaleString()}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="sma20" 
                stroke="#ff7300" 
                dot={false}
                name="SMA 20"
              />
              <Line 
                type="monotone" 
                dataKey="sma50" 
                stroke="#1f77b4" 
                dot={false}
                name="SMA 50"
              />
              <Line 
                type="monotone" 
                dataKey="sma200" 
                stroke="#d62728" 
                dot={false}
                name="SMA 200"
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200 text-sm text-gray-700">
            <p><strong>Moving Averages Usage:</strong> SMA 20 (short-term), SMA 50 (medium-term), SMA 200 (long-term). Price above MAs indicates uptrend, below indicates downtrend.</p>
          </div>
        </div>
      )}
    </div>
  );
}