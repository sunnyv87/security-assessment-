'use client';

import { Card, CardHeader } from '@/components/common/Card';
import { useValidation } from '@/hooks/useValidation';

interface ValidationChecklistProps {
  findingId: string;
}

export function ValidationChecklist({ findingId }: ValidationChecklistProps) {
  const { checklist, updateChecklistItem } = useValidation(findingId);

  if (!checklist) return null;

  const progress = checklist.totalCount > 0
    ? Math.round((checklist.completedCount / checklist.totalCount) * 100)
    : 0;

  return (
    <Card>
      <CardHeader
        title={`Validation Checklist (${checklist.templateName})`}
        description={`${checklist.completedCount}/${checklist.totalCount} completed`}
      />

      {/* Progress bar */}
      <div className="mt-3 h-1.5 w-full rounded-full bg-gray-200">
        <div
          className="h-1.5 rounded-full bg-blue-600 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="mt-4 space-y-2">
        {checklist.items.map((item) => (
          <label
            key={item.id}
            className="flex items-start gap-3 rounded-md p-2 hover:bg-gray-50"
          >
            <input
              type="checkbox"
              checked={item.checked}
              onChange={(e) => updateChecklistItem.mutate({ itemId: item.id, checked: e.target.checked })}
              className="mt-0.5 h-4 w-4 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">{item.label}</span>
          </label>
        ))}
      </div>
    </Card>
  );
}
