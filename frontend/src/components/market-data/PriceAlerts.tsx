'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Bell, X, Check } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';

interface PriceAlert {
  id: string;
  symbol: string;
  type: 'above' | 'below';
  price: number;
  currentPrice: number;
  triggered: boolean;
}

interface PriceAlertsProps {
  alerts: PriceAlert[];
  currentPrice: number;
  symbol: string;
  onAddAlert: (symbol: string, type: 'above' | 'below', price: number) => void;
  onRemoveAlert: (id: string) => void;
}

export function PriceAlerts({
  alerts,
  currentPrice,
  symbol,
  onAddAlert,
  onRemoveAlert,
}: PriceAlertsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [alertType, setAlertType] = useState<'above' | 'below'>('above');
  const [alertPrice, setAlertPrice] = useState('');

  const handleAddAlert = () => {
    if (alertPrice && !isNaN(parseFloat(alertPrice))) {
      onAddAlert(symbol, alertType, parseFloat(alertPrice));
      setAlertPrice('');
      setIsOpen(false);
    }
  };

  const symbolAlerts = alerts.filter(a => a.symbol === symbol);

  const isTriggered = (alert: PriceAlert) => {
    if (alert.type === 'above') {
      return currentPrice >= alert.price;
    } else {
      return currentPrice <= alert.price;
    }
  };

  return (
    <>
      <div className="bg-white p-4 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Bell className="h-5 w-5 mr-2" />
            Price Alerts
          </h3>
          <Button size="sm" onClick={() => setIsOpen(true)}>
            Add Alert
          </Button>
        </div>

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {symbolAlerts.length === 0 ? (
            <p className="text-sm text-gray-500">No price alerts set</p>
          ) : (
            symbolAlerts.map((alert) => {
              const triggered = isTriggered(alert);
              return (
                <div
                  key={alert.id}
                  className={`p-3 rounded-md border ${
                    triggered
                      ? 'bg-yellow-50 border-yellow-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium">
                        Alert when {symbol} is {alert.type === 'above' ? 'above' : 'below'} ${alert.price.toFixed(4)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Current: ${currentPrice.toFixed(4)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {triggered && (
                        <div className="flex items-center text-yellow-600 bg-yellow-100 px-2 py-1 rounded text-xs font-medium">
                          <Check className="h-3 w-3 mr-1" />
                          Triggered
                        </div>
                      )}
                      <button
                        onClick={() => onRemoveAlert(alert.id)}
                        className="text-gray-400 hover:text-red-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Add Price Alert">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alert Type
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  checked={alertType === 'above'}
                  onChange={() => setAlertType('above')}
                  className="h-4 w-4 text-blue-600"
                />
                <span className="ml-2 text-sm text-gray-700">Notify when price goes above</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  checked={alertType === 'below'}
                  onChange={() => setAlertType('below')}
                  className="h-4 w-4 text-blue-600"
                />
                <span className="ml-2 text-sm text-gray-700">Notify when price goes below</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Price
            </label>
            <input
              type="number"
              step="0.0001"
              value={alertPrice}
              onChange={(e) => setAlertPrice(e.target.value)}
              placeholder={`Current price: $${currentPrice.toFixed(4)}`}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleAddAlert}>
              Create Alert
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}