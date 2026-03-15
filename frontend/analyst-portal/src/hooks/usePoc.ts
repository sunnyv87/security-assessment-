import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchPocs, addPocStep, deletePocStep, exportPoc } from '@/lib/api-client';
import type { PocStep, PocExportOptions } from '@/types/poc';

export function usePoc(findingId?: string) {
  const queryClient = useQueryClient();

  const pocsQuery = useQuery({
    queryKey: ['pocs', findingId],
    queryFn: () => fetchPocs(findingId!),
    enabled: !!findingId,
  });

  const addStepMutation = useMutation({
    mutationFn: (params: { pocId: string; step: Omit<PocStep, 'id'> }) =>
      addPocStep(params.pocId, params.step),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pocs', findingId] });
    },
  });

  const deleteStepMutation = useMutation({
    mutationFn: (params: { pocId: string; stepId: string }) =>
      deletePocStep(params.pocId, params.stepId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pocs', findingId] });
    },
  });

  const exportPocMutation = useMutation({
    mutationFn: (params: { pocId: string; options: PocExportOptions }) =>
      exportPoc(params.pocId, params.options),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `poc-export.${blob.type.includes('pdf') ? 'pdf' : 'md'}`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  return {
    pocs: pocsQuery.data,
    isLoading: pocsQuery.isLoading,
    addStep: addStepMutation,
    deleteStep: deleteStepMutation,
    exportPoc: exportPocMutation,
  };
}
