import { useMutation, useQueryClient } from '@tanstack/react-query';
import { bulkUpdateFindings, assignFinding, submitValidation } from '@/lib/api-client';
import type { Finding, Severity, FindingStatus } from '@/types/finding';
import type { ValidationSubmission } from '@/types/validation';

export function useTriage() {
  const queryClient = useQueryClient();

  const bulkUpdate = useMutation({
    mutationFn: (params: {
      findingIds: string[];
      update: Partial<Pick<Finding, 'status' | 'severity' | 'assigneeId'>>;
    }) => bulkUpdateFindings(params.findingIds, params.update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings'] });
      queryClient.invalidateQueries({ queryKey: ['findings-summary'] });
    },
  });

  const assign = useMutation({
    mutationFn: (params: { findingId: string; assigneeId: string }) =>
      assignFinding(params.findingId, params.assigneeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings'] });
    },
  });

  const validate = useMutation({
    mutationFn: (data: ValidationSubmission) => submitValidation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings'] });
      queryClient.invalidateQueries({ queryKey: ['findings-summary'] });
    },
  });

  return { bulkUpdate, assign, validate };
}
