'use client';

import { useState } from 'react';

interface SymbolSearchProps {
  onSymbolSelect: (symbol: string) => void;
}

const POPULAR_SYMBOLS = [
  'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
  'USDCHF', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY'
];

export function SymbolSearch({ onSymbolSelect }: SymbolSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const filteredSymbols = POPULAR_SYMBOLS.filter(symbol =>
    symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (symbol: string) => {
    onSymbolSelect(symbol);
    setSearchTerm(symbol);
    setIsOpen(false);
  };

  return (
    <div className="relative w-full sm:w-48">
      <input
        type="text"
        placeholder="Search symbol..."
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        className="w-full px-4 py-3 sm:py-2 text-base sm:text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
      />

      {isOpen && (
        <div className="absolute z-10 w-full mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-72 overflow-y-auto">
          {filteredSymbols.map((symbol) => (
            <button
              key={symbol}
              onClick={() => handleSelect(symbol)}
              className="w-full text-left px-4 py-3 sm:py-2 hover:bg-blue-50 active:bg-blue-100 focus:bg-blue-50 focus:outline-none transition-colors"
            >
              <span className="font-medium text-gray-900">{symbol}</span>
            </button>
          ))}
          {filteredSymbols.length === 0 && (
            <div className="px-4 py-3 text-gray-500 text-center">No symbols found</div>
          )}
        </div>
      )}
    </div>
  );
}