'use client';

import { useWorkbenchStore } from '@/stores/workbenchStore';
import { useTriage } from '@/hooks/useTriage';
import type { FindingStatus, Severity } from '@/types/finding';

export function BulkActions() {
  const { selectedFindingIds, clearSelection } = useWorkbenchStore();
  const { bulkUpdate } = useTriage();
  const count = selectedFindingIds.size;

  if (count === 0) return null;

  const handleBulkStatus = (status: FindingStatus) => {
    bulkUpdate.mutate(
      { findingIds: Array.from(selectedFindingIds), update: { status } },
      { onSuccess: clearSelection },
    );
  };

  const handleBulkSeverity = (severity: Severity) => {
    bulkUpdate.mutate(
      { findingIds: Array.from(selectedFindingIds), update: { severity } },
      { onSuccess: clearSelection },
    );
  };

  return (
    <div className="flex items-center gap-3 rounded-lg bg-blue-50 px-4 py-2">
      <span className="text-sm font-medium text-blue-700">{count} selected</span>

      <div className="flex items-center gap-2">
        <select
          defaultValue=""
          onChange={(e) => {
            if (e.target.value) handleBulkStatus(e.target.value as FindingStatus);
            e.target.value = '';
          }}
          className="rounded border border-blue-200 bg-white px-2 py-1 text-sm"
        >
          <option value="" disabled>Set Status...</option>
          <option value="validated">Validated</option>
          <option value="false_positive">False Positive</option>
          <option value="duplicate">Duplicate</option>
          <option value="requires_retest">Requires Retest</option>
        </select>

        <select
          defaultValue=""
          onChange={(e) => {
            if (e.target.value) handleBulkSeverity(e.target.value as Severity);
            e.target.value = '';
          }}
          className="rounded border border-blue-200 bg-white px-2 py-1 text-sm"
        >
          <option value="" disabled>Set Severity...</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
      </div>

      <button
        type="button"
        onClick={clearSelection}
        className="ml-auto text-sm text-blue-600 hover:underline"
      >
        Clear selection
      </button>
    </div>
  );
}
