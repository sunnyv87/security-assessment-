'use client';

import { SeverityBreakdown } from './SeverityBreakdown';
import { ScanCoverageChart } from './ScanCoverageChart';
import { FindingsByScanner } from './FindingsByScanner';
import { ActivityFeed } from './ActivityFeed';
import { PageHeader } from '@/components/common/PageHeader';
import { useFindings } from '@/hooks/useFindings';
import { useEngagement } from '@/hooks/useEngagement';
import { useWorkbenchStore } from '@/stores/workbenchStore';

export function ScanResultsDashboard() {
  const activeEngagementId = useWorkbenchStore((s) => s.activeEngagementId);
  const setFilter = useWorkbenchStore((s) => s.setFilter);
  const { summary, activity } = useFindings(activeEngagementId);
  const { scanCoverage } = useEngagement(activeEngagementId);

  if (!activeEngagementId) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">Select an engagement to view scan results</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scan Results Dashboard"
        description="Overview of findings across all scanners"
      />

      {summary && (
        <SeverityBreakdown
          summary={summary}
          onSeverityClick={(severity) => setFilter('severity', [severity as 'critical'])}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <ScanCoverageChart coverage={scanCoverage || []} />
        <FindingsByScanner scannerCounts={summary?.byScanner || {}} />
      </div>

      <ActivityFeed events={activity || []} />
    </div>
  );
}
