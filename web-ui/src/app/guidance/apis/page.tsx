'use client';

import { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import { api } from '@/lib/api-client';
import type { APIGuidance } from '@/types';

export default function ApiGuidancePage() {
  const [apiGuidance, setApiGuidance] = useState<APIGuidance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingApi, setEditingApi] = useState<APIGuidance | null>(null);

  const [formData, setFormData] = useState({
    display_name: '',
    description: '',
    when_to_use: '',
    when_not_to_use: '',
    examples: [] as any[],
    priority: 0,
    is_active: true,
  });

  useEffect(() => {
    fetchApiGuidance();
  }, []);

  async function fetchApiGuidance() {
    try {
      setLoading(true);
      const response = await api.guidance.listApiGuidance();
      setApiGuidance(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch API guidance:', err);
      setError(err.response?.data?.detail || 'Failed to load API guidance');
    } finally {
      setLoading(false);
    }
  }

  function openEditModal(apiGuide: APIGuidance) {
    setEditingApi(apiGuide);
    setFormData({
      display_name: apiGuide.display_name,
      description: apiGuide.description || '',
      when_to_use: apiGuide.when_to_use || '',
      when_not_to_use: apiGuide.when_not_to_use || '',
      examples: apiGuide.examples || [],
      priority: apiGuide.priority,
      is_active: apiGuide.is_active,
    });
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingApi(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingApi) return;

    setError(null);
    try {
      await api.guidance.upsertApiGuidance(editingApi.api_name, formData);
      setSuccess('API guidance updated successfully');
      setTimeout(() => setSuccess(null), 3000);
      await fetchApiGuidance();
      closeModal();
    } catch (err: any) {
      console.error('Failed to update API guidance:', err);
      setError(err.response?.data?.detail || 'Failed to update API guidance');
    }
  }

  async function handleToggleActive(apiGuide: APIGuidance) {
    try {
      await api.guidance.upsertApiGuidance(apiGuide.api_name, {
        ...apiGuide,
        is_active: !apiGuide.is_active,
      });
      setSuccess(`${apiGuide.display_name} ${!apiGuide.is_active ? 'enabled' : 'disabled'}`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchApiGuidance();
    } catch (err: any) {
      console.error('Failed to toggle API:', err);
      setError(err.response?.data?.detail || 'Failed to toggle API');
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navigation />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">API Guidance</h2>
          <p className="text-gray-600">
            Configure when Claude should use each Nexus Dashboard API
          </p>
        </div>

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            {success}
          </div>
        )}

        {error && !showModal && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading API guidance...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      API Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      When to Use
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {apiGuidance.map((apiGuide) => (
                    <tr key={apiGuide.api_name} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {apiGuide.display_name}
                        </div>
                        <div className="text-xs text-gray-500">{apiGuide.api_name}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 max-w-md truncate">
                          {apiGuide.when_to_use || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{apiGuide.priority}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleToggleActive(apiGuide)}
                          className={`px-3 py-1 text-xs rounded-full font-semibold ${
                            apiGuide.is_active
                              ? 'bg-green-100 text-green-800 hover:bg-green-200'
                              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          }`}
                        >
                          {apiGuide.is_active ? 'Active' : 'Inactive'}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => openEditModal(apiGuide)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                  {apiGuidance.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                        No API guidance configured yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {showModal && editingApi && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-lg max-w-3xl w-full p-6 my-8 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Edit API Guidance: {editingApi.display_name}
            </h3>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    When to Use
                  </label>
                  <textarea
                    rows={4}
                    value={formData.when_to_use}
                    onChange={(e) => setFormData({ ...formData, when_to_use: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Describe when Claude should use this API..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    When NOT to Use
                  </label>
                  <textarea
                    rows={4}
                    value={formData.when_not_to_use}
                    onChange={(e) => setFormData({ ...formData, when_not_to_use: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Describe when Claude should NOT use this API..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Priority
                    </label>
                    <input
                      type="number"
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                      Active
                    </label>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}
