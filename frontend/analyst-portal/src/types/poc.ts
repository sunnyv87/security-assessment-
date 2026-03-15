import type { HttpMessage, Screenshot } from './finding';

export interface ProofOfConcept {
  id: string;
  findingId: string;
  title: string;
  steps: PocStep[];
  environment: PocEnvironment;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface PocStep {
  id: string;
  order: number;
  title: string;
  description: string;
  request: HttpMessage | null;
  response: HttpMessage | null;
  screenshots: Screenshot[];
  annotations: string;
}

export interface PocEnvironment {
  targetHost: string;
  targetPort: number;
  protocol: 'http' | 'https';
  tool: string;
  networkAccess: string;
  testDate: string;
  analystName: string;
  scopeAuthorization: string;
}

export interface PocExportOptions {
  format: 'pdf' | 'markdown' | 'json';
  includeScreenshots: boolean;
  includeRawRequests: boolean;
  redactSensitive: boolean;
}
