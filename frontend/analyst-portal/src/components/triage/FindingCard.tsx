'use client';

import { SeverityBadge, ConfidenceBadge } from '@/components/common/Badge';
import { cn } from '@/lib/utils';
import type { Finding } from '@/types/finding';

interface FindingCardProps {
  finding: Finding;
  selected: boolean;
  onToggleSelect: () => void;
  onClick: () => void;
}

export function FindingCard({ finding, selected, onToggleSelect, onClick }: FindingCardProps) {
  return (
    <div
      className={cn(
        'border-b border-gray-100 p-4 transition-colors hover:bg-gray-50',
        selected && 'bg-blue-50',
      )}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={(e) => {
            e.stopPropagation();
            onToggleSelect();
          }}
          className="mt-1 h-4 w-4 rounded border-gray-300"
        />

        <button type="button" className="flex-1 text-left" onClick={onClick}>
          <div className="flex items-center gap-2">
            <SeverityBadge severity={finding.severity} />
            <span className="text-sm font-medium text-gray-500">#{finding.id.slice(0, 6)}</span>
            <span className="font-medium text-gray-900">{finding.title}</span>
          </div>

          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span>{finding.scanner.replace(/_/g, ' ')}</span>
            <span>&middot;</span>
            <span>{finding.asset}</span>
            <span>&middot;</span>
            <span>CVSS {finding.cvssScore}</span>
            {finding.aiConfidence > 0 && finding.aiVerdict && (
              <>
                <span>&middot;</span>
                <ConfidenceBadge confidence={finding.aiConfidence} verdict={finding.aiVerdict} />
              </>
            )}
          </div>

          {finding.aiReasoning && (
            <div className="mt-1.5 rounded bg-gray-50 p-2 text-xs text-gray-600">
              <span className="font-medium">AI: </span>
              {finding.aiReasoning}
            </div>
          )}

          {finding.attackChainIds.length > 0 && (
            <div className="mt-1 text-xs text-purple-600">
              Attack chain: {finding.attackChainIds.length} linked findings
            </div>
          )}
        </button>
      </div>
    </div>
  );
}
