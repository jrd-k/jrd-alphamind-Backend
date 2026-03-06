'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Shield, Lock, AlertTriangle, CheckCircle } from 'lucide-react';

export function SecuritySettings() {
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorEnabled: false,
    sessionTimeout: 30, // minutes
    passwordExpiry: 90, // days
    loginAttempts: 5,
    ipWhitelist: '',
    auditLogging: true,
    dataEncryption: true,
  });

  const [loading, setLoading] = useState(false);

  const handleSettingChange = (key: string, value: any) => {
    setSecuritySettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const saveSecuritySettings = async () => {
    setLoading(true);
    try {
      // In a real app, this would call the backend API
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Security settings saved successfully!');
    } catch (error) {
      alert('Failed to save security settings');
    } finally {
      setLoading(false);
    }
  };

  const enableTwoFactor = async () => {
    // In a real app, this would initiate 2FA setup
    alert('2FA setup would be initiated here');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Shield className="h-6 w-6 mr-2 text-blue-600" />
          Security & Privacy
        </h2>

        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-yellow-400 mr-3" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Security Best Practices
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  Enable two-factor authentication and regularly update your password.
                  Monitor your account activity and report any suspicious behavior.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Two-Factor Authentication */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Lock className="h-6 w-6 text-gray-400" />
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Two-Factor Authentication</h3>
                  <p className="text-sm text-gray-500">
                    Add an extra layer of security to your account
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                {securitySettings.twoFactorEnabled ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                )}
                <Button
                  onClick={enableTwoFactor}
                  variant={securitySettings.twoFactorEnabled ? 'outline' : 'primary'}
                  size="sm"
                >
                  {securitySettings.twoFactorEnabled ? 'Configured' : 'Enable 2FA'}
                </Button>
              </div>
            </div>
          </div>

          {/* Session Management */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Session Management</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Session Timeout (minutes)
                </label>
                <select
                  value={securitySettings.sessionTimeout}
                  onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={120}>2 hours</option>
                  <option value={480}>8 hours</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Login Attempts
                </label>
                <select
                  value={securitySettings.loginAttempts}
                  onChange={(e) => handleSettingChange('loginAttempts', parseInt(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={3}>3 attempts</option>
                  <option value={5}>5 attempts</option>
                  <option value={10}>10 attempts</option>
                </select>
              </div>
            </div>
          </div>

          {/* Password Policy */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Password Policy</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password Expiry (days)
                </label>
                <select
                  value={securitySettings.passwordExpiry}
                  onChange={(e) => handleSettingChange('passwordExpiry', parseInt(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={30}>30 days</option>
                  <option value={60}>60 days</option>
                  <option value={90}>90 days</option>
                  <option value={180}>180 days</option>
                  <option value={0}>Never expires</option>
                </select>
              </div>
            </div>
          </div>

          {/* Advanced Security */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Advanced Security</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Audit Logging</label>
                  <p className="text-sm text-gray-500">Log all account activities for security monitoring</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={securitySettings.auditLogging}
                    onChange={(e) => handleSettingChange('auditLogging', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Data Encryption</label>
                  <p className="text-sm text-gray-500">Encrypt sensitive data at rest and in transit</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={securitySettings.dataEncryption}
                    onChange={(e) => handleSettingChange('dataEncryption', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>
            </div>
          </div>

          {/* IP Whitelist */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">IP Whitelist</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Allowed IP Addresses (one per line)
              </label>
              <textarea
                value={securitySettings.ipWhitelist}
                onChange={(e) => handleSettingChange('ipWhitelist', e.target.value)}
                placeholder="192.168.1.100&#10;10.0.0.1&#10;203.0.113.5"
                rows={4}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Leave empty to allow access from any IP address
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <Button onClick={saveSecuritySettings} disabled={loading}>
            {loading ? 'Saving...' : 'Save Security Settings'}
          </Button>
        </div>
      </div>
    </div>
  );
}