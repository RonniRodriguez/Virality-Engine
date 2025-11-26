import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export interface InjectIdeaRequest {
  world_id: string;
  text: string;
  tags: string[];
  target: {
    age_groups: string[];
    interests: string[];
    regions: string[];
  };
  virality_score: number;
  emotional_valence: number;
  initial_adopters: number;
}

export const useIdea = (worldId?: string) => {
  const queryClient = useQueryClient();

  const injectIdeaMutation = useMutation({
    mutationFn: async (data: InjectIdeaRequest) => {
      const response = await api.post(`/worlds/${data.world_id}/ideas`, data);
      return response.data;
    },
    onSuccess: () => {
      if (worldId) {
        queryClient.invalidateQueries({ queryKey: ['world', worldId] });
      }
    },
  });

  return {
    injectIdea: injectIdeaMutation,
  };
};

