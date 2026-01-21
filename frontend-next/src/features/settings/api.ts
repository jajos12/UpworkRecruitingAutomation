import axios from '@/lib/axios';

export interface Config {
  // AI Config
  ai_provider: string;
  openai_model?: string;
  gemini_model?: string;
  claude_model?: string;
  has_openai_key?: boolean;
  has_gemini_key?: boolean;
  has_claude_key?: boolean;
  
  // Upwork Config
  has_upwork_client_id?: boolean;
  has_upwork_secret?: boolean;
  has_upwork_token?: boolean;
  
  // Google Sheets Config
  google_sheet_id?: string;
  has_google_creds?: boolean;
}

export interface ConfigUpdatePayload {
  ai_provider?: string;
  api_key?: string;
  model_name?: string;
  
  upwork_client_id?: string;
  upwork_client_secret?: string;
  upwork_access_token?: string;
  
  google_sheets_creds_json?: string;
  google_sheet_id?: string;
}

export const getConfig = async (): Promise<Config> => {
  const { data } = await axios.get('/api/config');
  return data;
};

export const updateConfig = async (payload: ConfigUpdatePayload): Promise<{ status: string; message: string }> => {
  const { data } = await axios.post('/api/config', payload);
  return data;
};

export interface PipelineRunRequest {
  fetch: boolean;
  analyze: boolean;
  communicate: boolean;
  dry_run: boolean;
}

export const runPipeline = async (payload: PipelineRunRequest): Promise<{ status: string; message: string }> => {
  const { data } = await axios.post('/api/pipeline/run', payload);
  return data;
};
