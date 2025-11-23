'use client';

import { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { Cluster, CreateClusterRequest } from '@/types';

export default function ClustersPage() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCluster, setEditingCluster] = useState<Cluster | null>(null);
  const [testingCluster, setTestingCluster] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    username: '',
    password: '',
    verify_ssl: true,
  });

  useEffect(() => {
    fetchClusters();
  }, []);

  async function fetchClusters() {
    try {
      setLoading(true);
      const response = await api.clusters.list();
      setClusters(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch clusters:', err);
      setError('Failed to load clusters');
    } finally {
      setLoading(false);
    }
  }

  function openAddModal() {
    setEditingCluster(null);
    setFormData({
      name: '',
      url: '',
      username: '',
      password: '',
      verify_ssl: true,
    });
    setShowModal(true);
  }

  function openEditModal(cluster: Cluster) {
    setEditingCluster(cluster);
    setFormData({
      name: cluster.name,
      url: cluster.url,
      username: cluster.username,
      password: '',
      verify_ssl: cluster.verify_ssl,
    });
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingCluster(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (editingCluster) {
        // Update existing cluster
        await api.clusters.update(editingCluster.name, formData);
      } else {
        // Create new cluster
        await api.clusters.create(formData);
      }
      await fetchClusters();
      closeModal();
    } catch (err: any) {
      console.error('Failed to save cluster:', err);
      setError(err.response?.data?.detail || 'Failed to save cluster');
    }
  }

  async function handleDelete(clusterName: string) {
    if (!confirm(`Are you sure you want to delete cluster "${clusterName}"?`)) {
      return;
    }

    try {
      await api.clusters.delete(clusterName);
      await fetchClusters();
    } catch (err: any) {
      console.error('Failed to delete cluster:', err);
      alert(err.response?.data?.detail || 'Failed to delete cluster');
    }
  }

  async function handleTestConnection(cluster: Cluster) {
    setTestingCluster(cluster.name);
    try {
      await api.clusters.test({
        url: cluster.url,
        username: cluster.username,
        password: '',
        verify_ssl: cluster.verify_ssl,
      });
      alert(`Connection to "${cluster.name}" successful!`);
    } catch (err: any) {
      console.error('Connection test failed:', err);
      alert(err.response?.data?.detail || 'Connection test failed');
    } finally {
      setTestingCluster(null);
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Cluster Management</h2>
            <p className="text-gray-600">
              Manage Nexus Dashboard cluster connections and credentials
            </p>
          </div>
          <button
            onClick={openAddModal}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition font-medium"
          >
            Add New Cluster
          </button>
        </div>

        {error && !showModal && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading clusters...</p>
          </div>
        ) : clusters.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No clusters configured</h3>
            <p className="mt-1 text-gray-500">Get started by adding a new cluster connection.</p>
            <button
              onClick={openAddModal}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
            >
              Add Your First Cluster
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      URL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Username
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SSL Verify
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clusters.map((cluster) => (
                    <tr key={cluster.name} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{cluster.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{cluster.url}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{cluster.username}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                            cluster.status
                          )}`}
                        >
                          {cluster.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {cluster.verify_ssl ? 'Yes' : 'No'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleTestConnection(cluster)}
                          disabled={testingCluster === cluster.name}
                          className="text-blue-600 hover:text-blue-900 mr-4 disabled:opacity-50"
                        >
                          {testingCluster === cluster.name ? 'Testing...' : 'Test'}
                        </button>
                        <button
                          onClick={() => openEditModal(cluster)}
                          className="text-indigo-600 hover:text-indigo-900 mr-4"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(cluster.name)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {editingCluster ? 'Edit Cluster' : 'Add New Cluster'}
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
                    Cluster Name
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!editingCluster}
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-gray-900 placeholder:text-gray-400"
                    placeholder="my-nexus-cluster"
                  />
                  {editingCluster && (
                    <p className="mt-1 text-xs text-gray-500">Cluster name cannot be changed</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    URL
                  </label>
                  <input
                    type="url"
                    required
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder:text-gray-400"
                    placeholder="https://nexus-dashboard.example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder:text-gray-400"
                    placeholder="admin"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    required={!editingCluster}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder:text-gray-400"
                    placeholder={editingCluster ? 'Leave blank to keep current' : ''}
                  />
                  {editingCluster && (
                    <p className="mt-1 text-xs text-gray-500">
                      Leave blank to keep current password
                    </p>
                  )}
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="verify_ssl"
                    checked={formData.verify_ssl}
                    onChange={(e) => setFormData({ ...formData, verify_ssl: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="verify_ssl" className="ml-2 block text-sm text-gray-700">
                    Verify SSL certificate
                  </label>
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
                  {editingCluster ? 'Update Cluster' : 'Add Cluster'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
