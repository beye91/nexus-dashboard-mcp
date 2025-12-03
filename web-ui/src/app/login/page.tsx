'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [setupMode, setSetupMode] = useState(false);
  const [email, setEmail] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (setupMode) {
        // First user setup
        await api.auth.setup({ username, password, email });
        router.push('/');
      } else {
        // Normal login
        await api.auth.login({ username, password });
        router.push('/');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      if (err.response?.status === 401) {
        setError('Invalid username or password');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to login. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Check if setup is required on mount
  useState(() => {
    const checkAuth = async () => {
      try {
        const response = await api.auth.me();
        if (response.data.setup_required) {
          setSetupMode(true);
        } else if (response.data.authenticated) {
          router.push('/');
        }
      } catch (err) {
        // Not authenticated, stay on login page
      }
    };
    checkAuth();
  });

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Nexus Dashboard MCP
          </h1>
          <p className="text-gray-400">
            {setupMode ? 'Create Admin Account' : 'Sign in to continue'}
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          {setupMode && (
            <div className="mb-6 p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
              <p className="text-blue-300 text-sm">
                No users configured. Create the first admin account to get started.
              </p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                placeholder="Enter username"
                required
                autoComplete="username"
              />
            </div>

            {setupMode && (
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
                  Email (optional)
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  placeholder="admin@example.com"
                  autoComplete="email"
                />
              </div>
            )}

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                placeholder="Enter password"
                required
                autoComplete={setupMode ? 'new-password' : 'current-password'}
              />
            </div>

            {error && (
              <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {setupMode ? 'Creating Account...' : 'Signing in...'}
                </span>
              ) : (
                setupMode ? 'Create Admin Account' : 'Sign In'
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-gray-500 text-sm">
          Nexus Dashboard MCP Server
        </p>
      </div>
    </div>
  );
}
