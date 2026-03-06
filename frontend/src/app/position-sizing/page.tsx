'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { AccountBalance } from '@/types';
import { Button } from '@/components/ui/Button';
import { PositionSizeCalculator } from '@/components/position-sizing/PositionSizeCalculator';
import { RiskManagementPanel } from '@/components/position-sizing/RiskManagementPanel';

export default function PositionSizingPage() {
  const [balance, setBalance] = useState<AccountBalance | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const response = await api.get('/api/v1/accounts/balance');
        setBalance(response.data);
      } catch (error) {
        console.error('Failed to fetch balance:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Position Sizing & Risk Management</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Account Overview</h2>
            {loading ? (
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded"></div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Balance:</span>
                  <span className="font-semibold">${balance?.balance?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Available:</span>
                  <span className="font-semibold">${balance?.available?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Currency:</span>
                  <span className="font-semibold">{balance?.currency || 'USD'}</span>
                </div>
              </div>
            )}
          </div>

          <PositionSizeCalculator accountBalance={balance?.balance || 0} />
        </div>

        <div className="space-y-6">
          <RiskManagementPanel />
        </div>
      </div>
    </div>
  );
}