'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { SystemStats, SystemHealth } from '@/types';

export default function HomePage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await api.system.stats();
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    }

    async function fetchHealth() {
      try {
        const response = await api.health.get();
        setHealth(response.data);
      } catch (error) {
        console.error('Failed to fetch health:', error);
      }
    }

    fetchStats();
    fetchHealth();

    // Auto-refresh health every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

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
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'degraded':
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'unhealthy':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h2>
          <p className="text-gray-600">
            Manage Nexus Dashboard clusters, security settings, and view audit logs
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Operations</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {stats?.total_operations || 0}
                  </p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Clusters</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {stats?.clusters_configured || 0}
                  </p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Audit Logs</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {stats?.audit_logs_count || 0}
                  </p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Edit Mode</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {stats?.edit_mode_enabled ? 'ON' : 'OFF'}
                  </p>
                </div>
                <div className={`p-3 rounded-full ${stats?.edit_mode_enabled ? 'bg-yellow-100' : 'bg-gray-100'}`}>
                  <svg className={`w-8 h-8 ${stats?.edit_mode_enabled ? 'text-yellow-600' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* System Health Widget */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
              <Link
                href="/health"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View Details →
              </Link>
            </div>

            {health ? (
              <div className="space-y-4">
                {/* Overall Status */}
                <div className={`rounded-lg p-4 border-2 ${getStatusColor(health.status)}`}>
                  <div className="flex items-center gap-3">
                    {getStatusIcon(health.status)}
                    <div>
                      <p className="font-semibold capitalize">{health.status}</p>
                      <p className="text-xs opacity-75">Overall System Status</p>
                    </div>
                  </div>
                </div>

                {/* Service Status Grid */}
                <div className="grid grid-cols-1 gap-2">
                  {health.services.slice(0, 3).map((service) => (
                    <div
                      key={service.name}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center gap-2">
                        {getStatusIcon(service.status)}
                        <span className="text-sm font-medium text-gray-900">{service.name}</span>
                      </div>
                      {service.response_time_ms !== null && service.response_time_ms !== undefined && (
                        <span className="text-xs text-gray-500">{service.response_time_ms}ms</span>
                      )}
                    </div>
                  ))}
                </div>

                {/* Last Updated */}
                <p className="text-xs text-gray-500 text-center">
                  Last updated: {new Date(health.timestamp).toLocaleTimeString()}
                </p>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-blue-600 border-r-transparent"></div>
                <p className="mt-2 text-sm text-gray-600">Loading health status...</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Links</h3>
            <div className="space-y-3">
              <Link
                href="/clusters"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <h4 className="font-medium text-gray-900">Manage Clusters</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Add, edit, or remove Nexus Dashboard cluster connections
                </p>
              </Link>
              <Link
                href="/security"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <h4 className="font-medium text-gray-900">Security Settings</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Configure edit mode and security policies
                </p>
              </Link>
              <Link
                href="/audit"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <h4 className="font-medium text-gray-900">View Audit Logs</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Review operation history and export logs
                </p>
              </Link>
              <Link
                href="/health"
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <h4 className="font-medium text-gray-900">System Health</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Monitor all services and system status
                </p>
              </Link>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">About</h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>
                The Nexus Dashboard MCP Server provides an AI-powered interface to Cisco Nexus Dashboard
                through the Model Context Protocol.
              </p>
              <div className="border-t pt-3">
                <div className="flex justify-between py-2">
                  <span className="font-medium">APIs Loaded:</span>
                  <span>4 (Manage, Analyze, Infra, OneManage)</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="font-medium">Total Operations:</span>
                  <span>{stats?.total_operations || 638}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="font-medium">Status:</span>
                  <span className="text-green-600 font-medium">Running</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
