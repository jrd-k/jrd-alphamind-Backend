'use client';

import { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';

interface UseWebSocketOptions {
  url?: string;
  token?: string;
}

interface UseWebSocketReturn {
  socket: any;
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

export function useWebSocket({ url = 'http://localhost:8000', token }: UseWebSocketOptions = {}): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<any>(null);

  useEffect(() => {
    const socket = io(url, {
      auth: token ? { token } : undefined,
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => {
      setIsConnected(true);
      setError(null);
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('connect_error', (err: any) => {
      setError(err.message);
      setIsConnected(false);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, [url, token]);

  const reconnect = () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current.connect();
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    error,
    reconnect,
  };
}