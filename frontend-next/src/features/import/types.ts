import { FreelancerProfile } from '../jobs/types';

export interface ParsedApplicant {
  freelancer: FreelancerProfile;
  cover_letter: string;
  bid_amount: number;
  estimated_duration?: string;
  screening_answers?: string;
  confidence: number;
  parse_notes: string[];
}

export interface BulkImportParseResponse {
  applicants: ParsedApplicant[];
  total_found: number;
  parse_warnings: string[];
}

export interface BulkImportConfirmRequest {
  job_id: string;
  applicants: ParsedApplicant[];
  auto_analyze: boolean;
}

export interface BulkImportConfirmResponse {
  imported_count: number;
  proposal_ids: string[];
  failed: Array<{ name: string; error: string }>;
}
