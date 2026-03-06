'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';

interface OrderFormData {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
}

interface OrderFormProps {
  onOrderPlaced: () => void;
}

export function OrderForm({ onOrderPlaced }: OrderFormProps) {
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm<OrderFormData>({
    defaultValues: {
      symbol: 'EURUSD',
      side: 'buy',
      type: 'market',
      quantity: 0.01,
    },
  });

  const orderType = watch('type');

  const onSubmit = async (data: OrderFormData) => {
    setLoading(true);
    try {
      await api.post('/api/v1/orders', data);
      onOrderPlaced();
    } catch (error: any) {
      console.error('Failed to place order:', error);
      alert(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          {errors.symbol && (
            <p className="text-red-500 text-sm mt-1">{errors.symbol.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Side
          </label>
          <select
            {...register('side', { required: 'Side is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order Type
          </label>
          <select
            {...register('type', { required: 'Order type is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="market">Market</option>
            <option value="limit">Limit</option>
            <option value="stop">Stop</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantity
          </label>
          <input
            type="number"
            step="0.01"
            {...register('quantity', {
              required: 'Quantity is required',
              min: { value: 0.01, message: 'Minimum quantity is 0.01' }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.quantity && (
            <p className="text-red-500 text-sm mt-1">{errors.quantity.message}</p>
          )}
        </div>

        {(orderType === 'limit' || orderType === 'stop') && (
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price
            </label>
            <input
              type="number"
              step="0.00001"
              {...register('price', {
                required: 'Price is required for limit/stop orders',
                min: { value: 0, message: 'Price must be positive' }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.price && (
              <p className="text-red-500 text-sm mt-1">{errors.price.message}</p>
            )}
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" disabled={loading}>
          {loading ? 'Placing Order...' : 'Place Order'}
        </Button>
      </div>
    </form>
  );
}