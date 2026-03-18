'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { UseCase, Workflow } from '@/types';

export default function UseCasesPage() {
  const [useCases, setUseCases] = useState<UseCase[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUseCase, setEditingUseCase] = useState<UseCase | null>(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: '',
    is_active: true,
    workflow_ids: [] as number[],
  });

  const fetchUseCases = async () => {
    try {
      setLoading(true);
      const [useCasesRes, workflowsRes] = await Promise.all([
        api.guidance.listUseCases(),
        api.guidance.listWorkflows(),
      ]);
      setUseCases(useCasesRes.data);
      setWorkflows(workflowsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load use cases');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUseCases();
  }, []);

  const categories = Array.from(new Set(useCases.map((u) => u.category).filter(Boolean))) as string[];

  const filteredUseCases = useCases.filter((u) => {
    const matchesSearch =
      u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !categoryFilter || u.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleCreate = () => {
    setEditingUseCase(null);
    setFormData({ name: '', display_name: '', description: '', category: '', is_active: true, workflow_ids: [] });
    setShowModal(true);
  };

  const handleEdit = async (useCase: UseCase) => {
    setEditingUseCase(useCase);
    try {
      const detail = await api.guidance.getUseCase(useCase.id);
      setFormData({
        name: detail.data.name,
        display_name: detail.data.display_name,
        description: detail.data.description || '',
        category: detail.data.category || '',
        is_active: detail.data.is_active,
        workflow_ids: (detail.data.workflows || []).map((w) => w.id),
      });
    } catch {
      setFormData({
        name: useCase.name,
        display_name: useCase.display_name,
        description: useCase.description || '',
        category: useCase.category || '',
        is_active: useCase.is_active,
        workflow_ids: (useCase.workflows || []).map((w) => w.id),
      });
    }
    setShowModal(true);
  };

  const handleToggleWorkflow = (workflowId: number) => {
    setFormData((prev) => ({
      ...prev,
      workflow_ids: prev.workflow_ids.includes(workflowId)
        ? prev.workflow_ids.filter((id) => id !== workflowId)
        : [...prev.workflow_ids, workflowId],
    }));
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      setError('Name is required');
      return;
    }
    if (!formData.display_name.trim()) {
      setError('Display name is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editingUseCase) {
        await api.guidance.updateUseCase(editingUseCase.id, {
          display_name: formData.display_name,
          description: formData.description || null,
          category: formData.category || null,
          is_active: formData.is_active,
        });
        await api.guidance.setUseCaseWorkflows(editingUseCase.id, formData.workflow_ids);
      } else {
        const created = await api.guidance.createUseCase({
          name: formData.name,
          display_name: formData.display_name,
          description: formData.description || null,
          category: formData.category || null,
          is_active: formData.is_active,
        });
        if (formData.workflow_ids.length > 0) {
          await api.guidance.setUseCaseWorkflows(created.data.id, formData.workflow_ids);
        }
      }
      setShowModal(false);
      fetchUseCases();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save use case');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (useCase: UseCase) => {
    if (!confirm(`Are you sure you want to delete the use case "${useCase.display_name}"?`)) return;
    try {
      await api.guidance.deleteUseCase(useCase.id);
      fetchUseCases();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete use case');
    }
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
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Use Cases</h1>
            <p className="text-sm text-gray-600 mt-1">
              Group workflows into logical use cases for discovery and organization.
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            New Use Case
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex justify-between items-start">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700 flex-shrink-0">
              Dismiss
            </button>
          </div>
        )}

        <div className="mb-4 flex gap-3">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or description..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
          />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Use Case
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Workflows
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUseCases.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    {searchTerm || categoryFilter
                      ? 'No matching use cases found.'
                      : 'No use cases yet. Click "New Use Case" to create one.'}
                  </td>
                </tr>
              ) : (
                filteredUseCases.map((useCase) => (
                  <tr key={useCase.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{useCase.display_name}</div>
                      <div className="text-xs text-gray-500 mt-0.5 font-mono">{useCase.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600 max-w-xs truncate">
                        {useCase.description || <span className="text-gray-400 italic">No description</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {useCase.category ? (
                        <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                          {useCase.category}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full font-medium">
                        {useCase.workflows_count} workflow{useCase.workflows_count !== 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        useCase.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {useCase.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleEdit(useCase)}
                        className="text-blue-600 hover:text-blue-800 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(useCase)}
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
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                {editingUseCase ? 'Edit Use Case' : 'Create Use Case'}
              </h2>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Internal Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      disabled={!!editingUseCase}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                      placeholder="e.g., vlan-provisioning"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., VLAN Provisioning"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    list="existing-categories"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Networking, Security, Monitoring"
                  />
                  <datalist id="existing-categories">
                    {categories.map((cat) => (
                      <option key={cat} value={cat} />
                    ))}
                  </datalist>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="Describe this use case..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Associated Workflows ({formData.workflow_ids.length} selected)
                  </label>
                  <div className="border border-gray-300 rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                    {workflows.length === 0 ? (
                      <div className="px-3 py-4 text-sm text-gray-500 text-center">
                        No workflows available. Create workflows first.
                      </div>
                    ) : (
                      workflows.map((workflow) => {
                        const selected = formData.workflow_ids.includes(workflow.id);
                        return (
                          <label
                            key={workflow.id}
                            className={`flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-gray-50 border-b border-gray-100 last:border-0 ${
                              selected ? 'bg-blue-50' : ''
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selected}
                              onChange={() => handleToggleWorkflow(workflow.id)}
                              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                            />
                            <span className="flex-1 min-w-0">
                              <span className="text-sm font-medium text-gray-900 block">
                                {workflow.display_name}
                              </span>
                              {workflow.description && (
                                <span className="text-xs text-gray-500 truncate block">
                                  {workflow.description}
                                </span>
                              )}
                            </span>
                            <span className={`text-xs px-1.5 py-0.5 rounded flex-shrink-0 ${
                              workflow.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                            }`}>
                              {workflow.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </label>
                        );
                      })
                    )}
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="usecase_is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="usecase_is_active" className="ml-2 text-sm text-gray-700">
                    Active
                  </label>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => { setShowModal(false); setError(null); }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : editingUseCase ? 'Save Changes' : 'Create Use Case'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
