'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { Workflow, WorkflowStep } from '@/types';

interface StepForm {
  step_order: number;
  operation_name: string;
  description: string;
  expected_output: string;
  optional: boolean;
  fallback_operation: string;
}

export default function WorkflowDetailPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = parseInt(params.id as string);

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [steps, setSteps] = useState<StepForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [tagInput, setTagInput] = useState('');

  const [workflowForm, setWorkflowForm] = useState({
    display_name: '',
    description: '',
    problem_statement: '',
    use_case_tags: [] as string[],
    is_active: true,
    priority: 0,
  });

  useEffect(() => {
    if (workflowId) {
      fetchWorkflow();
    }
  }, [workflowId]);

  async function fetchWorkflow() {
    try {
      setLoading(true);
      const response = await api.guidance.getWorkflow(workflowId);
      setWorkflow(response.data);
      setWorkflowForm({
        display_name: response.data.display_name,
        description: response.data.description || '',
        problem_statement: response.data.problem_statement || '',
        use_case_tags: response.data.use_case_tags || [],
        is_active: response.data.is_active,
        priority: response.data.priority,
      });

      // Convert workflow steps to form data
      if (response.data.steps) {
        setSteps(
          response.data.steps.map((step: WorkflowStep) => ({
            step_order: step.step_order,
            operation_name: step.operation_name,
            description: step.description || '',
            expected_output: step.expected_output || '',
            optional: step.optional,
            fallback_operation: step.fallback_operation || '',
          }))
        );
      }
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch workflow:', err);
      setError(err.response?.data?.detail || 'Failed to load workflow');
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateWorkflow(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      await api.guidance.updateWorkflow(workflowId, workflowForm);
      setSuccess('Workflow updated successfully');
      setTimeout(() => setSuccess(null), 3000);
      await fetchWorkflow();
      setShowEditModal(false);
    } catch (err: any) {
      console.error('Failed to update workflow:', err);
      setError(err.response?.data?.detail || 'Failed to update workflow');
    }
  }

  async function handleSaveSteps() {
    setError(null);

    try {
      // Sort steps by step_order and clean up the data
      const sortedSteps = steps
        .sort((a, b) => a.step_order - b.step_order)
        .map(step => ({
          step_order: step.step_order,
          operation_name: step.operation_name,
          description: step.description || null,
          expected_output: step.expected_output || null,
          optional: step.optional,
          fallback_operation: step.fallback_operation || null,
        }));

      await api.guidance.setWorkflowSteps(workflowId, sortedSteps);
      setSuccess('Workflow steps saved successfully');
      setTimeout(() => setSuccess(null), 3000);
      await fetchWorkflow();
    } catch (err: any) {
      console.error('Failed to save steps:', err);
      setError(err.response?.data?.detail || 'Failed to save workflow steps');
    }
  }

  function handleAddStep() {
    const newStepOrder = steps.length > 0 ? Math.max(...steps.map(s => s.step_order)) + 1 : 1;
    setSteps([
      ...steps,
      {
        step_order: newStepOrder,
        operation_name: '',
        description: '',
        expected_output: '',
        optional: false,
        fallback_operation: '',
      },
    ]);
  }

  function handleRemoveStep(index: number) {
    setSteps(steps.filter((_, i) => i !== index));
  }

  function handleUpdateStep(index: number, field: keyof StepForm, value: any) {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  }

  function handleMoveStepUp(index: number) {
    if (index === 0) return;
    const newSteps = [...steps];
    [newSteps[index - 1], newSteps[index]] = [newSteps[index], newSteps[index - 1]];
    // Update step_order
    newSteps.forEach((step, i) => {
      step.step_order = i + 1;
    });
    setSteps(newSteps);
  }

  function handleMoveStepDown(index: number) {
    if (index === steps.length - 1) return;
    const newSteps = [...steps];
    [newSteps[index], newSteps[index + 1]] = [newSteps[index + 1], newSteps[index]];
    // Update step_order
    newSteps.forEach((step, i) => {
      step.step_order = i + 1;
    });
    setSteps(newSteps);
  }

  function handleAddTag() {
    if (tagInput.trim() && !workflowForm.use_case_tags.includes(tagInput.trim())) {
      setWorkflowForm({
        ...workflowForm,
        use_case_tags: [...workflowForm.use_case_tags, tagInput.trim()],
      });
      setTagInput('');
    }
  }

  function handleRemoveTag(tag: string) {
    setWorkflowForm({
      ...workflowForm,
      use_case_tags: workflowForm.use_case_tags.filter(t => t !== tag),
    });
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading workflow...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <p className="text-red-600">Workflow not found</p>
            <button
              onClick={() => router.push('/guidance/workflows')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Back to Workflows
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <button
            onClick={() => router.push('/guidance/workflows')}
            className="text-sm text-gray-600 hover:text-gray-900 mb-4 flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Workflows
          </button>

          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{workflow.display_name}</h2>
              <p className="text-gray-600">{workflow.description}</p>
              {workflow.problem_statement && (
                <p className="text-sm text-gray-500 mt-2">Problem: {workflow.problem_statement}</p>
              )}
              <div className="flex flex-wrap gap-2 mt-2">
                {workflow.use_case_tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <button
              onClick={() => setShowEditModal(true)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition"
            >
              Edit Details
            </button>
          </div>
        </div>

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            {success}
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Workflow Steps</h3>
            <div className="flex gap-3">
              <button
                onClick={handleAddStep}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition flex items-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Step
              </button>
              <button
                onClick={handleSaveSteps}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
              >
                Save Steps
              </button>
            </div>
          </div>

          {steps.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No steps defined yet. Click "Add Step" to get started.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-2">
                      <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                        Step {index + 1}
                      </span>
                      {step.optional && (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">
                          Optional
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleMoveStepUp(index)}
                        disabled={index === 0}
                        className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-30"
                        title="Move up"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleMoveStepDown(index)}
                        disabled={index === steps.length - 1}
                        className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-30"
                        title="Move down"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleRemoveStep(index)}
                        className="p-1 text-red-500 hover:text-red-700"
                        title="Remove step"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Operation Name
                      </label>
                      <input
                        type="text"
                        required
                        value={step.operation_name}
                        onChange={(e) => handleUpdateStep(index, 'operation_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        placeholder="e.g., list_sites"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <textarea
                        rows={2}
                        value={step.description}
                        onChange={(e) => handleUpdateStep(index, 'description', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        placeholder="What does this step do?"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Expected Output
                      </label>
                      <input
                        type="text"
                        value={step.expected_output}
                        onChange={(e) => handleUpdateStep(index, 'expected_output', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        placeholder="What should this return?"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Fallback Operation
                      </label>
                      <input
                        type="text"
                        value={step.fallback_operation}
                        onChange={(e) => handleUpdateStep(index, 'fallback_operation', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                        placeholder="Alternative if this fails"
                      />
                    </div>

                    <div className="col-span-2 flex items-center">
                      <input
                        type="checkbox"
                        id={`optional-${index}`}
                        checked={step.optional}
                        onChange={(e) => handleUpdateStep(index, 'optional', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor={`optional-${index}`} className="ml-2 block text-sm text-gray-700">
                        This step is optional
                      </label>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 my-8 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Edit Workflow Details
            </h3>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleUpdateWorkflow}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    required
                    value={workflowForm.display_name}
                    onChange={(e) => setWorkflowForm({ ...workflowForm, display_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    value={workflowForm.description}
                    onChange={(e) => setWorkflowForm({ ...workflowForm, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Problem Statement
                  </label>
                  <textarea
                    rows={3}
                    value={workflowForm.problem_statement}
                    onChange={(e) => setWorkflowForm({ ...workflowForm, problem_statement: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Use Case Tags
                  </label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddTag();
                        }
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                      placeholder="Add tag and press Enter"
                    />
                    <button
                      type="button"
                      onClick={handleAddTag}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Add
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {workflowForm.use_case_tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm flex items-center"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-2 text-blue-900 hover:text-blue-700"
                        >
                          &times;
                        </button>
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Priority
                    </label>
                    <input
                      type="number"
                      value={workflowForm.priority}
                      onChange={(e) => setWorkflowForm({ ...workflowForm, priority: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={workflowForm.is_active}
                      onChange={(e) => setWorkflowForm({ ...workflowForm, is_active: e.target.checked })}
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
                  onClick={() => setShowEditModal(false)}
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
    </div>
  );
}
