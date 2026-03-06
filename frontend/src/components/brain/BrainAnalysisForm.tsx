'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface BrainAnalysisFormProps {
  onSubmit: (symbol: string) => void;
  loading: boolean;
}

const POPULAR_SYMBOLS = [
  'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
  'USDCHF', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY'
];

export function BrainAnalysisForm({ onSubmit, loading }: BrainAnalysisFormProps) {
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(selectedSymbol);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Symbol for AI Analysis
        </label>
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        >
          {POPULAR_SYMBOLS.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-blue-50 p-4 rounded-md">
        <h4 className="text-sm font-medium text-blue-800 mb-2">Analysis Includes:</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Technical indicators (RSI, MACD, Fibonacci)</li>
          <li>• Market sentiment analysis</li>
          <li>• AI-powered decision recommendation</li>
          <li>• Confidence scoring</li>
        </ul>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Request Analysis'}
        </Button>
      </div>
    </form>
  );
}