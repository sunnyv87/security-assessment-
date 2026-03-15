'use client';

import { useRouter } from 'next/navigation';
import { FindingCard } from './FindingCard';
import { BulkActions } from './BulkActions';
import { TriageFilters } from './TriageFilters';
import { Pagination } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { EmptyState } from '@/components/common/EmptyState';
import { useFindings } from '@/hooks/useFindings';
import { useWorkbenchStore } from '@/stores/workbenchStore';

export function FindingTriage() {
  const router = useRouter();
  const activeEngagementId = useWorkbenchStore((s) => s.activeEngagementId);
  const { selectedFindingIds, toggleFindingSelection, selectAllFindings, clearSelection, filters, setFilter } =
    useWorkbenchStore();
  const { findings, isLoading } = useFindings(activeEngagementId);

  if (!activeEngagementId) {
    return (
      <EmptyState
        title="No Engagement Selected"
        description="Select an engagement from the sidebar to begin triaging findings."
      />
    );
  }

  const data = findings?.data || [];
  const allSelected = data.length > 0 && data.every((f) => selectedFindingIds.has(f.id));

  return (
    <div className="flex gap-6">
      {/* Filter sidebar */}
      <div className="hidden w-56 shrink-0 lg:block">
        <TriageFilters />
      </div>

      {/* Main content */}
      <div className="flex-1 space-y-4">
        <PageHeader
          title="Finding Triage"
          description={`${findings?.total || 0} findings to review`}
        />

        <BulkActions />

        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          {/* Select all header */}
          <div className="flex items-center gap-3 border-b border-gray-200 bg-gray-50 px-4 py-2">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={() => {
                if (allSelected) clearSelection();
                else selectAllFindings(data.map((f) => f.id));
              }}
              className="h-4 w-4 rounded border-gray-300"
            />
            <span className="text-xs font-medium text-gray-500">
              {allSelected ? 'Deselect all' : 'Select all'}
            </span>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <span className="text-sm text-gray-500">Loading findings...</span>
            </div>
          ) : data.length === 0 ? (
            <div className="py-12 text-center text-sm text-gray-500">
              No findings match your filters
            </div>
          ) : (
            data.map((finding) => (
              <FindingCard
                key={finding.id}
                finding={finding}
                selected={selectedFindingIds.has(finding.id)}
                onToggleSelect={() => toggleFindingSelection(finding.id)}
                onClick={() => router.push(`/workbench/findings/${finding.id}`)}
              />
            ))
          )}

          {findings && findings.totalPages > 1 && (
            <Pagination
              page={filters.page}
              totalPages={findings.totalPages}
              onPageChange={(page) => setFilter('page', page)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
