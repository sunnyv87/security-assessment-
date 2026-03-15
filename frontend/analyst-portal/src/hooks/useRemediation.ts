import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchRemediation,
  regenerateRemediation,
  updateRemediation,
  approveRemediation,
  overrideSeverity,
} from '@/lib/api-client';
import type { RemediationGuidance, SeverityOverride } from '@/types/api';

export function useRemediation(findingId: string) {
  const queryClient = useQueryClient();

  const guidanceQuery = useQuery({
    queryKey: ['remediation', findingId],
    queryFn: () => fetchRemediation(findingId),
  });

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateRemediation(findingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remediation', findingId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<RemediationGuidance>) => updateRemediation(findingId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remediation', findingId] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => approveRemediation(findingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remediation', findingId] });
    },
  });

  const overrideSeverityMutation = useMutation({
    mutationFn: (data: SeverityOverride) => overrideSeverity(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finding', findingId] });
      queryClient.invalidateQueries({ queryKey: ['findings'] });
    },
  });

  return {
    guidance: guidanceQuery.data,
    isLoading: guidanceQuery.isLoading,
    regenerate: regenerateMutation,
    updateGuidance: updateMutation,
    approve: approveMutation,
    overrideSeverity: overrideSeverityMutation,
  };
}
