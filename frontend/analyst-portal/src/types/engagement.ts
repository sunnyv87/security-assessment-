export type EngagementStatus =
  | 'draft'
  | 'scoping'
  | 'approved'
  | 'scanning'
  | 'analysis'
  | 'review'
  | 'reporting'
  | 'delivered'
  | 'closed';

export type EngagementType =
  | 'web_app'
  | 'api'
  | 'mobile'
  | 'infrastructure'
  | 'cloud'
  | 'network';

export interface Engagement {
  id: string;
  customerId: string;
  customerName: string;
  name: string;
  type: EngagementType;
  status: EngagementStatus;
  startDate: string;
  endDate: string;
  analystIds: string[];
  leadAnalystId: string;
  findingCount: number;
  scanProgress: number;
  createdAt: string;
  updatedAt: string;
}

export interface ScanJob {
  id: string;
  engagementId: string;
  scanner: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  findingsFound: number;
  startedAt: string | null;
  completedAt: string | null;
}

export interface ScanCoverage {
  assetType: string;
  totalAssets: number;
  scannedAssets: number;
  coveragePercent: number;
}
