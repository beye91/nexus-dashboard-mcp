'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { SystemHealth, SystemStats } from '@/types';

export default function HealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchHealth();
    fetchStats();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchHealth();
        fetchStats();
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  async function fetchHealth() {
    try {
      const response = await api.health.get();
      setHealth(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch health:', err);
      setError('Failed to load system health');
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    try {
      const response = await api.stats.get();
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'healthy':
        return (
          <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'degraded':
        return (
          <svg className="w-6 h-6 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'unhealthy':
        return (
          <svg className="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return null;
    }
  }

  function formatUptime(seconds: number) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    return parts.length > 0 ? parts.join(' ') : '< 1m';
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">System Health</h2>
            <p className="text-gray-600">
              Real-time status of all services and components
            </p>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Auto-refresh (30s)
            </label>
            <button
              onClick={() => {
                fetchHealth();
                fetchStats();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition font-medium"
            >
              Refresh Now
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading system health...</p>
          </div>
        ) : health ? (
          <div className="space-y-6">
            {/* Overall Status Card */}
            <div className={`rounded-lg shadow-lg p-6 border-2 ${getStatusColor(health.status)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {getStatusIcon(health.status)}
                  <div>
                    <h3 className="text-2xl font-bold capitalize">{health.status}</h3>
                    <p className="text-sm mt-1">
                      Overall System Status • Uptime: {formatUptime(health.uptime_seconds)}
                    </p>
                    <p className="text-xs mt-1 opacity-75">
                      Last updated: {new Date(health.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Services Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {health.services.map((service) => (
                <div
                  key={service.name}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="font-semibold text-gray-900">{service.name}</h4>
                    {getStatusIcon(service.status)}
                  </div>
                  <div
                    className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-3 ${getStatusColor(
                      service.status
                    )}`}
                  >
                    {service.status}
                  </div>
                  {service.message && (
                    <p className="text-sm text-gray-600 mb-2">{service.message}</p>
                  )}
                  {service.response_time_ms !== null && service.response_time_ms !== undefined && (
                    <p className="text-xs text-gray-500">
                      Response time: {service.response_time_ms}ms
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* System Statistics */}
            {stats && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Statistics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-blue-600">{stats.total_operations}</p>
                    <p className="text-sm text-gray-600 mt-1">Total Operations</p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-green-600">{stats.clusters_configured}</p>
                    <p className="text-sm text-gray-600 mt-1">Clusters Configured</p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-purple-600">{stats.audit_logs_count}</p>
                    <p className="text-sm text-gray-600 mt-1">Audit Logs</p>
                  </div>
                  <div className="text-center">
                    <div
                      className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${
                        stats.edit_mode_enabled
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {stats.edit_mode_enabled ? 'Edit Mode ON' : 'Read-Only'}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">Security Mode</p>
                  </div>
                </div>
              </div>
            )}

            {/* Documentation Link */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <svg
                  className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-blue-900 mb-2">Need Help?</h4>
                  <p className="text-sm text-blue-800 mb-3">
                    Learn more about the Nexus Dashboard MCP Server, its components, and how to use it effectively.
                  </p>
                  <Link
                    href="/docs"
                    className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition text-sm font-medium"
                  >
                    View Documentation
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
