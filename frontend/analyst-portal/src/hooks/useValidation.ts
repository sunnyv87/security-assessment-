import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchNotes,
  createNote,
  fetchChecklist,
  updateChecklistItem,
  submitValidation,
} from '@/lib/api-client';
import type { ValidationSubmission } from '@/types/validation';

export function useValidation(findingId: string) {
  const queryClient = useQueryClient();

  const notesQuery = useQuery({
    queryKey: ['notes', findingId],
    queryFn: () => fetchNotes(findingId),
  });

  const checklistQuery = useQuery({
    queryKey: ['checklist', findingId],
    queryFn: () => fetchChecklist(findingId),
  });

  const createNoteMutation = useMutation({
    mutationFn: (params: { content: string; attachments?: File[] }) =>
      createNote(findingId, params.content, params.attachments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', findingId] });
    },
  });

  const updateChecklistItemMutation = useMutation({
    mutationFn: (params: { itemId: string; checked: boolean }) =>
      updateChecklistItem(findingId, params.itemId, params.checked),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checklist', findingId] });
    },
  });

  const submitVerdictMutation = useMutation({
    mutationFn: (data: ValidationSubmission) => submitValidation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finding', findingId] });
      queryClient.invalidateQueries({ queryKey: ['findings'] });
    },
  });

  return {
    notes: notesQuery.data,
    checklist: checklistQuery.data,
    createNote: createNoteMutation,
    updateChecklistItem: updateChecklistItemMutation,
    submitVerdict: submitVerdictMutation,
  };
}
