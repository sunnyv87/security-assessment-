'use client';

import { useState, useCallback } from 'react';
import { Card, CardHeader } from '@/components/common/Card';
import { formatDistanceToNow } from 'date-fns';
import { useValidation } from '@/hooks/useValidation';

interface ValidationNotesProps {
  findingId: string;
}

export function ValidationNotes({ findingId }: ValidationNotesProps) {
  const { notes, createNote } = useValidation(findingId);
  const [newNote, setNewNote] = useState('');
  const [files, setFiles] = useState<File[]>([]);

  const handleSubmit = useCallback(() => {
    if (!newNote.trim()) return;
    createNote.mutate(
      { content: newNote, attachments: files.length > 0 ? files : undefined },
      {
        onSuccess: () => {
          setNewNote('');
          setFiles([]);
        },
      },
    );
  }, [newNote, files, createNote]);

  return (
    <Card>
      <CardHeader title="Analyst Notes" />

      {/* New note form */}
      <div className="mt-4 space-y-3">
        <textarea
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="Add a validation note..."
          rows={3}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <div className="flex items-center justify-between">
          <label className="cursor-pointer text-sm text-blue-600 hover:underline">
            Attach screenshot
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => {
                if (e.target.files) setFiles(Array.from(e.target.files));
              }}
            />
          </label>
          {files.length > 0 && (
            <span className="text-xs text-gray-500">{files.length} file(s) selected</span>
          )}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!newNote.trim() || createNote.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createNote.isPending ? 'Saving...' : 'Add Note'}
          </button>
        </div>
      </div>

      {/* Existing notes */}
      <div className="mt-6 space-y-4">
        {(notes || []).map((note) => (
          <div key={note.id} className="rounded-md border border-gray-200 p-3">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span className="font-medium text-gray-700">{note.authorName}</span>
              <span>{formatDistanceToNow(new Date(note.createdAt), { addSuffix: true })}</span>
            </div>
            <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{note.content}</p>
            {note.attachments.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {note.attachments.map((att) => (
                  <a
                    key={att.id}
                    href={att.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded bg-gray-100 px-2 py-1 text-xs text-blue-600 hover:bg-gray-200"
                  >
                    {att.filename}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
