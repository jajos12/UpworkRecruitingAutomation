import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobApi } from '../api';
import { JobCreate } from '../types';

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

export function useCreateJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: JobCreate) => jobApi.createJob(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useGenerateCriteria() {
  return useMutation({
    mutationFn: (description: string) => jobApi.generateCriteria(description),
  });
}
