'use client';

import * as RadioGroup from '@radix-ui/react-radio-group';
import { cn } from '@/lib/utils';
import type { ValidationVerdict } from '@/types/finding';

interface VerdictSelectorProps {
  value: ValidationVerdict | null;
  onChange: (verdict: ValidationVerdict) => void;
  disabled?: boolean;
}

const verdicts: { value: ValidationVerdict; label: string; color: string }[] = [
  { value: 'true_positive', label: 'True Positive', color: 'border-red-300 data-[state=checked]:bg-red-50 data-[state=checked]:border-red-500' },
  { value: 'false_positive', label: 'False Positive', color: 'border-green-300 data-[state=checked]:bg-green-50 data-[state=checked]:border-green-500' },
  { value: 'duplicate', label: 'Duplicate', color: 'border-purple-300 data-[state=checked]:bg-purple-50 data-[state=checked]:border-purple-500' },
  { value: 'requires_retest', label: 'Requires Retest', color: 'border-orange-300 data-[state=checked]:bg-orange-50 data-[state=checked]:border-orange-500' },
  { value: 'not_applicable', label: 'Not Applicable', color: 'border-gray-300 data-[state=checked]:bg-gray-50 data-[state=checked]:border-gray-500' },
  { value: 'informational', label: 'Informational', color: 'border-blue-300 data-[state=checked]:bg-blue-50 data-[state=checked]:border-blue-500' },
];

export function VerdictSelector({ value, onChange, disabled }: VerdictSelectorProps) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-gray-700">Validation Verdict</h3>
      <RadioGroup.Root
        value={value || ''}
        onValueChange={(v) => onChange(v as ValidationVerdict)}
        disabled={disabled}
        className="grid grid-cols-2 gap-2 lg:grid-cols-3"
      >
        {verdicts.map((v) => (
          <RadioGroup.Item
            key={v.value}
            value={v.value}
            className={cn(
              'flex items-center justify-center rounded-lg border-2 px-3 py-2.5 text-sm font-medium transition-colors',
              v.color,
              disabled && 'opacity-50',
            )}
          >
            {v.label}
          </RadioGroup.Item>
        ))}
      </RadioGroup.Root>
    </div>
  );
}
