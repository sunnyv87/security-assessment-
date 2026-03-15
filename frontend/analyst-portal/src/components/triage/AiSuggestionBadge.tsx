'use client';

import { cn } from '@/lib/utils';
import type { ValidationVerdict } from '@/types/finding';

interface AiSuggestionBadgeProps {
  confidence: number;
  verdict: ValidationVerdict | null;
  reasoning?: string | null;
  className?: string;
}

export function AiSuggestionBadge({ confidence, verdict, reasoning, className }: AiSuggestionBadgeProps) {
  const pct = Math.round(confidence * 100);
  const isHighConfidence = pct >= 85;

  const verdictLabels: Record<ValidationVerdict, string> = {
    true_positive: 'True Positive',
    false_positive: 'False Positive',
    duplicate: 'Duplicate',
    requires_retest: 'Requires Retest',
    not_applicable: 'N/A',
    informational: 'Informational',
  };

  return (
    <div className={cn('rounded-md border border-gray-200 bg-gray-50 p-3', className)}>
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-gray-500">AI Suggestion:</span>
        {verdict && (
          <span className={cn('text-sm font-medium', isHighConfidence ? 'text-green-700' : 'text-yellow-700')}>
            {verdictLabels[verdict]}
          </span>
        )}
        <span className={cn(
          'ml-auto rounded-full px-2 py-0.5 text-xs font-medium',
          pct >= 90 ? 'bg-green-100 text-green-700' :
          pct >= 70 ? 'bg-yellow-100 text-yellow-700' :
          'bg-red-100 text-red-700',
        )}>
          {pct}% confidence
        </span>
      </div>
      {reasoning && (
        <p className="mt-1.5 text-xs text-gray-600">{reasoning}</p>
      )}
    </div>
  );
}
