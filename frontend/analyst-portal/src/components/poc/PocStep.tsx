'use client';

import { RequestResponseViewer } from './RequestResponseViewer';
import type { PocStep as PocStepType } from '@/types/poc';

interface PocStepProps {
  step: PocStepType;
  stepNumber: number;
  onEdit: (step: PocStepType) => void;
  onDelete: (stepId: string) => void;
}

export function PocStepComponent({ step, stepNumber, onEdit, onDelete }: PocStepProps) {
  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">
          Step {stepNumber}: {step.title}
        </h4>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onEdit(step)}
            className="text-xs text-blue-600 hover:underline"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => onDelete(step.id)}
            className="text-xs text-red-600 hover:underline"
          >
            Delete
          </button>
        </div>
      </div>

      {step.description && (
        <p className="mt-2 text-sm text-gray-600">{step.description}</p>
      )}

      <div className="mt-3">
        <RequestResponseViewer request={step.request} response={step.response} />
      </div>

      {step.annotations && (
        <div className="mt-3 rounded-md bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
          <span className="font-medium">Annotations: </span>
          {step.annotations}
        </div>
      )}

      {step.screenshots.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {step.screenshots.map((ss) => (
            <a
              key={ss.id}
              href={ss.url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded border border-gray-200 px-2 py-1 text-xs text-blue-600 hover:bg-gray-50"
            >
              {ss.filename}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
