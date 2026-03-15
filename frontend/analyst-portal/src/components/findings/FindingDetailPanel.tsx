'use client';

import { FindingTabs } from './FindingTabs';
import { PageHeader } from '@/components/common/PageHeader';
import { SeverityBadge, StatusBadge } from '@/components/common/Badge';
import { useFindings } from '@/hooks/useFindings';
import Link from 'next/link';

interface FindingDetailPanelProps {
  findingId: string;
}

export function FindingDetailPanel({ findingId }: FindingDetailPanelProps) {
  const { finding, isLoadingFinding } = useFindings(null, findingId);

  if (isLoadingFinding) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="text-sm text-gray-500">Loading finding details...</span>
      </div>
    );
  }

  if (!finding) {
    return (
      <div className="flex h-64 items-center justify-center">
        <span className="text-sm text-gray-500">Finding not found</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href="/workbench/triage" className="text-sm text-blue-600 hover:underline">
          &larr; Back to Triage
        </Link>
      </div>

      <PageHeader
        title={finding.title}
        description={`Finding #${finding.id.slice(0, 8)}`}
        actions={
          <div className="flex items-center gap-2">
            <SeverityBadge severity={finding.severity} />
            <StatusBadge status={finding.status} />
          </div>
        }
      />

      <FindingTabs finding={finding} />
    </div>
  );
}
