'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      try {
        // Try to login with backend
        const response = await api.post('/api/v1/auth/login', {
          username: formData.username,
          password: formData.password,
        });
        const { access_token } = response.data;

        // Store token and update auth state
        localStorage.setItem('access_token', access_token);
        login(access_token, { username: formData.username });

        router.push('/dashboard');
      } catch (err: any) {
        // If backend not available or network error, use demo mode
        const isNetworkError = !err.response || err.message === 'Network Error';
        const is404or422 = err.response?.status === 404 || err.response?.status === 422;
        
        if (isNetworkError || is404or422) {
          console.log('Using demo mode - backend not available');
          
          // Create a demo token
          const demoToken = `demo_${formData.username}_${Date.now()}`;
          localStorage.setItem('access_token', demoToken);
          login(demoToken, { 
            username: formData.username,
            email: formData.username.includes('@') ? formData.username : `${formData.username}@alphamind.local`,
            demo: true,
          });

          router.push('/dashboard');
        } else {
          throw err;
        }
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>

      <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded mb-4">
        <p className="text-sm">
          <strong>Demo Mode:</strong> Use any username and password to log in and explore the trading platform.
        </p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="username" className="block text-gray-700 mb-2">
            Username
          </label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div className="mb-6">
          <label htmlFor="password" className="block text-gray-700 mb-2">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={loading}
        >
          {loading ? 'Signing In...' : 'Sign In'}
        </Button>
      </form>

      <p className="text-center mt-4">
        Don't have an account?{' '}
        <Link href="/auth/register" className="text-blue-600 hover:text-blue-800">
          Sign up
        </Link>
      </p>
    </div>
  );
}