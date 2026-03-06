'use client';

interface TradingPreferencesProps {
  settings: any;
  onSettingsChange: (settings: any) => void;
  user: any;
}

export function TradingPreferences({ settings, onSettingsChange }: TradingPreferencesProps) {
  const handleChange = (field: string, value: any) => {
    onSettingsChange({
      ...settings,
      [field]: value,
    });
  };

  const handleRiskChange = (field: string, value: any) => {
    onSettingsChange({
      ...settings,
      riskSettings: {
        ...settings.riskSettings,
        [field]: value,
      },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">Default Trading Settings</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Symbol
            </label>
            <select
              value={settings.defaultSymbol}
              onChange={(e) => handleChange('defaultSymbol', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="EURUSD">EURUSD</option>
              <option value="GBPUSD">GBPUSD</option>
              <option value="USDJPY">USDJPY</option>
              <option value="AUDUSD">AUDUSD</option>
              <option value="USDCAD">USDCAD</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Timeframe
            </label>
            <select
              value={settings.defaultTimeframe}
              onChange={(e) => handleChange('defaultTimeframe', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
            </select>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Risk Management</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Drawdown (%)
            </label>
            <input
              type="number"
              step="0.1"
              min="1"
              max="20"
              value={settings.riskSettings.maxDrawdown}
              onChange={(e) => handleRiskChange('maxDrawdown', parseFloat(e.target.value))}
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
              min="10"
              value={settings.riskSettings.maxDailyLoss}
              onChange={(e) => handleRiskChange('maxDailyLoss', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Risk Per Trade (%)
            </label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="5"
              value={settings.riskSettings.defaultRiskPerTrade}
              onChange={(e) => handleRiskChange('defaultRiskPerTrade', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}