'use client';

import type { CodeExample as CodeExampleType } from '@/types/api';

interface CodeExampleProps {
  example: CodeExampleType;
}

export function CodeExample({ example }: CodeExampleProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-gray-700">{example.label}</h4>
      <div className="grid gap-3 lg:grid-cols-2">
        <div>
          <span className="mb-1 block text-xs font-medium text-red-600">BEFORE (vulnerable)</span>
          <pre className="overflow-auto rounded-md bg-red-950 p-3 text-xs text-red-100">
            {example.before}
          </pre>
        </div>
        <div>
          <span className="mb-1 block text-xs font-medium text-green-600">AFTER (secure)</span>
          <pre className="overflow-auto rounded-md bg-green-950 p-3 text-xs text-green-100">
            {example.after}
          </pre>
        </div>
      </div>
    </div>
  );
}
