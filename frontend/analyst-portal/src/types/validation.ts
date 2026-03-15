import type { ValidationVerdict } from './finding';

export interface ValidationNote {
  id: string;
  findingId: string;
  authorId: string;
  authorName: string;
  content: string;
  attachments: NoteAttachment[];
  createdAt: string;
  updatedAt: string;
}

export interface NoteAttachment {
  id: string;
  filename: string;
  url: string;
  mimeType: string;
  size: number;
}

export interface ValidationChecklistItem {
  id: string;
  label: string;
  checked: boolean;
  category: string;
}

export interface ValidationChecklist {
  findingId: string;
  templateId: string;
  templateName: string;
  items: ValidationChecklistItem[];
  completedCount: number;
  totalCount: number;
}

export interface ValidationSubmission {
  findingId: string;
  verdict: ValidationVerdict;
  justification: string;
  checklistCompleted: boolean;
}
