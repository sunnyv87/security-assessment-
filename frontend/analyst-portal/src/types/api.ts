export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface FindingFilters {
  severity?: string[];
  status?: string[];
  scanner?: string[];
  assigneeId?: string;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
}

export interface RemediationGuidance {
  findingId: string;
  summary: string;
  detailedSteps: string[];
  codeExamples: CodeExample[];
  references: Reference[];
  aiGenerated: boolean;
  approvedBy: string | null;
  approvedAt: string | null;
}

export interface CodeExample {
  language: string;
  label: string;
  before: string;
  after: string;
}

export interface Reference {
  title: string;
  url: string;
  source: string;
}

export interface SeverityOverride {
  findingId: string;
  originalSeverity: string;
  originalCvss: number;
  newSeverity: string;
  newCvss: number;
  justification: string;
  contextFactors: string[];
}

export interface ActivityEvent {
  id: string;
  type: 'validation' | 'poc' | 'severity_change' | 'assignment' | 'note' | 'status_change';
  description: string;
  actorName: string;
  findingId: string;
  findingTitle: string;
  timestamp: string;
}
