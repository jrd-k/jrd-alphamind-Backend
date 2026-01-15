// Example React component showing backend integration
// Place this in src/components/StockChart.tsx

import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { useState } from 'react';

interface StockChartProps {
  symbol: string;
}

export function StockChart({ symbol }: StockChartProps) {
  const [interval, setInterval] = useState('daily');

  // Fetch stock data using React Query
  const { data: stockData, isLoading, error } = useQuery({
    queryKey: ['stocks', symbol, interval],
    queryFn: () => api.getStocks(symbol, interval),
    enabled: !!symbol, // Only run if symbol exists
  });

  // Fetch current quote
  const { data: quote } = useQuery({
    queryKey: ['quote', symbol],
    queryFn: () => api.getStockQuote(symbol),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (isLoading) return <div>Loading stock data...</div>;
  if (error) return <div>Error loading data: {error.message}</div>;

  return (
    <div className="stock-chart">
      <div className="chart-header">
        <h2>{symbol.toUpperCase()}</h2>
        {quote && (
          <div className="quote">
            <span className="price">${quote.price}</span>
            <span className={`change ${quote.change >= 0 ? 'positive' : 'negative'}`}>
              {quote.change >= 0 ? '+' : ''}{quote.change} ({quote.changePercent}%)
            </span>
          </div>
        )}

        <select value={interval} onChange={(e) => setInterval(e.target.value)}>
          <option value="daily">Daily</option>
          <option value="hourly">Hourly</option>
        </select>
      </div>

      {/* Chart rendering with your preferred library */}
      <div className="chart-container">
        {stockData?.data && (
          <pre>{JSON.stringify(stockData.data.slice(0, 5), null, 2)}</pre>
          // Replace with actual chart library (recharts, lightweight-charts, etc.)
        )}
      </div>
    </div>
  );
}

// Example usage in a page component
export function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');

  return (
    <div>
      <select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)}>
        <option value="AAPL">Apple</option>
        <option value="GOOGL">Google</option>
        <option value="MSFT">Microsoft</option>
        <option value="EURUSD">EUR/USD</option>
      </select>

      <StockChart symbol={selectedSymbol} />
    </div>
  );
}