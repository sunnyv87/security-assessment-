import { create } from 'zustand';
import type { Engagement } from '@/types/engagement';
import type { Severity, FindingStatus } from '@/types/finding';

interface FindingFilterState {
  severity: Severity[];
  status: FindingStatus[];
  scanner: string[];
  assigneeId: string | null;
  search: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  page: number;
  pageSize: number;
}

interface WorkbenchState {
  // Engagement context
  engagements: Engagement[];
  activeEngagementId: string | null;
  setEngagements: (engagements: Engagement[]) => void;
  setActiveEngagement: (id: string) => void;

  // Finding selection (for bulk ops)
  selectedFindingIds: Set<string>;
  toggleFindingSelection: (id: string) => void;
  selectAllFindings: (ids: string[]) => void;
  clearSelection: () => void;

  // Filters
  filters: FindingFilterState;
  setFilter: <K extends keyof FindingFilterState>(key: K, value: FindingFilterState[K]) => void;
  resetFilters: () => void;

  // UI state
  detailPanelOpen: boolean;
  activeFindingId: string | null;
  openFindingDetail: (id: string) => void;
  closeFindingDetail: () => void;
}

const defaultFilters: FindingFilterState = {
  severity: [],
  status: [],
  scanner: [],
  assigneeId: null,
  search: '',
  sortBy: 'aiConfidence',
  sortOrder: 'desc',
  page: 1,
  pageSize: 20,
};

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  engagements: [],
  activeEngagementId: null,
  setEngagements: (engagements) => set({ engagements }),
  setActiveEngagement: (id) => set({ activeEngagementId: id }),

  selectedFindingIds: new Set(),
  toggleFindingSelection: (id) =>
    set((state) => {
      const next = new Set(state.selectedFindingIds);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { selectedFindingIds: next };
    }),
  selectAllFindings: (ids) => set({ selectedFindingIds: new Set(ids) }),
  clearSelection: () => set({ selectedFindingIds: new Set() }),

  filters: defaultFilters,
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value, ...(key !== 'page' ? { page: 1 } : {}) },
    })),
  resetFilters: () => set({ filters: defaultFilters }),

  detailPanelOpen: false,
  activeFindingId: null,
  openFindingDetail: (id) => set({ detailPanelOpen: true, activeFindingId: id }),
  closeFindingDetail: () => set({ detailPanelOpen: false, activeFindingId: null }),
}));
