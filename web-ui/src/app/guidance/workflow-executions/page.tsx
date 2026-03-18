'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import { api } from '@/lib/api-client';
import type { WorkflowExecution, Workflow } from '@/types';

function StatusBadge({ status }: { status: WorkflowExecution['status'] }) {
  const styles: Record<WorkflowExecution['status'], string> = {
    running: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-600',
  };
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded ${styles[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function StepStatusBadge({ status }: { status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' }) {
  const styles: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    running: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    skipped: 'bg-blue-100 text-blue-700',
  };
  return (
    <span className={`px-1.5 py-0.5 text-xs rounded ${styles[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString();
}

function durationSeconds(started: string | null, completed: string | null): string {
  if (!started || !completed) return '-';
  const ms = new Date(completed).getTime() - new Date(started).getTime();
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function WorkflowExecutionsPage() {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workflowFilter, setWorkflowFilter] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedExecution, setExpandedExecution] = useState<WorkflowExecution | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchExecutions = async (workflowId?: number) => {
    try {
      setLoading(true);
      const response = await api.guidance.listWorkflowExecutions(workflowId, 100);
      setExecutions(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load workflow executions');
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const response = await api.guidance.listWorkflows();
      setWorkflows(response.data);
    } catch {
      // non-critical
    }
  };

  useEffect(() => {
    fetchWorkflows();
    fetchExecutions();
  }, []);

  const handleWorkflowFilterChange = (value: string) => {
    setWorkflowFilter(value);
    fetchExecutions(value ? parseInt(value) : undefined);
  };

  const handleToggleExpand = async (execution: WorkflowExecution) => {
    if (expandedId === execution.id) {
      setExpandedId(null);
      setExpandedExecution(null);
      return;
    }
    setExpandedId(execution.id);
    setLoadingDetail(true);
    try {
      const detail = await api.guidance.getWorkflowExecution(execution.id);
      setExpandedExecution(detail.data);
    } catch {
      setExpandedExecution(execution);
    } finally {
      setLoadingDetail(false);
    }
  };

  const getWorkflowName = (workflowId: number): string => {
    const wf = workflows.find((w) => w.id === workflowId);
    return wf ? wf.display_name : `Workflow #${workflowId}`;
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
            <h1 className="text-2xl font-bold text-gray-900">Workflow Execution History</h1>
            <p className="text-sm text-gray-600 mt-1">
              View the history of workflow executions and step-by-step results.
            </p>
          </div>
          <button
            onClick={() => fetchExecutions(workflowFilter ? parseInt(workflowFilter) : undefined)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
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
          <select
            value={workflowFilter}
            onChange={(e) => handleWorkflowFilterChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
          >
            <option value="">All Workflows</option>
            {workflows.map((wf) => (
              <option key={wf.id} value={wf.id.toString()}>
                {wf.display_name}
              </option>
            ))}
          </select>
        </div>

        {executions.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 px-6 py-12 text-center text-gray-500">
            No execution records found.
            {workflowFilter && (
              <button
                onClick={() => handleWorkflowFilterChange('')}
                className="block mx-auto mt-2 text-blue-600 hover:text-blue-700 text-sm"
              >
                Clear filter
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {executions.map((execution) => {
              const isExpanded = expandedId === execution.id;
              return (
                <div
                  key={execution.id}
                  className="bg-white rounded-lg border border-gray-200 overflow-hidden"
                >
                  <button
                    onClick={() => handleToggleExpand(execution)}
                    className="w-full text-left"
                  >
                    <div className="px-6 py-4 flex items-center gap-4 hover:bg-gray-50 transition">
                      <svg
                        className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>

                      <div className="flex-1 min-w-0 grid grid-cols-5 gap-4 items-center">
                        <div className="col-span-2 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {getWorkflowName(execution.workflow_id)}
                          </div>
                          <div className="text-xs text-gray-500">ID #{execution.id}</div>
                        </div>

                        <div>
                          <StatusBadge status={execution.status} />
                        </div>

                        <div className="text-sm text-gray-600">
                          <div className="text-xs text-gray-400">Started</div>
                          {formatDate(execution.started_at)}
                        </div>

                        <div className="text-sm text-gray-600">
                          <div className="text-xs text-gray-400">Duration</div>
                          {durationSeconds(execution.started_at, execution.completed_at)}
                        </div>
                      </div>

                      {execution.error_message && (
                        <div className="flex-shrink-0 max-w-xs">
                          <span className="text-xs text-red-600 truncate block">
                            {execution.error_message}
                          </span>
                        </div>
                      )}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
                      {loadingDetail && expandedId === execution.id ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                          <span className="ml-2 text-sm text-gray-500">Loading steps...</span>
                        </div>
                      ) : (
                        <>
                          <div className="mb-3 grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500 block text-xs">User ID</span>
                              <span className="text-gray-900">
                                {expandedExecution?.user_id ?? execution.user_id ?? '-'}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 block text-xs">Completed At</span>
                              <span className="text-gray-900">
                                {formatDate((expandedExecution ?? execution).completed_at)}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 block text-xs">Started At</span>
                              <span className="text-gray-900">
                                {formatDate((expandedExecution ?? execution).started_at)}
                              </span>
                            </div>
                          </div>

                          {(expandedExecution ?? execution).error_message && (
                            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                              <div className="text-xs font-medium text-red-700 mb-1">Error</div>
                              <div className="text-sm text-red-600">
                                {(expandedExecution ?? execution).error_message}
                              </div>
                            </div>
                          )}

                          {(expandedExecution?.step_executions ?? []).length > 0 ? (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Step Executions</h4>
                              <div className="space-y-2">
                                {(expandedExecution?.step_executions ?? []).map((step) => (
                                  <div
                                    key={step.id}
                                    className="bg-white rounded border border-gray-200 p-3"
                                  >
                                    <div className="flex items-center gap-3">
                                      <span className="text-xs text-gray-500 font-medium w-14 flex-shrink-0">
                                        Step {step.step_order}
                                      </span>
                                      <span className="text-sm font-medium text-gray-900 flex-1 min-w-0 truncate">
                                        {step.operation_name}
                                      </span>
                                      <StepStatusBadge status={step.status} />
                                      <span className="text-xs text-gray-500 flex-shrink-0">
                                        {durationSeconds(step.started_at, step.completed_at)}
                                      </span>
                                    </div>
                                    {step.error_message && (
                                      <div className="mt-1.5 text-xs text-red-600 pl-[4.25rem]">
                                        {step.error_message}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 text-center py-2">
                              No step execution details available.
                            </p>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
