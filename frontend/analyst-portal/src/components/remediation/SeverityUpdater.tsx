'use client';

import { useState } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import type { Severity } from '@/types/finding';
import { useRemediation } from '@/hooks/useRemediation';

interface SeverityUpdaterProps {
  findingId: string;
  originalSeverity: Severity;
  originalCvss: number;
}

const severities: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];

const contextFactorOptions = [
  { id: 'internet_facing', label: 'Internet-facing' },
  { id: 'auth_not_required', label: 'Auth not required' },
  { id: 'pii_sensitive', label: 'PII/sensitive data' },
  { id: 'compensating_controls', label: 'Compensating controls' },
  { id: 'limited_exposure', label: 'Limited data exposure' },
  { id: 'rate_limiting', label: 'Rate limiting in place' },
];

export function SeverityUpdater({ findingId, originalSeverity, originalCvss }: SeverityUpdaterProps) {
  const [newSeverity, setNewSeverity] = useState<Severity>(originalSeverity);
  const [newCvss, setNewCvss] = useState(originalCvss);
  const [justification, setJustification] = useState('');
  const [contextFactors, setContextFactors] = useState<string[]>([]);
  const { overrideSeverity } = useRemediation(findingId);

  const hasChanges = newSeverity !== originalSeverity || newCvss !== originalCvss;

  const toggleFactor = (factorId: string) => {
    setContextFactors((prev) =>
      prev.includes(factorId) ? prev.filter((f) => f !== factorId) : [...prev, factorId],
    );
  };

  const handleSubmit = () => {
    if (!hasChanges || !justification.trim()) return;
    overrideSeverity.mutate({
      findingId,
      originalSeverity,
      originalCvss,
      newSeverity,
      newCvss,
      justification,
      contextFactors,
    });
  };

  return (
    <Card>
      <CardHeader title="Severity Override" />
      <div className="mt-4 space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Scanner Severity</span>
            <p className="mt-1 font-medium capitalize text-gray-900">
              {originalSeverity} (CVSS {originalCvss})
            </p>
          </div>
          <div className="space-y-2">
            <label htmlFor="severity-select" className="text-gray-500">Analyst Override</label>
            <div className="flex gap-2">
              <select
                id="severity-select"
                value={newSeverity}
                onChange={(e) => setNewSeverity(e.target.value as Severity)}
                className="rounded border border-gray-300 px-2 py-1 text-sm capitalize"
              >
                {severities.map((s) => (
                  <option key={s} value={s} className="capitalize">{s}</option>
                ))}
              </select>
              <input
                type="number"
                value={newCvss}
                onChange={(e) => setNewCvss(Number(e.target.value))}
                min={0}
                max={10}
                step={0.1}
                className="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Context factors */}
        <div>
          <p className="mb-2 text-sm font-medium text-gray-700">Context Factors</p>
          <div className="grid grid-cols-2 gap-2">
            {contextFactorOptions.map((factor) => (
              <label key={factor.id} className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={contextFactors.includes(factor.id)}
                  onChange={() => toggleFactor(factor.id)}
                  className="h-3.5 w-3.5 rounded border-gray-300"
                />
                {factor.label}
              </label>
            ))}
          </div>
        </div>

        {hasChanges && (
          <>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              placeholder="Justification for severity change..."
              rows={2}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!justification.trim() || overrideSeverity.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {overrideSeverity.isPending ? 'Saving...' : 'Apply Override'}
            </button>
          </>
        )}
      </div>
    </Card>
  );
}
