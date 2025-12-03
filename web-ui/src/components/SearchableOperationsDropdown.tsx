'use client';

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { api } from '@/lib/api-client';
import type { Operation, OperationsGrouped } from '@/types';

interface Props {
  selectedOperations: string[];
  onChange: (operations: string[]) => void;
  disabled?: boolean;
  maxHeight?: number;
}

interface GroupedOperations {
  [apiName: string]: Operation[];
}

export default function SearchableOperationsDropdown({
  selectedOperations,
  onChange,
  disabled = false,
  maxHeight = 400,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [operations, setOperations] = useState<GroupedOperations>({});
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Fetch operations on mount
  useEffect(() => {
    const fetchOperations = async () => {
      try {
        setLoading(true);
        const response = await api.operations.grouped();
        setOperations(response.data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch operations:', err);
        setError('Failed to load operations');
      } finally {
        setLoading(false);
      }
    };
    fetchOperations();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Filter operations based on search term
  const filteredOperations = useMemo(() => {
    if (!searchTerm.trim()) return operations;

    const term = searchTerm.toLowerCase();
    const filtered: GroupedOperations = {};

    Object.entries(operations).forEach(([apiName, ops]) => {
      const matchingOps = ops.filter(
        op =>
          op.name.toLowerCase().includes(term) ||
          op.description.toLowerCase().includes(term) ||
          op.method.toLowerCase().includes(term) ||
          op.path.toLowerCase().includes(term)
      );
      if (matchingOps.length > 0) {
        filtered[apiName] = matchingOps;
      }
    });

    return filtered;
  }, [operations, searchTerm]);

  // Count total and selected operations
  const totalOperations = useMemo(() => {
    return Object.values(operations).reduce((sum, ops) => sum + ops.length, 0);
  }, [operations]);

  const selectedCount = selectedOperations.length;

  // Toggle operation selection
  const toggleOperation = useCallback((opName: string) => {
    if (selectedOperations.includes(opName)) {
      onChange(selectedOperations.filter(o => o !== opName));
    } else {
      onChange([...selectedOperations, opName]);
    }
  }, [selectedOperations, onChange]);

  // Select/deselect all in a group
  const toggleGroup = useCallback((apiName: string, ops: Operation[]) => {
    const opNames = ops.map(o => o.name);
    const allSelected = opNames.every(name => selectedOperations.includes(name));

    if (allSelected) {
      // Deselect all in group
      onChange(selectedOperations.filter(o => !opNames.includes(o)));
    } else {
      // Select all in group
      const newSelected = [...new Set([...selectedOperations, ...opNames])];
      onChange(newSelected);
    }
  }, [selectedOperations, onChange]);

  // Select/deselect all operations
  const toggleAll = useCallback(() => {
    if (selectedCount === totalOperations) {
      onChange([]);
    } else {
      const allOps = Object.values(operations).flat().map(o => o.name);
      onChange(allOps);
    }
  }, [selectedCount, totalOperations, operations, onChange]);

  // Toggle group expansion
  const toggleGroupExpansion = useCallback((apiName: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(apiName)) {
        next.delete(apiName);
      } else {
        next.add(apiName);
      }
      return next;
    });
  }, []);

  // Remove a selected operation (chip click)
  const removeOperation = useCallback((opName: string) => {
    onChange(selectedOperations.filter(o => o !== opName));
  }, [selectedOperations, onChange]);

  // Get method color
  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'text-green-600';
      case 'POST': return 'text-blue-600';
      case 'PUT': return 'text-yellow-600';
      case 'PATCH': return 'text-orange-600';
      case 'DELETE': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 bg-white">
        <div className="animate-pulse flex items-center">
          <div className="h-4 w-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-200 rounded-lg p-4 bg-white">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div ref={dropdownRef} className="relative">
      {/* Selected Operations Display */}
      <div
        className={`border rounded-lg p-3 bg-white cursor-pointer transition-colors ${
          disabled ? 'border-gray-200 opacity-50 cursor-not-allowed' : 'border-gray-300 hover:border-gray-400'
        } ${isOpen ? 'border-blue-500 ring-2 ring-blue-100' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">
            {selectedCount} of {totalOperations} operations selected
          </span>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        {/* Selected chips (show first 5) */}
        {selectedCount > 0 && (
          <div className="flex flex-wrap gap-1">
            {selectedOperations.slice(0, 5).map(opName => (
              <span
                key={opName}
                className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-700 border border-blue-200"
                onClick={e => {
                  e.stopPropagation();
                  removeOperation(opName);
                }}
              >
                {opName}
                <svg className="w-3 h-3 ml-1 cursor-pointer hover:text-blue-900" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </span>
            ))}
            {selectedCount > 5 && (
              <span className="text-xs text-gray-500 self-center">+{selectedCount - 5} more</span>
            )}
          </div>
        )}
      </div>

      {/* Dropdown Panel */}
      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-xl">
          {/* Search Input */}
          <div className="p-3 border-b border-gray-200">
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search operations..."
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Select All / Clear All */}
          <div className="px-3 py-2 border-b border-gray-200 flex justify-between items-center">
            <button
              className="text-xs text-blue-600 hover:text-blue-800"
              onClick={toggleAll}
            >
              {selectedCount === totalOperations ? 'Clear All' : 'Select All'}
            </button>
            <span className="text-xs text-gray-500">
              {Object.keys(filteredOperations).length} API groups
            </span>
          </div>

          {/* Operations List */}
          <div className="overflow-y-auto" style={{ maxHeight: `${maxHeight}px` }}>
            {Object.entries(filteredOperations).map(([apiName, ops]) => {
              const isExpanded = expandedGroups.has(apiName);
              const groupSelected = ops.filter(o => selectedOperations.includes(o.name)).length;
              const allGroupSelected = groupSelected === ops.length;
              const someGroupSelected = groupSelected > 0 && groupSelected < ops.length;

              return (
                <div key={apiName} className="border-b border-gray-100 last:border-b-0">
                  {/* Group Header */}
                  <div
                    className="flex items-center justify-between px-3 py-2 bg-gray-50 cursor-pointer hover:bg-gray-100"
                    onClick={() => toggleGroupExpansion(apiName)}
                  >
                    <div className="flex items-center space-x-2">
                      <svg
                        className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <span className="text-sm font-medium text-gray-900">{apiName}</span>
                      <span className="text-xs text-gray-500">({ops.length})</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">{groupSelected}/{ops.length}</span>
                      <button
                        className="text-xs text-blue-600 hover:text-blue-800"
                        onClick={e => {
                          e.stopPropagation();
                          toggleGroup(apiName, ops);
                        }}
                      >
                        {allGroupSelected ? 'Clear' : 'Select All'}
                      </button>
                    </div>
                  </div>

                  {/* Group Operations */}
                  {isExpanded && (
                    <div className="bg-white">
                      {ops.map(op => {
                        const isSelected = selectedOperations.includes(op.name);
                        return (
                          <div
                            key={op.name}
                            className={`flex items-center px-6 py-2 cursor-pointer border-l-2 transition-colors ${
                              isSelected
                                ? 'bg-blue-50 border-blue-500'
                                : 'border-transparent hover:bg-gray-50'
                            }`}
                            onClick={() => toggleOperation(op.name)}
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {}}
                              className="mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2">
                                <span className={`text-xs font-mono ${getMethodColor(op.method)}`}>
                                  {op.method}
                                </span>
                                <span className="text-sm text-gray-900 truncate">{op.name}</span>
                              </div>
                              <p className="text-xs text-gray-500 truncate">{op.path}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

            {Object.keys(filteredOperations).length === 0 && (
              <div className="p-4 text-center text-gray-500">
                No operations found matching "{searchTerm}"
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
