import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getConfig, updateConfig, ConfigUpdatePayload } from '../api';

export const useConfig = () => {
  return useQuery({
    queryKey: ['config'],
    queryFn: getConfig,
  });
};

export const useUpdateConfig = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (payload: ConfigUpdatePayload) => updateConfig(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
    },
  });
};
