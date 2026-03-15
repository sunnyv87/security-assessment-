'use client';

import { useState } from 'react';
import { VerdictSelector } from './VerdictSelector';
import { ValidationChecklist } from './ValidationChecklist';
import { ValidationNotes } from './ValidationNotes';
import { useValidation } from '@/hooks/useValidation';
import type { ValidationVerdict } from '@/types/finding';

interface ValidationPanelProps {
  findingId: string;
}

export function ValidationPanel({ findingId }: ValidationPanelProps) {
  const [verdict, setVerdict] = useState<ValidationVerdict | null>(null);
  const [justification, setJustification] = useState('');
  const { submitVerdict } = useValidation(findingId);

  const handleSubmitVerdict = () => {
    if (!verdict) return;
    submitVerdict.mutate({
      findingId,
      verdict,
      justification,
      checklistCompleted: true,
    });
  };

  return (
    <div className="space-y-6">
      <VerdictSelector value={verdict} onChange={setVerdict} />

      {verdict && (
        <div>
          <label htmlFor="justification" className="block text-sm font-medium text-gray-700">
            Justification
          </label>
          <textarea
            id="justification"
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            rows={2}
            placeholder="Briefly explain your verdict..."
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSubmitVerdict}
            disabled={submitVerdict.isPending}
            className="mt-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitVerdict.isPending ? 'Submitting...' : 'Submit Verdict'}
          </button>
        </div>
      )}

      <ValidationChecklist findingId={findingId} />
      <ValidationNotes findingId={findingId} />
    </div>
  );
}
