'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';

export function RiskManagementPanel() {
  const [settings, setSettings] = useState({
    maxDrawdown: 5,
    maxDailyLoss: 100,
    maxOpenPositions: 5,
    maxRiskPerTrade: 2,
  });

  const handleSettingChange = (key: string, value: number) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Risk Management Settings</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Drawdown (%)
            </label>
            <input
              type="number"
              step="0.1"
              value={settings.maxDrawdown}
              onChange={(e) => handleSettingChange('maxDrawdown', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Daily Loss ($)
            </label>
            <input
              type="number"
              step="10"
              value={settings.maxDailyLoss}
              onChange={(e) => handleSettingChange('maxDailyLoss', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Open Positions
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={settings.maxOpenPositions}
              onChange={(e) => handleSettingChange('maxOpenPositions', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Risk Per Trade (%)
            </label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="5"
              value={settings.maxRiskPerTrade}
              onChange={(e) => handleSettingChange('maxRiskPerTrade', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="mt-6">
          <Button className="w-full">Save Settings</Button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Risk Alerts</h2>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-md">
            <div>
              <p className="text-sm font-medium text-green-800">Daily Loss Limit</p>
              <p className="text-xs text-green-600">Within safe limits</p>
            </div>
            <span className="text-green-600">✓</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <div>
              <p className="text-sm font-medium text-yellow-800">Drawdown Warning</p>
              <p className="text-xs text-yellow-600">Approaching 3% limit</p>
            </div>
            <span className="text-yellow-600">⚠</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div>
              <p className="text-sm font-medium text-blue-800">Position Count</p>
              <p className="text-xs text-blue-600">2 of 5 positions open</p>
            </div>
            <span className="text-blue-600">ℹ</span>
          </div>
        </div>
      </div>
    </div>
  );
}