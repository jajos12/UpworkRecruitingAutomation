import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importApi } from '../api';
import { BulkImportConfirmRequest } from '../types';

export function useParseRawText() {
  return useMutation({
    mutationFn: ({
      jobId,
      rawText,
      formatHint,
    }: {
      jobId: string;
      rawText: string;
      formatHint?: string;
    }) => importApi.parseRawText(jobId, rawText, formatHint),
  });
}

export function useConfirmImport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkImportConfirmRequest) => importApi.confirmImport(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['jobs', variables.job_id, 'proposals'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
    },
  });
}
