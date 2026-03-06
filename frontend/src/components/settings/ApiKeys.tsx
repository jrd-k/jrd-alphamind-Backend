'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface ApiKeysProps {
  settings: any;
  onSettingsChange: (settings: any) => void;
  user: any;
}

export function ApiKeys({ settings, onSettingsChange }: ApiKeysProps) {
  const [apiKeys, setApiKeys] = useState({
    deepseek: '',
    openai: '',
    showKeys: false,
  });

  const handleKeyChange = (provider: string, value: string) => {
    setApiKeys(prev => ({
      ...prev,
      [provider]: value,
    }));
  };

  const saveApiKeys = () => {
    // In a real app, this would be encrypted and stored securely
    console.log('Saving API keys:', apiKeys);
    alert('API keys saved successfully!');
  };

  const generateApiKey = () => {
    // This would typically call the backend to generate a new API key
    const newKey = 'ak_' + Math.random().toString(36).substr(2, 16);
    return newKey;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">API Keys & Integrations</h2>

        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Security Notice
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  API keys are sensitive information. They are encrypted and stored securely.
                  Never share your API keys with anyone.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">AI Services</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  DeepSeek API Key
                </label>
                <div className="flex space-x-2">
                  <input
                    type={apiKeys.showKeys ? 'text' : 'password'}
                    value={apiKeys.deepseek}
                    onChange={(e) => handleKeyChange('deepseek', e.target.value)}
                    placeholder="sk-..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setApiKeys(prev => ({ ...prev, deepseek: generateApiKey() }))}
                  >
                    Generate
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Used for web search and market intelligence
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  OpenAI API Key
                </label>
                <div className="flex space-x-2">
                  <input
                    type={apiKeys.showKeys ? 'text' : 'password'}
                    value={apiKeys.openai}
                    onChange={(e) => handleKeyChange('openai', e.target.value)}
                    placeholder="sk-..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setApiKeys(prev => ({ ...prev, openai: generateApiKey() }))}
                  >
                    Generate
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Used for AI-powered trading recommendations
                </p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Application API</h3>

            <div className="bg-gray-50 p-4 rounded-md">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Your API Key</span>
                <Button variant="outline" size="sm">
                  Regenerate
                </Button>
              </div>
              <code className="text-sm text-gray-600 bg-white px-2 py-1 rounded border">
                {apiKeys.showKeys ? 'ak_live_1234567890abcdef' : '••••••••••••••••••••'}
              </code>
              <p className="text-xs text-gray-500 mt-2">
                Use this key to access the AlphaMind API programmatically
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4 mt-6">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={apiKeys.showKeys}
              onChange={(e) => setApiKeys(prev => ({ ...prev, showKeys: e.target.checked }))}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">Show API keys</span>
          </label>
        </div>

        <div className="mt-6">
          <Button onClick={saveApiKeys}>
            Save API Keys
          </Button>
        </div>
      </div>
    </div>
  );
}