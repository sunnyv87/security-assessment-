'use client';

import { Card, CardHeader } from '@/components/common/Card';
import { RemediationEditor } from './RemediationEditor';
import { CodeExample } from './CodeExample';
import { ReferenceLinks } from './ReferenceLinks';
import { SeverityUpdater } from './SeverityUpdater';
import { useRemediation } from '@/hooks/useRemediation';
import { useFindings } from '@/hooks/useFindings';

interface RemediationGuidanceProps {
  findingId: string;
}

export function RemediationGuidance({ findingId }: RemediationGuidanceProps) {
  const { finding } = useFindings(null, findingId);
  const { guidance, isLoading, regenerate, updateGuidance, approve } = useRemediation(findingId);

  if (isLoading) {
    return <div className="py-12 text-center text-sm text-gray-500">Loading remediation guidance...</div>;
  }

  if (!guidance) {
    return (
      <div className="space-y-4 text-center">
        <p className="text-sm text-gray-500">No remediation guidance generated yet</p>
        <button
          type="button"
          onClick={() => regenerate.mutate()}
          disabled={regenerate.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {regenerate.isPending ? 'Generating...' : 'Generate with AI'}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Remediation content */}
      <Card>
        <CardHeader
          title="Remediation Guidance"
          action={
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => regenerate.mutate()}
                disabled={regenerate.isPending}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
              >
                Regenerate
              </button>
              {!guidance.approvedBy && (
                <button
                  type="button"
                  onClick={() => approve.mutate()}
                  disabled={approve.isPending}
                  className="rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
                >
                  Approve
                </button>
              )}
            </div>
          }
        />

        <div className="mt-4">
          <RemediationEditor
            guidance={guidance}
            onSave={(updated) => updateGuidance.mutate(updated)}
            isSaving={updateGuidance.isPending}
          />
        </div>
      </Card>

      {/* Code examples */}
      {guidance.codeExamples.length > 0 && (
        <Card>
          <CardHeader title="Code Examples" />
          <div className="mt-4 space-y-6">
            {guidance.codeExamples.map((example, idx) => (
              <CodeExample key={idx} example={example} />
            ))}
          </div>
        </Card>
      )}

      {/* References */}
      {guidance.references.length > 0 && (
        <Card>
          <ReferenceLinks references={guidance.references} />
        </Card>
      )}

      {/* Severity override */}
      {finding && (
        <SeverityUpdater
          findingId={findingId}
          originalSeverity={finding.severity}
          originalCvss={finding.cvssScore}
        />
      )}
    </div>
  );
}
