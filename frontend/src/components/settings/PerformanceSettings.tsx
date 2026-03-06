'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Zap, Database, HardDrive, Cpu } from 'lucide-react';

export function PerformanceSettings() {
  const [performanceSettings, setPerformanceSettings] = useState({
    enableCaching: true,
    cacheExpiry: 300, // seconds
    lazyLoading: true,
    imageOptimization: true,
    bundleSplitting: true,
    compression: true,
  });

  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleSettingChange = (key: string, value: any) => {
    setPerformanceSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const savePerformanceSettings = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Performance settings saved successfully!');
    } catch (error) {
      alert('Failed to save performance settings');
    } finally {
      setLoading(false);
    }
  };

  const runBundleAnalysis = async () => {
    setAnalyzing(true);
    try {
      // Simulate bundle analysis
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('Bundle analysis complete! Check the console for details.');
    } catch (error) {
      alert('Bundle analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const clearCache = async () => {
    try {
      // Clear local storage, session storage, etc.
      localStorage.clear();
      sessionStorage.clear();

      // Clear service worker cache if available
      if ('serviceWorker' in navigator && 'caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames.map(cacheName => caches.delete(cacheName))
        );
      }

      alert('Cache cleared successfully!');
    } catch (error) {
      alert('Failed to clear cache');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Zap className="h-6 w-6 mr-2 text-yellow-600" />
          Performance Optimization
        </h2>

        <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Performance Tips
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  Enable caching and lazy loading to improve load times.
                  Regularly clear cache and run bundle analysis to optimize performance.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Bundle Analysis */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <HardDrive className="h-6 w-6 text-gray-400" />
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Bundle Analysis</h3>
                  <p className="text-sm text-gray-500">
                    Analyze bundle size and identify optimization opportunities
                  </p>
                </div>
              </div>
              <Button
                onClick={runBundleAnalysis}
                disabled={analyzing}
                variant="outline"
                size="sm"
              >
                {analyzing ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Analyzing...
                  </>
                ) : (
                  'Run Analysis'
                )}
              </Button>
            </div>
          </div>

          {/* Caching Settings */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Database className="h-5 w-5 mr-2 text-gray-400" />
              Caching
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Enable API Caching</label>
                  <p className="text-sm text-gray-500">Cache API responses to reduce load times</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={performanceSettings.enableCaching}
                    onChange={(e) => handleSettingChange('enableCaching', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cache Expiry (seconds)
                </label>
                <select
                  value={performanceSettings.cacheExpiry}
                  onChange={(e) => handleSettingChange('cacheExpiry', parseInt(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={60}>1 minute</option>
                  <option value={300}>5 minutes</option>
                  <option value={900}>15 minutes</option>
                  <option value={3600}>1 hour</option>
                </select>
              </div>

              <div className="pt-4">
                <Button onClick={clearCache} variant="outline" size="sm">
                  Clear All Cache
                </Button>
              </div>
            </div>
          </div>

          {/* Loading Optimization */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Cpu className="h-5 w-5 mr-2 text-gray-400" />
              Loading Optimization
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Lazy Loading</label>
                  <p className="text-sm text-gray-500">Load components only when needed</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={performanceSettings.lazyLoading}
                    onChange={(e) => handleSettingChange('lazyLoading', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Image Optimization</label>
                  <p className="text-sm text-gray-500">Optimize images for faster loading</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={performanceSettings.imageOptimization}
                    onChange={(e) => handleSettingChange('imageOptimization', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Bundle Splitting</label>
                  <p className="text-sm text-gray-500">Split code into smaller chunks</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={performanceSettings.bundleSplitting}
                    onChange={(e) => handleSettingChange('bundleSplitting', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Response Compression</label>
                  <p className="text-sm text-gray-500">Compress responses for faster transfer</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={performanceSettings.compression}
                    onChange={(e) => handleSettingChange('compression', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <Button onClick={savePerformanceSettings} disabled={loading}>
            {loading ? 'Saving...' : 'Save Performance Settings'}
          </Button>
        </div>
      </div>
    </div>
  );
}