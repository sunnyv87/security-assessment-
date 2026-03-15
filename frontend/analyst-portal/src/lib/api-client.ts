import ky from 'ky';
import type { PaginatedResponse, FindingFilters, RemediationGuidance, SeverityOverride, ActivityEvent } from '@/types/api';
import type { Finding, FindingSummary } from '@/types/finding';
import type { Engagement, ScanCoverage } from '@/types/engagement';
import type { ValidationNote, ValidationSubmission, ValidationChecklist } from '@/types/validation';
import type { ProofOfConcept, PocStep, PocExportOptions } from '@/types/poc';

const api = ky.create({
  prefixUrl: '/api/v1',
  timeout: 30_000,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = typeof window !== 'undefined'
          ? sessionStorage.getItem('access_token')
          : null;
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      },
    ],
  },
});

// ── Engagements ──

export async function fetchEngagements(): Promise<Engagement[]> {
  return api.get('engagements').json();
}

export async function fetchEngagement(id: string): Promise<Engagement> {
  return api.get(`engagements/${id}`).json();
}

// ── Findings ──

export async function fetchFindings(
  engagementId: string,
  filters: FindingFilters = {},
): Promise<PaginatedResponse<Finding>> {
  return api.get(`engagements/${engagementId}/findings`, { searchParams: filters as Record<string, string> }).json();
}

export async function fetchFinding(findingId: string): Promise<Finding> {
  return api.get(`findings/${findingId}`).json();
}

export async function fetchFindingSummary(engagementId: string): Promise<FindingSummary> {
  return api.get(`engagements/${engagementId}/findings/summary`).json();
}

// ── Scan Coverage ──

export async function fetchScanCoverage(engagementId: string): Promise<ScanCoverage[]> {
  return api.get(`engagements/${engagementId}/scan-coverage`).json();
}

// ── Triage / Validation ──

export async function submitValidation(data: ValidationSubmission): Promise<Finding> {
  return api.put(`findings/${data.findingId}/verdict`, { json: data }).json();
}

export async function bulkUpdateFindings(
  findingIds: string[],
  update: Partial<Pick<Finding, 'status' | 'severity' | 'assigneeId'>>,
): Promise<void> {
  return api.patch('findings/bulk', { json: { findingIds, ...update } }).json();
}

export async function assignFinding(findingId: string, assigneeId: string): Promise<Finding> {
  return api.put(`findings/${findingId}/assign`, { json: { assigneeId } }).json();
}

// ── Validation Notes ──

export async function fetchNotes(findingId: string): Promise<ValidationNote[]> {
  return api.get(`findings/${findingId}/notes`).json();
}

const ALLOWED_ATTACHMENT_TYPES = new Set([
  'image/png', 'image/jpeg', 'image/gif', 'image/webp',
  'application/pdf',
  'text/plain', 'text/csv',
  'application/json',
  'application/xml', 'text/xml',
]);
const MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024; // 10 MB
const MAX_ATTACHMENTS = 10;

function validateAttachments(files: File[]): void {
  if (files.length > MAX_ATTACHMENTS) {
    throw new Error(`Too many attachments: max ${MAX_ATTACHMENTS} files allowed`);
  }
  for (const f of files) {
    if (!ALLOWED_ATTACHMENT_TYPES.has(f.type)) {
      throw new Error(`Unsupported file type: ${f.type || 'unknown'} (${f.name})`);
    }
    if (f.size > MAX_ATTACHMENT_SIZE) {
      throw new Error(`File too large: ${f.name} (${(f.size / 1024 / 1024).toFixed(1)} MB, max 10 MB)`);
    }
  }
}

export async function createNote(findingId: string, content: string, attachments?: File[]): Promise<ValidationNote> {
  if (attachments?.length) {
    validateAttachments(attachments);
    const form = new FormData();
    form.set('content', content);
    attachments.forEach((f) => form.append('attachments', f));
    return api.post(`findings/${findingId}/notes`, { body: form }).json();
  }
  return api.post(`findings/${findingId}/notes`, { json: { content } }).json();
}

// ── Validation Checklist ──

export async function fetchChecklist(findingId: string): Promise<ValidationChecklist> {
  return api.get(`findings/${findingId}/checklist`).json();
}

export async function updateChecklistItem(
  findingId: string,
  itemId: string,
  checked: boolean,
): Promise<ValidationChecklist> {
  return api.patch(`findings/${findingId}/checklist/${itemId}`, { json: { checked } }).json();
}

// ── Proof of Concept ──

export async function fetchPocs(findingId: string): Promise<ProofOfConcept[]> {
  return api.get(`findings/${findingId}/pocs`).json();
}

export async function createPoc(findingId: string, poc: Omit<ProofOfConcept, 'id' | 'createdAt' | 'updatedAt'>): Promise<ProofOfConcept> {
  return api.post(`findings/${findingId}/pocs`, { json: poc }).json();
}

export async function updatePocStep(pocId: string, step: PocStep): Promise<ProofOfConcept> {
  return api.put(`pocs/${pocId}/steps/${step.id}`, { json: step }).json();
}

export async function addPocStep(pocId: string, step: Omit<PocStep, 'id'>): Promise<PocStep> {
  return api.post(`pocs/${pocId}/steps`, { json: step }).json();
}

export async function deletePocStep(pocId: string, stepId: string): Promise<void> {
  return api.delete(`pocs/${pocId}/steps/${stepId}`).json();
}

export async function exportPoc(pocId: string, options: PocExportOptions): Promise<Blob> {
  return api.post(`pocs/${pocId}/export`, { json: options }).blob();
}

// ── Remediation ──

export async function fetchRemediation(findingId: string): Promise<RemediationGuidance> {
  return api.get(`findings/${findingId}/remediation`).json();
}

export async function regenerateRemediation(findingId: string): Promise<RemediationGuidance> {
  return api.post(`findings/${findingId}/remediation/regenerate`).json();
}

export async function updateRemediation(
  findingId: string,
  guidance: Partial<RemediationGuidance>,
): Promise<RemediationGuidance> {
  return api.patch(`findings/${findingId}/remediation`, { json: guidance }).json();
}

export async function approveRemediation(findingId: string): Promise<RemediationGuidance> {
  return api.post(`findings/${findingId}/remediation/approve`).json();
}

// ── Severity Override ──

export async function overrideSeverity(data: SeverityOverride): Promise<Finding> {
  return api.put(`findings/${data.findingId}/severity`, { json: data }).json();
}

// ── Activity ──

export async function fetchActivity(engagementId: string, limit = 20): Promise<ActivityEvent[]> {
  return api.get(`engagements/${engagementId}/activity`, { searchParams: { limit: String(limit) } }).json();
}
