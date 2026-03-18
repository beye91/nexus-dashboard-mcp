'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { ToolProfile, CreateToolProfileRequest, UpdateToolProfileRequest } from '@/types';

interface OperationItem {
  name: string;
  method: string;
  path: string;
  api_name: string;
  description: string;
}

interface OperationsSearchDropdownProps {
  selectedOperations: string[];
  onToggle: (operationName: string) => void;
}

function OperationsSearchDropdown({ selectedOperations, onToggle }: OperationsSearchDropdownProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [operations, setOperations] = useState<OperationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const fetchOperations = useCallback(async (search: string) => {
    try {
      setLoading(true);
      const response = await api.operations.list({ search, limit: 50 });
      setOperations(response.data.operations || []);
    } catch {
      setOperations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchOperations(searchTerm);
    }
  }, [open, searchTerm, fetchOperations]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 flex justify-between items-center"
      >
        <span className="text-sm text-gray-600">
          {selectedOperations.length === 0
            ? 'Select operations...'
            : `${selectedOperations.length} operation${selectedOperations.length !== 1 ? 's' : ''} selected`}
        </span>
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={open ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'} />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search operations..."
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-gray-900"
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {loading ? (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">Loading...</div>
            ) : operations.length === 0 ? (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">No operations found</div>
            ) : (
              operations.map((op) => {
                const selected = selectedOperations.includes(op.name);
                return (
                  <button
                    key={op.name}
                    type="button"
                    onClick={() => onToggle(op.name)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2 ${
                      selected ? 'bg-blue-50' : ''
                    }`}
                  >
                    <span className={`w-4 h-4 border rounded flex items-center justify-center flex-shrink-0 ${
                      selected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
                    }`}>
                      {selected && (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </span>
                    <span className="flex-1 min-w-0">
                      <span className="font-medium text-gray-900 truncate block">{op.name}</span>
                      <span className="text-xs text-gray-500 truncate block">
                        <span className={`inline-block px-1 rounded text-xs mr-1 ${
                          op.method === 'GET' ? 'bg-green-100 text-green-700' :
                          op.method === 'POST' ? 'bg-blue-100 text-blue-700' :
                          op.method === 'PUT' ? 'bg-yellow-100 text-yellow-700' :
                          op.method === 'DELETE' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                        }`}>
                          {op.method}
                        </span>
                        {op.path}
                      </span>
                    </span>
                  </button>
                );
              })
            )}
          </div>
          <div className="p-2 border-t border-gray-200">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="w-full text-center text-sm text-gray-600 hover:text-gray-900 py-1"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ToolProfilesPage() {
  const [profiles, setProfiles] = useState<ToolProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingProfile, setEditingProfile] = useState<ToolProfile | null>(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    max_tools: 50,
    is_active: true,
    operations: [] as string[],
  });

  const fetchProfiles = async () => {
    try {
      setLoading(true);
      const response = await api.toolProfiles.list();
      setProfiles(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load tool profiles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  const filteredProfiles = profiles.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreate = () => {
    setEditingProfile(null);
    setFormData({ name: '', description: '', max_tools: 50, is_active: true, operations: [] });
    setShowModal(true);
  };

  const handleEdit = async (profile: ToolProfile) => {
    setEditingProfile(profile);
    try {
      const detail = await api.toolProfiles.get(profile.id);
      setFormData({
        name: detail.data.name,
        description: detail.data.description || '',
        max_tools: detail.data.max_tools,
        is_active: detail.data.is_active,
        operations: detail.data.operations || [],
      });
    } catch {
      setFormData({
        name: profile.name,
        description: profile.description || '',
        max_tools: profile.max_tools,
        is_active: profile.is_active,
        operations: profile.operations || [],
      });
    }
    setShowModal(true);
  };

  const handleToggleOperation = (operationName: string) => {
    setFormData((prev) => ({
      ...prev,
      operations: prev.operations.includes(operationName)
        ? prev.operations.filter((o) => o !== operationName)
        : [...prev.operations, operationName],
    }));
  };

  const handleRemoveOperation = (operationName: string) => {
    setFormData((prev) => ({
      ...prev,
      operations: prev.operations.filter((o) => o !== operationName),
    }));
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      setError('Profile name is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editingProfile) {
        const updateData: UpdateToolProfileRequest = {
          name: formData.name,
          description: formData.description || undefined,
          max_tools: formData.max_tools,
          is_active: formData.is_active,
        };
        await api.toolProfiles.update(editingProfile.id, updateData);
        await api.toolProfiles.setOperations(editingProfile.id, formData.operations);
      } else {
        const createData: CreateToolProfileRequest = {
          name: formData.name,
          description: formData.description || undefined,
          max_tools: formData.max_tools,
          operations: formData.operations,
        };
        await api.toolProfiles.create(createData);
      }
      setShowModal(false);
      fetchProfiles();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save tool profile');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (profile: ToolProfile) => {
    if (!confirm(`Are you sure you want to delete the profile "${profile.name}"?`)) return;
    try {
      await api.toolProfiles.delete(profile.id);
      fetchProfiles();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete tool profile');
    }
  };

  const handleToggleActive = async (profile: ToolProfile) => {
    try {
      await api.toolProfiles.update(profile.id, { is_active: !profile.is_active });
      fetchProfiles();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to update profile status');
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
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Tool Profiles</h1>
            <p className="text-sm text-gray-600 mt-1">
              Define named sets of operations to control which tools are exposed to users.
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            New Profile
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

        <div className="mb-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or description..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
          />
        </div>

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Profile Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Operations
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max Tools
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
              {filteredProfiles.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    {searchTerm
                      ? 'No matching profiles found.'
                      : 'No tool profiles yet. Click "New Profile" to create one.'}
                  </td>
                </tr>
              ) : (
                filteredProfiles.map((profile) => (
                  <tr key={profile.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{profile.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600 max-w-xs truncate">
                        {profile.description || <span className="text-gray-400 italic">No description</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full font-medium">
                        {profile.operations_count} ops
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {profile.max_tools}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleToggleActive(profile)}
                        className={`px-2 py-1 text-xs font-medium rounded transition ${
                          profile.is_active
                            ? 'bg-green-100 text-green-800 hover:bg-green-200'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {profile.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleEdit(profile)}
                        className="text-blue-600 hover:text-blue-800 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(profile)}
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
                {editingProfile ? 'Edit Tool Profile' : 'Create Tool Profile'}
              </h2>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Profile Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., read-only, network-admin"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="Describe what this profile allows..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Tools</label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={formData.max_tools}
                    onChange={(e) => setFormData({ ...formData, max_tools: parseInt(e.target.value) || 50 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Maximum number of tools to expose from this profile</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Allowed Operations
                  </label>
                  <OperationsSearchDropdown
                    selectedOperations={formData.operations}
                    onToggle={handleToggleOperation}
                  />
                  {formData.operations.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1">
                      {formData.operations.map((op) => (
                        <span
                          key={op}
                          className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs"
                        >
                          {op}
                          <button
                            type="button"
                            onClick={() => handleRemoveOperation(op)}
                            className="text-blue-600 hover:text-blue-900 ml-0.5"
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {editingProfile && (
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active_profile"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="is_active_profile" className="ml-2 text-sm text-gray-700">
                      Active
                    </label>
                  </div>
                )}
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
                  {saving ? 'Saving...' : 'Save Profile'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
