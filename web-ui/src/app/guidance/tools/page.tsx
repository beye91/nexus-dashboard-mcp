'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { ToolDescriptionOverride } from '@/types';

export default function ToolOverridesPage() {
  const [overrides, setOverrides] = useState<ToolDescriptionOverride[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingOverride, setEditingOverride] = useState<ToolDescriptionOverride | null>(null);
  const [formData, setFormData] = useState({
    operation_name: '',
    enhanced_description: '',
    usage_hint: '',
    related_tools: [] as string[],
    is_active: true,
  });
  const [newRelatedTool, setNewRelatedTool] = useState('');

  const fetchOverrides = async () => {
    try {
      setLoading(true);
      const response = await api.guidance.listToolOverrides();
      setOverrides(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load tool overrides');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverrides();
  }, []);

  const filteredOverrides = overrides.filter((o) =>
    o.operation_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (o.enhanced_description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEdit = (override: ToolDescriptionOverride) => {
    setEditingOverride(override);
    setFormData({
      operation_name: override.operation_name,
      enhanced_description: override.enhanced_description || '',
      usage_hint: override.usage_hint || '',
      related_tools: override.related_tools || [],
      is_active: override.is_active,
    });
    setShowModal(true);
  };

  const handleCreate = () => {
    setEditingOverride(null);
    setFormData({
      operation_name: '',
      enhanced_description: '',
      usage_hint: '',
      related_tools: [],
      is_active: true,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      await api.guidance.upsertToolOverride(formData.operation_name, {
        enhanced_description: formData.enhanced_description,
        usage_hint: formData.usage_hint,
        related_tools: formData.related_tools,
        is_active: formData.is_active,
      });
      setShowModal(false);
      fetchOverrides();
    } catch (err: any) {
      setError(err.message || 'Failed to save tool override');
    }
  };

  const handleDelete = async (operationName: string) => {
    if (!confirm('Are you sure you want to delete this tool override?')) return;
    try {
      await api.guidance.deleteToolOverride(operationName);
      fetchOverrides();
    } catch (err: any) {
      setError(err.message || 'Failed to delete tool override');
    }
  };

  const addRelatedTool = () => {
    if (newRelatedTool && !formData.related_tools.includes(newRelatedTool)) {
      setFormData({
        ...formData,
        related_tools: [...formData.related_tools, newRelatedTool],
      });
      setNewRelatedTool('');
    }
  };

  const removeRelatedTool = (tool: string) => {
    setFormData({
      ...formData,
      related_tools: formData.related_tools.filter((t) => t !== tool),
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/guidance" className="text-blue-600 hover:text-blue-700">
            &larr; Back to Guidance
          </Link>
        </div>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tool Description Overrides</h1>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add Override
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">
            Dismiss
          </button>
        </div>
      )}

      <div className="mb-4">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by operation name or description..."
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Operation</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usage Hint</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Related Tools</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredOverrides.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  {searchTerm ? 'No matching overrides found.' : 'No tool overrides found. Click "Add Override" to create one.'}
                </td>
              </tr>
            ) : (
              filteredOverrides.map((override) => (
                <tr key={override.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{override.operation_name}</div>
                    {override.enhanced_description && (
                      <div className="text-xs text-gray-500 mt-1 truncate max-w-xs">
                        {override.enhanced_description.substring(0, 80)}...
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {override.usage_hint ? (
                      <span className="truncate max-w-xs block">{override.usage_hint.substring(0, 50)}...</span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {(override.related_tools || []).slice(0, 3).map((tool) => (
                        <span key={tool} className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                          {tool}
                        </span>
                      ))}
                      {(override.related_tools || []).length > 3 && (
                        <span className="text-xs text-gray-500">+{override.related_tools.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      override.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {override.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleEdit(override)}
                      className="text-blue-600 hover:text-blue-800 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(override.operation_name)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {editingOverride ? 'Edit Tool Override' : 'Add Tool Override'}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Operation Name</label>
                <input
                  type="text"
                  value={formData.operation_name}
                  onChange={(e) => setFormData({ ...formData, operation_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400"
                  disabled={!!editingOverride}
                  placeholder="e.g., manage_createVlan"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Enhanced Description</label>
                <textarea
                  value={formData.enhanced_description}
                  onChange={(e) => setFormData({ ...formData, enhanced_description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400"
                  rows={4}
                  placeholder="Detailed description of what this operation does and when to use it..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Usage Hint</label>
                <textarea
                  value={formData.usage_hint}
                  onChange={(e) => setFormData({ ...formData, usage_hint: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400"
                  rows={2}
                  placeholder="Quick tip for using this operation..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Related Tools</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newRelatedTool}
                    onChange={(e) => setNewRelatedTool(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400"
                    placeholder="Operation name"
                    onKeyPress={(e) => e.key === 'Enter' && addRelatedTool()}
                  />
                  <button
                    onClick={addRelatedTool}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.related_tools.map((tool) => (
                    <span
                      key={tool}
                      className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm flex items-center gap-2"
                    >
                      {tool}
                      <button
                        onClick={() => removeRelatedTool(tool)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Active</label>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
      </main>
    </div>
  );
}
