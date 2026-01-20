export interface JobCriteria {
  must_have: string[];
  nice_to_have: Array<{ text: string; weight: number | string }>;
  red_flags: string[];
}

export interface Job {
  job_id: string;
  title: string;
  description: string;
  criteria: JobCriteria;
  proposal_count: number;
  tier1_count: number;
  tier2_count: number;
  tier3_count: number;
  created_at: string;
}

export interface JobCreate {
  title: string;
  description: string;
  criteria?: JobCriteria;
}

export interface GenerateCriteriaRequest {
  description: string;
}

export interface FreelancerProfile {
  freelancer_id: string;
  name: string;
  title: string;
  hourly_rate?: number;
  job_success_score?: number;
  total_earnings?: number;
  top_rated_status?: string;
  skills: string[];
  bio?: string;
  profile_url?: string;
}

export interface Proposal {
  proposal_id: string;
  job_id: string;
  freelancer: FreelancerProfile;
  cover_letter: string;
  bid_amount: number;
  ai_score?: number;
  ai_tier?: number;
  ai_reasoning?: string;
  status: 'pending' | 'tier1' | 'tier2' | 'tier3' | 'rejected' | 'approved';
  created_at: string;
}
