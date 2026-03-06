'use client';

import { useWebSocketContext } from '@/components/providers/WebSocketProvider';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';

export function ConnectionStatus() {
  const { isConnected, error, reconnect } = useWebSocketContext();

  if (isConnected) {
    return (
      <div className="flex items-center space-x-2 text-green-600">
        <Wifi className="h-4 w-4" />
        <span className="text-sm">Connected</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center space-x-2 text-red-600">
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">Connection Error</span>
        <button
          onClick={reconnect}
          className="text-xs underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-yellow-600">
      <WifiOff className="h-4 w-4" />
      <span className="text-sm">Connecting...</span>
    </div>
  );
}