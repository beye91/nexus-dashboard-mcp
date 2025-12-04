'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { SystemPromptSection } from '@/types';

export default function SystemPromptPage() {
  const [sections, setSections] = useState<SystemPromptSection[]>([]);
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingSection, setEditingSection] = useState<SystemPromptSection | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [formData, setFormData] = useState({
    section_name: '',
    section_order: 0,
    title: '',
    content: '',
    is_active: true,
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sectionsRes, promptRes] = await Promise.all([
        api.guidance.listSystemPromptSections(),
        api.guidance.getGeneratedSystemPrompt(),
      ]);
      setSections(sectionsRes.data);
      setGeneratedPrompt(promptRes.data.prompt);
    } catch (err: any) {
      setError(err.message || 'Failed to load system prompt data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleEdit = (section: SystemPromptSection) => {
    setEditingSection(section);
    setFormData({
      section_name: section.section_name,
      section_order: section.section_order,
      title: section.title || '',
      content: section.content,
      is_active: section.is_active,
    });
    setShowModal(true);
  };

  const handleCreate = () => {
    setEditingSection(null);
    const maxOrder = sections.reduce((max, s) => Math.max(max, s.section_order), 0);
    setFormData({
      section_name: '',
      section_order: maxOrder + 10,
      title: '',
      content: '',
      is_active: true,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      await api.guidance.upsertSystemPromptSection(formData.section_name, {
        section_order: formData.section_order,
        title: formData.title,
        content: formData.content,
        is_active: formData.is_active,
      });
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to save section');
    }
  };

  const handleDelete = async (sectionName: string) => {
    if (!confirm('Are you sure you want to delete this section?')) return;
    try {
      await api.guidance.deleteSystemPromptSection(sectionName);
      fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to delete section');
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
        <h1 className="text-2xl font-bold text-gray-900">System Prompt Configuration</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className={`px-4 py-2 rounded-lg ${
              showPreview
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {showPreview ? 'Hide Preview' : 'Show Preview'}
          </button>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Section
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sections Editor */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sections</h2>
          <div className="space-y-3">
            {sections.sort((a, b) => a.section_order - b.section_order).map((section) => (
              <div
                key={section.id}
                className={`p-4 rounded-lg border ${
                  section.is_active ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-200 opacity-60'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-xs text-gray-500 font-mono">Order: {section.section_order}</span>
                    <h3 className="font-medium text-gray-900">{section.title || section.section_name}</h3>
                    <span className="text-xs text-gray-500">{section.section_name}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded ${
                      section.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600'
                    }`}>
                      {section.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{section.content}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(section)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(section.section_name)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
            {sections.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No sections configured. Click "Add Section" to create one.
              </div>
            )}
          </div>
        </div>

        {/* Preview */}
        {showPreview && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Generated Prompt Preview</h2>
            <div className="bg-gray-100 border border-gray-300 rounded-lg p-4 text-gray-900 font-mono text-sm overflow-auto max-h-[600px]">
              <pre className="whitespace-pre-wrap">{generatedPrompt || 'No prompt generated yet.'}</pre>
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(generatedPrompt);
                alert('Copied to clipboard!');
              }}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800"
            >
              Copy to Clipboard
            </button>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {editingSection ? 'Edit Section' : 'Add Section'}
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Section Name (ID)</label>
                  <input
                    type="text"
                    value={formData.section_name}
                    onChange={(e) => setFormData({ ...formData, section_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    disabled={!!editingSection}
                    placeholder="e.g., api_overview"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Order</label>
                  <input
                    type="number"
                    value={formData.section_order}
                    onChange={(e) => setFormData({ ...formData, section_order: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="Section title (displayed in prompt)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                  rows={10}
                  placeholder="The actual content of this section..."
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">Active (include in generated prompt)</label>
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
