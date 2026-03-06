'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { UserProfile } from '@/components/settings/UserProfile';
import { TradingPreferences } from '@/components/settings/TradingPreferences';
import { NotificationSettings } from '@/components/settings/NotificationSettings';
import { ApiKeys } from '@/components/settings/ApiKeys';
import { SecuritySettings } from '@/components/settings/SecuritySettings';
import { PerformanceSettings } from '@/components/settings/PerformanceSettings';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [settings, setSettings] = useState({
    theme: 'light',
    defaultSymbol: 'EURUSD',
    defaultTimeframe: '1h',
    notifications: {
      email: true,
      browser: true,
      tradeAlerts: true,
      priceAlerts: false,
    },
    riskSettings: {
      maxDrawdown: 5,
      maxDailyLoss: 100,
      defaultRiskPerTrade: 1,
    },
  });

  const tabs = [
    { id: 'profile', label: 'Profile', component: UserProfile },
    { id: 'trading', label: 'Trading Preferences', component: TradingPreferences },
    { id: 'notifications', label: 'Notifications', component: NotificationSettings },
    { id: 'api', label: 'API Keys', component: ApiKeys },
    { id: 'security', label: 'Security', component: SecuritySettings },
    { id: 'performance', label: 'Performance', component: PerformanceSettings },
  ];

  const saveSettings = async () => {
    try {
      await api.put('/api/v1/users/settings', settings);
      alert('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    }
  };

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Settings & Configuration</h1>
        <Button onClick={saveSettings}>
          Save Changes
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {ActiveComponent && (
            <ActiveComponent
              settings={settings}
              onSettingsChange={setSettings}
              user={user}
            />
          )}
        </div>
      </div>
    </div>
  );
}