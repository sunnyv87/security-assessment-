'use client';

import { Card, CardHeader } from '@/components/common/Card';
import { cn } from '@/lib/utils';
import type { ValidationVerdict } from '@/types/finding';

interface AiAnalysisCardProps {
  confidence: number;
  verdict: ValidationVerdict | null;
  reasoning: string | null;
  attackChainIds: string[];
}

export function AiAnalysisCard({ confidence, verdict, reasoning, attackChainIds }: AiAnalysisCardProps) {
  const pct = Math.round(confidence * 100);

  const verdictLabel = verdict
    ? verdict.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Pending';

  return (
    <Card>
      <CardHeader title="AI Analysis" />
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm lg:grid-cols-4">
        <div>
          <span className="font-medium text-gray-500">Confidence</span>
          <p className={cn(
            'mt-1 text-lg font-bold',
            pct >= 90 ? 'text-green-700' : pct >= 70 ? 'text-yellow-700' : 'text-red-700',
          )}>
            {pct}%
          </p>
        </div>
        <div>
          <span className="font-medium text-gray-500">Verdict</span>
          <p className="mt-1 font-medium text-gray-900">{verdictLabel}</p>
        </div>
        <div>
          <span className="font-medium text-gray-500">Exploitability</span>
          <p className="mt-1 font-medium text-gray-900">
            {pct >= 85 ? 'HIGH' : pct >= 60 ? 'MEDIUM' : 'LOW'}
          </p>
        </div>
        <div>
          <span className="font-medium text-gray-500">Attack Chains</span>
          <p className="mt-1 font-medium text-gray-900">
            {attackChainIds.length > 0 ? `${attackChainIds.length} linked` : 'None'}
          </p>
        </div>
      </div>
      {reasoning && (
        <div className="mt-4 rounded-md bg-blue-50 p-3">
          <p className="text-sm text-blue-800">{reasoning}</p>
        </div>
      )}
    </Card>
  );
}
