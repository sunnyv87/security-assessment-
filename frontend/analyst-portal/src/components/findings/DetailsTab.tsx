'use client';

import { Card, CardHeader } from '@/components/common/Card';
import { SeverityBadge, StatusBadge } from '@/components/common/Badge';
import { EvidenceViewer } from './EvidenceViewer';
import { AiAnalysisCard } from './AiAnalysisCard';
import type { Finding } from '@/types/finding';

interface DetailsTabProps {
  finding: Finding;
}

export function DetailsTab({ finding }: DetailsTabProps) {
  return (
    <div className="space-y-6">
      {/* Metadata grid */}
      <Card>
        <CardHeader title="Finding Details" />
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm lg:grid-cols-3">
          <div>
            <span className="font-medium text-gray-500">Status</span>
            <div className="mt-1">
              <StatusBadge status={finding.status} />
            </div>
          </div>
          <div>
            <span className="font-medium text-gray-500">Severity</span>
            <div className="mt-1">
              <SeverityBadge severity={finding.severity} />
            </div>
          </div>
          <div>
            <span className="font-medium text-gray-500">CVSS</span>
            <p className="mt-1 text-gray-900">{finding.cvssScore} ({finding.cvssVector})</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Category</span>
            <p className="mt-1 text-gray-900">{finding.cweId} - {finding.cweName}</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Scanner</span>
            <p className="mt-1 text-gray-900">{finding.scanner.replace(/_/g, ' ')}</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Assignee</span>
            <p className="mt-1 text-gray-900">{finding.assigneeName || 'Unassigned'}</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Asset</span>
            <p className="mt-1 text-gray-900">{finding.asset}</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Endpoint</span>
            <p className="mt-1 font-mono text-gray-900">
              {finding.httpMethod} {finding.endpoint}
            </p>
          </div>
        </div>
      </Card>

      {/* Description */}
      <Card>
        <CardHeader title="Description" />
        <p className="mt-3 text-sm leading-relaxed text-gray-700">{finding.description}</p>
      </Card>

      {/* Evidence */}
      {finding.evidence && (
        <Card>
          <CardHeader title="Evidence (from scanner)" />
          <div className="mt-4">
            <EvidenceViewer evidence={finding.evidence} />
          </div>
        </Card>
      )}

      {/* AI Analysis */}
      {finding.aiConfidence > 0 && (
        <AiAnalysisCard
          confidence={finding.aiConfidence}
          verdict={finding.aiVerdict}
          reasoning={finding.aiReasoning}
          attackChainIds={finding.attackChainIds}
        />
      )}
    </div>
  );
}
