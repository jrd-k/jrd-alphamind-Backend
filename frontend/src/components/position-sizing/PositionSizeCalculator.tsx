'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';

interface PositionSizeForm {
  riskPercentage: number;
  stopLossPips: number;
  symbol: string;
}

interface PositionSizeCalculatorProps {
  accountBalance: number;
}

export function PositionSizeCalculator({ accountBalance }: PositionSizeCalculatorProps) {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<PositionSizeForm>({
    defaultValues: {
      riskPercentage: 1,
      stopLossPips: 50,
      symbol: 'EURUSD',
    },
  });

  const onSubmit = async (data: PositionSizeForm) => {
    setLoading(true);
    try {
      const response = await api.post('/api/v1/position-sizing/calculate', {
        account_balance: accountBalance,
        risk_percentage: data.riskPercentage,
        stop_loss_pips: data.stopLossPips,
        symbol: data.symbol,
      });
      setResult(response.data);
    } catch (error: any) {
      console.error('Failed to calculate position size:', error);
      alert(error.response?.data?.detail || 'Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Position Size Calculator</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Risk Percentage (%)
          </label>
          <input
            type="number"
            step="0.1"
            {...register('riskPercentage', {
              required: 'Risk percentage is required',
              min: { value: 0.1, message: 'Minimum 0.1%' },
              max: { value: 5, message: 'Maximum 5%' }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.riskPercentage && (
            <p className="text-red-500 text-sm mt-1">{errors.riskPercentage.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stop Loss (Pips)
          </label>
          <input
            type="number"
            step="1"
            {...register('stopLossPips', {
              required: 'Stop loss is required',
              min: { value: 10, message: 'Minimum 10 pips' },
              max: { value: 500, message: 'Maximum 500 pips' }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.stopLossPips && (
            <p className="text-red-500 text-sm mt-1">{errors.stopLossPips.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Symbol
          </label>
          <select
            {...register('symbol', { required: 'Symbol is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="EURUSD">EURUSD</option>
            <option value="GBPUSD">GBPUSD</option>
            <option value="USDJPY">USDJPY</option>
            <option value="AUDUSD">AUDUSD</option>
          </select>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Calculating...' : 'Calculate Position Size'}
        </Button>
      </form>

      {result && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <h3 className="text-lg font-semibold text-green-800 mb-3">Recommended Position</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-green-700">Position Size:</span>
              <span className="font-semibold text-green-800">{result.position_size?.toFixed(2)} lots</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-700">Risk Amount:</span>
              <span className="font-semibold text-green-800">${result.risk_amount?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-700">Lot Size:</span>
              <span className="font-semibold text-green-800">{result.lot_size?.toFixed(5)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}