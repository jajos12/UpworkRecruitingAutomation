import api from '@/lib/axios';
import { Job, JobCreate, JobCriteria, GenerateCriteriaRequest, Proposal, ProposalCreate, ChatMessage } from './types';

export const jobApi = {
  getJobs: async (): Promise<Job[]> => {
    const response = await api.get('/api/jobs');
    return response.data;
  },

  getJob: async (id: string): Promise<Job> => {
    const response = await api.get(`/api/jobs/${id}`);
    return response.data;
  },

  getJobProposals: async (jobId: string): Promise<Proposal[]> => {
    const response = await api.get(`/api/proposals?job_id=${jobId}`);
    return response.data;
  },

  getAllProposals: async (): Promise<Proposal[]> => {
    const response = await api.get('/api/proposals');
    return response.data;
  },

  updateProposalStatus: async (proposalId: string, status: string): Promise<void> => {
    await api.patch(`/api/proposals/${proposalId}/status`, { status });
  },

  createProposal: async (data: ProposalCreate): Promise<Proposal> => {
    const response = await api.post('/api/proposals', data);
    return response.data;
  },

  createJob: async (data: JobCreate): Promise<Job> => {
    const response = await api.post('/api/jobs', data);
    return response.data;
  },

  updateJob: async (id: string, data: JobCreate): Promise<Job> => {
    const response = await api.put(`/api/jobs/${id}`, data);
    return response.data;
  },

  deleteJob: async (id: string): Promise<void> => {
    await api.delete(`/api/jobs/${id}`);
  },

  generateCriteria: async (description: string): Promise<JobCriteria> => {
    const response = await api.post('/api/jobs/generate-criteria', { description });
    return response.data;
  },

  analyzeJob: async (id: string, force = false): Promise<any> => {
    const response = await api.post(`/api/analyze/job/${id}${force ? '?force=true' : ''}`);
    return response.data;
  },

  analyzeProposal: async (id: string): Promise<any> => {
    const response = await api.post(`/api/analyze/${id}`);
    return response.data;
  },

  generateInterviewGuide: async (proposalId: string, config?: any): Promise<any> => {
    const response = await api.post(`/api/analyze/interview/${proposalId}`, config);
    return response.data;
  },

  chatWithCandidate: async (proposalId: string, message: string): Promise<ChatMessage> => {
    const response = await api.post(`/api/analyze/chat/${proposalId}`, { message });
    return response.data;
  }
};

