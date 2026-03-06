'use client';

import React, { createContext, useContext, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/lib/store';

interface WebSocketContextType {
  socket: any;
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore();
  const { socket, isConnected, error, reconnect } = useWebSocket({
    token: token || undefined,
  });

  return (
    <WebSocketContext.Provider value={{ socket, isConnected, error, reconnect }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}