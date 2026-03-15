'use client';

import { PocStepComponent } from './PocStep';
import { PocEnvironmentDisplay } from './PocEnvironment';
import { PocExport } from './PocExport';
import { PageHeader } from '@/components/common/PageHeader';
import { EmptyState } from '@/components/common/EmptyState';
import { usePoc } from '@/hooks/usePoc';
import type { PocStep } from '@/types/poc';

interface PocRecorderProps {
  findingId: string;
}

export function PocRecorder({ findingId }: PocRecorderProps) {
  const { pocs, addStep, deleteStep, isLoading } = usePoc(findingId);
  const activePoc = pocs?.[0]; // Primary PoC

  const handleAddStep = () => {
    if (!activePoc) return;
    addStep.mutate({
      pocId: activePoc.id,
      step: {
        order: (activePoc.steps.length || 0) + 1,
        title: `Step ${(activePoc.steps.length || 0) + 1}`,
        description: '',
        request: null,
        response: null,
        screenshots: [],
        annotations: '',
      },
    });
  };

  const handleEditStep = (_step: PocStep) => {
    // Opens edit modal (implementation deferred to modal component)
  };

  const handleDeleteStep = (stepId: string) => {
    if (!activePoc) return;
    deleteStep.mutate({ pocId: activePoc.id, stepId });
  };

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-gray-500">Loading PoC data...</div>;
  }

  if (!activePoc) {
    return (
      <EmptyState
        title="No Proof of Concept"
        description="Record a PoC to demonstrate this vulnerability"
        action={
          <button
            type="button"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Start Recording
          </button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Proof of Concept"
        actions={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleAddStep}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              + Add Step
            </button>
          </div>
        }
      />

      {/* PoC Steps */}
      <div className="space-y-4">
        {activePoc.steps
          .sort((a, b) => a.order - b.order)
          .map((step, idx) => (
            <PocStepComponent
              key={step.id}
              step={step}
              stepNumber={idx + 1}
              onEdit={handleEditStep}
              onDelete={handleDeleteStep}
            />
          ))}
      </div>

      {/* Environment */}
      <PocEnvironmentDisplay environment={activePoc.environment} />

      {/* Export controls */}
      <PocExport pocId={activePoc.id} />
    </div>
  );
}
