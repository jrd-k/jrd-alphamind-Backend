'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        Welcome to AlphaMind
      </h1>
      <p className="text-xl text-gray-600 mb-8">
        AI-powered trading platform with real-time market data and intelligent decision making
      </p>

      <div className="space-x-4">
        <Link
          href="/auth/register"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Get Started
        </Link>
        <Link
          href="/auth/login"
          className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
        >
          Sign In
        </Link>
      </div>

      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Real-time Trading</h3>
          <p className="text-gray-600">
            Execute trades with live market data and instant order processing
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">AI Decision Making</h3>
          <p className="text-gray-600">
            Leverage AI-powered analysis and technical indicators for smarter trading
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Risk Management</h3>
          <p className="text-gray-600">
            Advanced position sizing and risk controls to protect your capital
          </p>
        </div>
      </div>
    </div>
  );
}
