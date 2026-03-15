export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type FindingStatus =
  | 'new'
  | 'in_review'
  | 'validated'
  | 'false_positive'
  | 'duplicate'
  | 'requires_retest'
  | 'remediated'
  | 'accepted_risk';

export type ValidationVerdict =
  | 'true_positive'
  | 'false_positive'
  | 'duplicate'
  | 'requires_retest'
  | 'not_applicable'
  | 'informational';

export type ScannerType =
  | 'burp_suite'
  | 'nuclei'
  | 'fortify'
  | 'tenable'
  | 'mobsf'
  | 'nmap'
  | 'scoutsuite'
  | 'trivy'
  | 'zap';

export interface Finding {
  id: string;
  engagementId: string;
  title: string;
  description: string;
  severity: Severity;
  status: FindingStatus;
  scanner: ScannerType;
  cvssScore: number;
  cvssVector: string;
  cweId: string;
  cweName: string;
  asset: string;
  endpoint: string;
  httpMethod: string;
  category: string;
  assigneeId: string | null;
  assigneeName: string | null;
  aiConfidence: number;
  aiVerdict: ValidationVerdict | null;
  aiReasoning: string | null;
  duplicateOfId: string | null;
  attackChainIds: string[];
  evidence: FindingEvidence;
  validationVerdict: ValidationVerdict | null;
  validatedAt: string | null;
  validatedBy: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface FindingEvidence {
  request: HttpMessage | null;
  response: HttpMessage | null;
  screenshots: Screenshot[];
  rawOutput: string | null;
}

export interface HttpMessage {
  method?: string;
  url?: string;
  statusCode?: number;
  headers: Record<string, string>;
  body: string;
}

export interface Screenshot {
  id: string;
  filename: string;
  url: string;
  caption: string;
  createdAt: string;
}

export interface FindingSummary {
  totalFindings: number;
  bySeverity: Record<Severity, number>;
  byStatus: Record<FindingStatus, number>;
  byScanner: Record<string, number>;
  validatedCount: number;
  falsePositiveRate: number;
}

export interface FindingCluster {
  clusterId: string;
  primaryFindingId: string;
  relatedFindingIds: string[];
  similarity: number;
}

export interface AttackChain {
  id: string;
  findingIds: string[];
  description: string;
  impactSummary: string;
  severity: Severity;
}
