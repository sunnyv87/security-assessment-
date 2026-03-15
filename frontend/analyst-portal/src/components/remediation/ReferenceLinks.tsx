'use client';

import type { Reference } from '@/types/api';

interface ReferenceLinksProps {
  references: Reference[];
}

export function ReferenceLinks({ references }: ReferenceLinksProps) {
  if (references.length === 0) return null;

  return (
    <div>
      <h4 className="mb-2 text-sm font-medium text-gray-700">References</h4>
      <ul className="space-y-1.5">
        {references.map((ref) => (
          <li key={ref.url} className="flex items-center gap-2 text-sm">
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
              {ref.source}
            </span>
            <a
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {ref.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
