'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { X, Plus, Star } from 'lucide-react';

interface WatchlistItem {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

interface WatchlistProps {
  items: WatchlistItem[];
  onAddItem: (symbol: string) => void;
  onRemoveItem: (symbol: string) => void;
  onSelectSymbol: (symbol: string) => void;
  selectedSymbol: string;
}

export function Watchlist({
  items,
  onAddItem,
  onRemoveItem,
  onSelectSymbol,
  selectedSymbol,
}: WatchlistProps) {
  const [newSymbol, setNewSymbol] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const handleAddSymbol = () => {
    if (newSymbol.trim()) {
      onAddItem(newSymbol.toUpperCase());
      setNewSymbol('');
      setShowAddForm(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md h-full">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center">
            <Star className="h-5 w-5 mr-2 text-yellow-400" />
            Watchlist
          </h3>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {showAddForm && (
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
              placeholder="Symbol (e.g., AAPL)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Button size="sm" onClick={handleAddSymbol}>
              Add
            </Button>
          </div>
        )}
      </div>

      <div className="divide-y max-h-96 overflow-y-auto">
        {items.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No items in watchlist
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.symbol}
              className={`p-4 hover:bg-gray-50 cursor-pointer transition ${
                selectedSymbol === item.symbol ? 'bg-blue-50 border-l-4 border-blue-500' : ''
              }`}
              onClick={() => onSelectSymbol(item.symbol)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900">{item.symbol}</h4>
                  <p className="text-sm text-gray-600">${item.price.toFixed(4)}</p>
                </div>
                <div className="text-right flex-1">
                  <p className={`text-sm font-semibold ${
                    item.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {item.change >= 0 ? '+' : ''}{item.change.toFixed(4)}
                  </p>
                  <p className={`text-xs ${
                    item.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemoveItem(item.symbol);
                }}
                className="mt-2 text-xs text-gray-400 hover:text-red-600 flex items-center"
              >
                <X className="h-3 w-3 mr-1" />
                Remove
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}