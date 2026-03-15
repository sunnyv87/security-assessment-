'use client';

import { useState } from 'react';
import type { RemediationGuidance } from '@/types/api';

interface RemediationEditorProps {
  guidance: RemediationGuidance;
  onSave: (updated: Partial<RemediationGuidance>) => void;
  isSaving: boolean;
}

export function RemediationEditor({ guidance, onSave, isSaving }: RemediationEditorProps) {
  const [editing, setEditing] = useState(false);
  const [summary, setSummary] = useState(guidance.summary);
  const [steps, setSteps] = useState(guidance.detailedSteps.join('\n'));

  const handleSave = () => {
    onSave({
      summary,
      detailedSteps: steps.split('\n').filter((s) => s.trim()),
    });
    setEditing(false);
  };

  if (!editing) {
    return (
      <div>
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-700">
            {guidance.aiGenerated ? 'AI-Generated Remediation' : 'Remediation Guidance'}
          </h4>
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="text-sm text-blue-600 hover:underline"
          >
            Edit
          </button>
        </div>
        <div className="mt-3 space-y-3">
          <div>
            <p className="text-sm font-medium text-gray-900">Summary</p>
            <p className="mt-1 text-sm text-gray-700">{guidance.summary}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Steps</p>
            <ol className="mt-1 list-inside list-decimal space-y-1 text-sm text-gray-700">
              {guidance.detailedSteps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="remediation-summary" className="block text-sm font-medium text-gray-700">Summary</label>
        <textarea
          id="remediation-summary"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={3}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
      <div>
        <label htmlFor="remediation-steps" className="block text-sm font-medium text-gray-700">
          Steps (one per line)
        </label>
        <textarea
          id="remediation-steps"
          value={steps}
          onChange={(e) => setSteps(e.target.value)}
          rows={6}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:border-blue-500 focus:outline-none"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
