'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface NotificationsContextType {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

const NotificationsContext = createContext<NotificationsContextType | null>(null);

export function NotificationsProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { socket, isConnected } = useWebSocketContext();

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false,
    };
    setNotifications(prev => [newNotification, ...prev]);

    // Browser notification if permission granted
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
      });
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === id ? { ...notif, read: true } : notif
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notif => ({ ...notif, read: true }))
    );
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  // WebSocket notification listeners
  useEffect(() => {
    if (!socket || !isConnected) return;

    const handleTradeNotification = (data: any) => {
      addNotification({
        type: data.type || 'info',
        title: data.title || 'Trade Update',
        message: data.message || 'New trade activity detected',
      });
    };

    const handlePriceAlert = (data: any) => {
      addNotification({
        type: 'warning',
        title: 'Price Alert',
        message: `${data.symbol} has reached ${data.price}`,
      });
    };

    const handleSystemNotification = (data: any) => {
      addNotification({
        type: data.type || 'info',
        title: data.title || 'System Notification',
        message: data.message || 'System update',
      });
    };

    socket.on('trade_notification', handleTradeNotification);
    socket.on('price_alert', handlePriceAlert);
    socket.on('system_notification', handleSystemNotification);

    return () => {
      socket.off('trade_notification', handleTradeNotification);
      socket.off('price_alert', handlePriceAlert);
      socket.off('system_notification', handleSystemNotification);
    };
  }, [socket, isConnected]);

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return (
    <NotificationsContext.Provider
      value={{
        notifications,
        unreadCount,
        addNotification,
        markAsRead,
        markAllAsRead,
        removeNotification,
        clearAll,
      }}
    >
      {children}
    </NotificationsContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationsProvider');
  }
  return context;
}