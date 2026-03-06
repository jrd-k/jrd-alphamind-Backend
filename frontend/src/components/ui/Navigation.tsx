'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { Button } from './Button';
import { ConnectionStatus } from './ConnectionStatus';
import { NotificationsDropdown } from './NotificationsDropdown';
import { LayoutDashboard, TrendingUp, ShoppingCart, BarChart3, Brain, Zap, Settings, LogOut } from 'lucide-react';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const { isAuthenticated, logout } = useAuthStore();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
  };

  const isActive = (path: string) => pathname === path;

  const navItems = [
    { href: '/dashboard', label: 'Home', icon: LayoutDashboard },
    { href: '/market-data', label: 'Market', icon: TrendingUp },
    { href: '/orders', label: 'Orders', icon: ShoppingCart },
    { href: '/trades', label: 'Trades', icon: BarChart3 },
    { href: '/broker', label: 'Broker', icon: Zap },
    { href: '/brain', label: 'AI', icon: Brain },
  ];

  return (
    <>
      {/* Top Header with Logo and Actions */}
      {isAuthenticated && (
        <div className="sticky top-0 z-40 bg-white border-b border-gray-200 p-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
            ⚡ AlphaMind
          </Link>
          <div className="flex items-center gap-3">
            <NotificationsDropdown />
            <ConnectionStatus />
            <Link href="/settings" className="text-gray-600 hover:text-gray-900 p-2 rounded-lg hover:bg-gray-100 transition-colors">
              <Settings className="h-6 w-6" />
            </Link>
            <button onClick={handleLogout} className="text-gray-600 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 transition-colors" title="Logout">
              <LogOut className="h-6 w-6" />
            </button>
          </div>
        </div>
      )}

      {/* iOS-Style Bottom Tab Bar - All Screens */}
      {isAuthenticated && (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 shadow-lg">
          <div className="flex justify-around items-center h-20 px-2 md:px-8 max-w-7xl mx-auto w-full">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex flex-col items-center justify-center w-16 h-16 md:w-20 md:h-16 rounded-xl transition-all active:scale-95 $
                    active
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-6 w-6 md:h-7 md:w-7 mb-1" />
                  <span className="text-xs md:text-sm font-medium text-center">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      )}
    </>
  );
}