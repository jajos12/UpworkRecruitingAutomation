import api from '@/lib/axios';
import { BulkImportParseResponse, BulkImportConfirmRequest, BulkImportConfirmResponse } from './types';

export const importApi = {
  parseRawText: async (
    jobId: string,
    rawText: string,
    formatHint?: string
  ): Promise<BulkImportParseResponse> => {
    const response = await api.post('/api/import/parse', {
      job_id: jobId,
      raw_text: rawText,
      input_format_hint: formatHint || null,
    });
    return response.data;
  },

  confirmImport: async (data: BulkImportConfirmRequest): Promise<BulkImportConfirmResponse> => {
    const response = await api.post('/api/import/confirm', data);
    return response.data;
  },
};
