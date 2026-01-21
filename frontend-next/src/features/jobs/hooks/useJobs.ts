import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobApi } from '../api';
import { JobCreate, ProposalCreate } from '../types';

export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: jobApi.getJobs,
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => jobApi.getJob(id),
    enabled: !!id,
  });
}

export function useJobProposals(jobId: string) {
  return useQuery({
    queryKey: ['jobs', jobId, 'proposals'],
    queryFn: () => jobApi.getJobProposals(jobId),
    enabled: !!jobId,
  });
}

export function useAllProposals() {
  return useQuery({
    queryKey: ['proposals'],
    queryFn: jobApi.getAllProposals,
  });
}

export function useUpdateProposalStatus() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => 
      jobApi.updateProposalStatus(id, status),
    onSuccess: (_, variables) => {
      // Invalidate all proposal queries to refresh lists
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useAnalyzeProposal() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => jobApi.analyzeProposal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useAnalyzeJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, force }: { id: string; force?: boolean }) => 
      jobApi.analyzeJob(id, force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: JobCreate) => jobApi.createJob(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useCreateProposal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProposalCreate) => jobApi.createProposal(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['jobs', variables.job_id, 'proposals'] });
    },
  });
}

export function useGenerateInterviewGuide() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ proposalId, config }: { proposalId: string; config?: any }) => 
      jobApi.generateInterviewGuide(proposalId, config),
    onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ['jobs'] });
    }
  });
}

export function useGenerateCriteria() {
  return useMutation({
    mutationFn: (description: string) => jobApi.generateCriteria(description),
  });
}

export function useChatWithCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ proposalId, message }: { proposalId: string; message: string }) => 
      jobApi.chatWithCandidate(proposalId, message),
    onSuccess: () => {
         // Silently update cache without triggering loading states if possible? 
         // For now just invalidate to be safe about data persistence
         queryClient.invalidateQueries({ queryKey: ['proposals'] });
         queryClient.invalidateQueries({ queryKey: ['jobs'] });
    }
  });
}

