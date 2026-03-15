import { useQuery } from '@tanstack/react-query';
import { fetchFindings, fetchFinding, fetchFindingSummary, fetchActivity } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbenchStore';

export function useFindings(engagementId: string | null, findingId?: string) {
  const filters = useWorkbenchStore((s) => s.filters);

  const findingsQuery = useQuery({
    queryKey: ['findings', engagementId, filters],
    queryFn: () => fetchFindings(engagementId!, filters),
    enabled: !!engagementId,
  });

  const summaryQuery = useQuery({
    queryKey: ['findings-summary', engagementId],
    queryFn: () => fetchFindingSummary(engagementId!),
    enabled: !!engagementId,
  });

  const activityQuery = useQuery({
    queryKey: ['activity', engagementId],
    queryFn: () => fetchActivity(engagementId!),
    enabled: !!engagementId,
    refetchInterval: 30_000,
  });

  const findingQuery = useQuery({
    queryKey: ['finding', findingId],
    queryFn: () => fetchFinding(findingId!),
    enabled: !!findingId,
  });

  return {
    findings: findingsQuery.data,
    isLoading: findingsQuery.isLoading,
    summary: summaryQuery.data,
    activity: activityQuery.data,
    finding: findingQuery.data,
    isLoadingFinding: findingQuery.isLoading,
  };
}
