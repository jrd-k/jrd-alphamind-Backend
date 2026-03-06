'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface AppInitializerProps {
  children: React.ReactNode;
}

export function AppInitializer({ children }: AppInitializerProps) {
  const { isAuthenticated } = useAuthStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        // Simulate app initialization
        await new Promise(resolve => setTimeout(resolve, 1000));
      } finally {
        setIsInitializing(false);
      }
    };

    init();
  }, []);

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Initializing AlphaMind
          </h2>
          <p className="text-gray-600">
            Setting up your trading platform...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}