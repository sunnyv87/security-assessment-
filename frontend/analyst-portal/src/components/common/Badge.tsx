'use client';

import { cn, severityColors } from '@/lib/utils';
import type { Severity, FindingStatus, ValidationVerdict } from '@/types/finding';

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold uppercase',
        severityColors[severity],
        className,
      )}
    >
      {severity}
    </span>
  );
}

const statusStyles: Record<FindingStatus, string> = {
  new: 'bg-blue-100 text-blue-800',
  in_review: 'bg-yellow-100 text-yellow-800',
  validated: 'bg-red-100 text-red-800',
  false_positive: 'bg-green-100 text-green-800',
  duplicate: 'bg-purple-100 text-purple-800',
  requires_retest: 'bg-orange-100 text-orange-800',
  remediated: 'bg-emerald-100 text-emerald-800',
  accepted_risk: 'bg-gray-100 text-gray-800',
};

interface StatusBadgeProps {
  status: FindingStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const label = status.replace(/_/g, ' ');
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium capitalize',
        statusStyles[status],
        className,
      )}
    >
      {label}
    </span>
  );
}

const verdictStyles: Record<ValidationVerdict, string> = {
  true_positive: 'bg-red-100 text-red-800',
  false_positive: 'bg-green-100 text-green-800',
  duplicate: 'bg-purple-100 text-purple-800',
  requires_retest: 'bg-orange-100 text-orange-800',
  not_applicable: 'bg-gray-100 text-gray-800',
  informational: 'bg-blue-100 text-blue-800',
};

interface VerdictBadgeProps {
  verdict: ValidationVerdict;
  className?: string;
}

export function VerdictBadge({ verdict, className }: VerdictBadgeProps) {
  const label = verdict.replace(/_/g, ' ');
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium capitalize',
        verdictStyles[verdict],
        className,
      )}
    >
      {label}
    </span>
  );
}

interface ConfidenceBadgeProps {
  confidence: number;
  verdict: ValidationVerdict | null;
  className?: string;
}

export function ConfidenceBadge({ confidence, verdict, className }: ConfidenceBadgeProps) {
  const pct = Math.round(confidence * 100);
  const colorClass =
    pct >= 90 ? 'text-green-700 bg-green-50' :
    pct >= 70 ? 'text-yellow-700 bg-yellow-50' :
    'text-red-700 bg-red-50';

  const label = verdict === 'true_positive' ? 'TP' : verdict === 'false_positive' ? 'FP' : '?';

  return (
    <span className={cn('inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium', colorClass, className)}>
      AI: {pct}% {label}
    </span>
  );
}
