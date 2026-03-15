'use client';

import type { FindingEvidence, HttpMessage } from '@/types/finding';

interface EvidenceViewerProps {
  evidence: FindingEvidence;
}

export function EvidenceViewer({ evidence }: EvidenceViewerProps) {
  return (
    <div className="space-y-4">
      {evidence.request && evidence.response && (
        <div className="grid gap-4 lg:grid-cols-2">
          <HttpMessageBlock label="Request" message={evidence.request} />
          <HttpMessageBlock label="Response" message={evidence.response} />
        </div>
      )}

      {evidence.screenshots.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">Screenshots</h4>
          <div className="flex flex-wrap gap-2">
            {evidence.screenshots.map((screenshot) => (
              <a
                key={screenshot.id}
                href={screenshot.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded border border-gray-200 p-2 text-sm text-blue-600 hover:bg-gray-50"
              >
                {screenshot.filename}
              </a>
            ))}
          </div>
        </div>
      )}

      {evidence.rawOutput && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">Raw Scanner Output</h4>
          <pre className="max-h-60 overflow-auto rounded-md bg-gray-900 p-4 text-xs text-gray-100">
            {evidence.rawOutput}
          </pre>
        </div>
      )}
    </div>
  );
}

function HttpMessageBlock({ label, message }: { label: string; message: HttpMessage }) {
  const headerLines = Object.entries(message.headers)
    .map(([k, v]) => `${k}: ${v}`)
    .join('\n');

  const firstLine = message.method
    ? `${message.method} ${message.url} HTTP/1.1`
    : `HTTP/1.1 ${message.statusCode}`;

  return (
    <div>
      <h4 className="mb-2 text-sm font-medium text-gray-700">{label}</h4>
      <pre className="max-h-48 overflow-auto rounded-md bg-gray-900 p-3 text-xs text-gray-100">
        {firstLine}
        {headerLines && `\n${headerLines}`}
        {message.body && `\n\n${message.body}`}
      </pre>
    </div>
  );
}
