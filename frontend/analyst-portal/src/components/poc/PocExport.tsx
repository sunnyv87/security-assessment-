'use client';

import { useState } from 'react';
import { usePoc } from '@/hooks/usePoc';
import type { PocExportOptions } from '@/types/poc';

interface PocExportProps {
  pocId: string;
}

export function PocExport({ pocId }: PocExportProps) {
  const { exportPoc } = usePoc();
  const [options, setOptions] = useState<PocExportOptions>({
    format: 'pdf',
    includeScreenshots: true,
    includeRawRequests: true,
    redactSensitive: false,
  });

  const handleExport = () => {
    exportPoc.mutate({ pocId, options });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={options.format}
        onChange={(e) => setOptions({ ...options, format: e.target.value as PocExportOptions['format'] })}
        className="rounded border border-gray-300 px-2 py-1.5 text-sm"
      >
        <option value="pdf">Export as PDF</option>
        <option value="markdown">Export as Markdown</option>
        <option value="json">Export as JSON</option>
      </select>

      <label className="flex items-center gap-1.5 text-sm text-gray-600">
        <input
          type="checkbox"
          checked={options.includeScreenshots}
          onChange={(e) => setOptions({ ...options, includeScreenshots: e.target.checked })}
          className="h-3.5 w-3.5 rounded border-gray-300"
        />
        Screenshots
      </label>

      <label className="flex items-center gap-1.5 text-sm text-gray-600">
        <input
          type="checkbox"
          checked={options.redactSensitive}
          onChange={(e) => setOptions({ ...options, redactSensitive: e.target.checked })}
          className="h-3.5 w-3.5 rounded border-gray-300"
        />
        Redact sensitive
      </label>

      <button
        type="button"
        onClick={handleExport}
        disabled={exportPoc.isPending}
        className="rounded-md bg-gray-800 px-4 py-1.5 text-sm font-medium text-white hover:bg-gray-900 disabled:opacity-50"
      >
        {exportPoc.isPending ? 'Exporting...' : 'Export PoC'}
      </button>

      <button
        type="button"
        className="rounded-md border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100"
      >
        Attach to Report
      </button>
    </div>
  );
}
