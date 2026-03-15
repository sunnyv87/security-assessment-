'use client';

import type { HttpMessage } from '@/types/finding';

interface RequestResponseViewerProps {
  request: HttpMessage | null;
  response: HttpMessage | null;
  onEditRequest?: (message: HttpMessage) => void;
  onEditResponse?: (message: HttpMessage) => void;
  editable?: boolean;
}

export function RequestResponseViewer({
  request,
  response,
  onEditRequest,
  onEditResponse,
  editable = false,
}: RequestResponseViewerProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-700">Request</h4>
          {editable && onEditRequest && request && (
            <button
              type="button"
              onClick={() => onEditRequest(request)}
              className="text-xs text-blue-600 hover:underline"
            >
              Edit
            </button>
          )}
        </div>
        {request ? (
          <pre className="max-h-48 overflow-auto rounded-md bg-gray-900 p-3 text-xs text-gray-100">
            {request.method} {request.url} HTTP/1.1
            {Object.entries(request.headers).map(([k, v]) => `\n${k}: ${v}`).join('')}
            {request.body && `\n\n${request.body}`}
          </pre>
        ) : (
          <div className="flex h-24 items-center justify-center rounded-md bg-gray-100 text-sm text-gray-500">
            No request data
          </div>
        )}
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-700">Response</h4>
          {editable && onEditResponse && response && (
            <button
              type="button"
              onClick={() => onEditResponse(response)}
              className="text-xs text-blue-600 hover:underline"
            >
              Edit
            </button>
          )}
        </div>
        {response ? (
          <pre className="max-h-48 overflow-auto rounded-md bg-gray-900 p-3 text-xs text-gray-100">
            HTTP/1.1 {response.statusCode}
            {Object.entries(response.headers).map(([k, v]) => `\n${k}: ${v}`).join('')}
            {response.body && `\n\n${response.body}`}
          </pre>
        ) : (
          <div className="flex h-24 items-center justify-center rounded-md bg-gray-100 text-sm text-gray-500">
            No response data
          </div>
        )}
      </div>
    </div>
  );
}
