'use client';

import { StatCard } from '@/components/common/Card';
import type { FindingSummary } from '@/types/finding';

interface SeverityBreakdownProps {
  summary: FindingSummary;
  onSeverityClick?: (severity: string) => void;
}

export function SeverityBreakdown({ summary, onSeverityClick }: SeverityBreakdownProps) {
  const cards = [
    { label: 'Critical', value: summary.bySeverity.critical || 0, color: 'text-severity-critical' },
    { label: 'High', value: summary.bySeverity.high || 0, color: 'text-severity-high' },
    { label: 'Medium', value: summary.bySeverity.medium || 0, color: 'text-severity-medium' },
    { label: 'Low', value: summary.bySeverity.low || 0, color: 'text-severity-low' },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {cards.map((card) => (
        <StatCard
          key={card.label}
          label={card.label}
          value={card.value}
          colorClass={card.color}
          onClick={() => onSeverityClick?.(card.label.toLowerCase())}
        />
      ))}
    </div>
  );
}
