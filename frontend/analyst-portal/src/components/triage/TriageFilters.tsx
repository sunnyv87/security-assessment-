'use client';

import { useWorkbenchStore } from '@/stores/workbenchStore';
import type { Severity, FindingStatus } from '@/types/finding';

const severities: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];
const statuses: FindingStatus[] = ['new', 'in_review', 'validated', 'false_positive', 'duplicate', 'requires_retest'];
const scanners = ['burp_suite', 'nuclei', 'fortify', 'tenable', 'nmap', 'zap', 'trivy'];

export function TriageFilters() {
  const { filters, setFilter, resetFilters } = useWorkbenchStore();

  const toggleArrayFilter = <K extends 'severity' | 'status' | 'scanner'>(
    key: K,
    value: string,
  ) => {
    const current = filters[key] as string[];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    setFilter(key, next as typeof filters[K]);
  };

  return (
    <div className="space-y-4">
      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Search findings..."
          value={filters.search}
          onChange={(e) => setFilter('search', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Severity */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase text-gray-500">Severity</p>
        <div className="space-y-1">
          {severities.map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={filters.severity.includes(s)}
                onChange={() => toggleArrayFilter('severity', s)}
                className="h-3.5 w-3.5 rounded border-gray-300"
              />
              <span className="capitalize">{s}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Status */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase text-gray-500">Status</p>
        <div className="space-y-1">
          {statuses.map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={filters.status.includes(s)}
                onChange={() => toggleArrayFilter('status', s)}
                className="h-3.5 w-3.5 rounded border-gray-300"
              />
              <span className="capitalize">{s.replace(/_/g, ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Scanner */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase text-gray-500">Scanner</p>
        <div className="space-y-1">
          {scanners.map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={filters.scanner.includes(s)}
                onChange={() => toggleArrayFilter('scanner', s)}
                className="h-3.5 w-3.5 rounded border-gray-300"
              />
              <span>{s.replace(/_/g, ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Sort */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase text-gray-500">Sort by</p>
        <select
          value={filters.sortBy}
          onChange={(e) => setFilter('sortBy', e.target.value)}
          className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
        >
          <option value="aiConfidence">AI Priority</option>
          <option value="cvssScore">CVSS Score</option>
          <option value="createdAt">Date Found</option>
          <option value="severity">Severity</option>
        </select>
      </div>

      <button
        type="button"
        onClick={resetFilters}
        className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
      >
        Reset Filters
      </button>
    </div>
  );
}
