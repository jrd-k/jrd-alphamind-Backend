'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Order } from '@/types';
import { Button } from '@/components/ui/Button';
import { OrderForm } from '@/components/orders/OrderForm';
import { OrderList } from '@/components/orders/OrderList';

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [demoMode, setDemoMode] = useState(false);

  const mockOrders: Order[] = [
    { id: 1, symbol: 'EURUSD', type: 'limit', side: 'buy', quantity: 1, price: 1.0800, status: 'pending', created_at: new Date(Date.now() - 3600000).toISOString() },
    { id: 2, symbol: 'GBPUSD', type: 'market', side: 'sell', quantity: 1, price: 1.2850, status: 'executed', created_at: new Date(Date.now() - 7200000).toISOString() },
    { id: 3, symbol: 'USDJPY', type: 'stop', side: 'buy', quantity: 1, price: 110.00, status: 'pending', created_at: new Date(Date.now() - 1800000).toISOString() },
  ];

  const fetchOrders = async () => {
    try {
      const response = await api.get('/api/v1/orders');
      setOrders(response.data);
      setDemoMode(false);
    } catch (error: any) {
      const isNetworkError = !error.response || error.message === 'Network Error';
      const is404or422 = error.response?.status === 404 || error.response?.status === 422;
      
      if (isNetworkError || is404or422) {
        console.log('Using demo mode for orders');
        setOrders(mockOrders);
        setDemoMode(true);
      } else {
        console.error('Failed to fetch orders:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleOrderPlaced = () => {
    setShowOrderForm(false);
    fetchOrders(); // Refresh orders list
  };

  const handleCancelOrder = async (orderId: number) => {
    try {
      await api.delete(`/api/v1/orders/${orderId}`);
      fetchOrders(); // Refresh orders list
    } catch (error) {
      console.error('Failed to cancel order:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Orders</h1>
        <Button onClick={() => setShowOrderForm(!showOrderForm)}>
          {showOrderForm ? 'Cancel' : 'Place New Order'}
        </Button>
      </div>

      {demoMode && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded">
          <p className="text-sm">
            <strong>Demo Mode:</strong> Using mock order data. Connect backend API to place real orders.
          </p>
        </div>
      )}

      {showOrderForm && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Place New Order</h2>
          <OrderForm onOrderPlaced={handleOrderPlaced} />
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Order History</h2>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <OrderList orders={orders} onCancelOrder={handleCancelOrder} />
        )}
      </div>
    </div>
  );
}