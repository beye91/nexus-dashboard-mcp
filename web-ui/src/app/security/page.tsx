'use client';

import { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { SecurityConfig } from '@/types';

export default function SecurityPage() {
  const [config, setConfig] = useState<SecurityConfig | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [formConfig, setFormConfig] = useState<SecurityConfig>({
    edit_mode_enabled: false,
    allowed_operations: [],
    audit_logging: true,
  });
  const [newAllowedOp, setNewAllowedOp] = useState('');

  useEffect(() => {
    fetchSecurityConfig();
  }, []);

  async function fetchSecurityConfig() {
    try {
      setLoading(true);
      const [configRes, editModeRes] = await Promise.all([
        api.security.getConfig(),
        api.security.getEditMode(),
      ]);

      const configData = configRes.data;
      // Ensure allowed_operations is an array
      if (!configData.allowed_operations) {
        configData.allowed_operations = [];
      }
      setConfig(configData);
      setFormConfig(configData);
      setEditMode(editModeRes.data.enabled);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch security config:', err);
      setError('Failed to load security configuration');
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleEditMode() {
    try {
      const newEditMode = !editMode;
      await api.security.setEditMode(newEditMode);
      setEditMode(newEditMode);
      setSuccess(`Edit mode ${newEditMode ? 'enabled' : 'disabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Failed to toggle edit mode:', err);
      setError(err.response?.data?.detail || 'Failed to toggle edit mode');
    }
  }

  async function handleSaveConfig() {
    try {
      setSaving(true);
      setError(null);
      await api.security.updateConfig(formConfig);
      setConfig(formConfig);
      setSuccess('Security configuration updated successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Failed to save config:', err);
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  }

  function handleAddAllowedOp() {
    if (newAllowedOp.trim() && !formConfig.allowed_operations.includes(newAllowedOp.trim())) {
      setFormConfig({
        ...formConfig,
        allowed_operations: [...formConfig.allowed_operations, newAllowedOp.trim()],
      });
      setNewAllowedOp('');
    }
  }

  function handleRemoveAllowedOp(op: string) {
    setFormConfig({
      ...formConfig,
      allowed_operations: formConfig.allowed_operations.filter((item) => item !== op),
    });
  }

  function hasChanges() {
    return JSON.stringify(config) !== JSON.stringify(formConfig);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Security Settings</h2>
          <p className="text-gray-600">
            Configure edit mode and operation permissions for the MCP server
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right text-red-700 hover:text-red-900"
            >
              &times;
            </button>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            {success}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading security settings...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Edit Mode Toggle */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Edit Mode</h3>
                  <p className="text-sm text-gray-600">
                    Enable or disable write operations on Nexus Dashboard clusters. When disabled,
                    all operations are read-only.
                  </p>
                  <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                    <div className="flex">
                      <svg
                        className="h-5 w-5 text-yellow-400 mr-2"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-yellow-800">Warning</p>
                        <p className="text-sm text-yellow-700 mt-1">
                          Enabling edit mode allows write operations that can modify your Nexus
                          Dashboard configuration. Use with caution.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="ml-6">
                  <button
                    onClick={handleToggleEditMode}
                    className={`relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      editMode ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                    role="switch"
                    aria-checked={editMode}
                  >
                    <span
                      className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        editMode ? 'translate-x-6' : 'translate-x-0'
                      }`}
                    />
                  </button>
                  <p className="mt-2 text-sm font-medium text-gray-900 text-center">
                    {editMode ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
              </div>
            </div>

            {/* Allowed Operations */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Allowed Operations</h3>
              <p className="text-sm text-gray-600 mb-4">
                Specific operations that are explicitly allowed. Leave empty to allow all operations when edit mode is enabled.
              </p>

              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newAllowedOp}
                  onChange={(e) => setNewAllowedOp(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddAllowedOp()}
                  placeholder="e.g., manage_createVlan, analyze_getInsights"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder:text-gray-400"
                />
                <button
                  onClick={handleAddAllowedOp}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                >
                  Add
                </button>
              </div>

              {formConfig.allowed_operations.length === 0 ? (
                <p className="text-sm text-gray-500 italic">All operations allowed (when edit mode is enabled)</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {formConfig.allowed_operations.map((op) => (
                    <div
                      key={op}
                      className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                    >
                      {op}
                      <button
                        onClick={() => handleRemoveAllowedOp(op)}
                        className="ml-2 text-green-600 hover:text-green-900"
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Save Button */}
            {hasChanges() && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">
                      You have unsaved changes to the security configuration.
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setFormConfig(config || formConfig)}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                    >
                      Discard Changes
                    </button>
                    <button
                      onClick={handleSaveConfig}
                      disabled={saving}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Configuration'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Current Configuration Summary */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="border-l-4 border-blue-500 pl-4">
                  <p className="text-sm font-medium text-gray-600">Edit Mode</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {editMode ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div className="border-l-4 border-green-500 pl-4">
                  <p className="text-sm font-medium text-gray-600">Allowed Operations</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {config?.allowed_operations?.length || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
