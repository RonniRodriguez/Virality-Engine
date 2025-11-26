import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import type { World, CreateWorldRequest, WorldSnapshot } from '../types/world';

export const useWorlds = () => {
  const queryClient = useQueryClient();

  const worldsQuery = useQuery({
    queryKey: ['worlds'],
    queryFn: async () => {
      const response = await api.get<World[]>('/worlds');
      return response.data;
    },
  });

  const createWorldMutation = useMutation({
    mutationFn: async (data: CreateWorldRequest) => {
      const response = await api.post<World>('/worlds', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worlds'] });
    },
  });

  return {
    worlds: worldsQuery,
    createWorld: createWorldMutation,
  };
};

export const useWorld = (worldId: string) => {
  const queryClient = useQueryClient();

  const worldQuery = useQuery({
    queryKey: ['world', worldId],
    queryFn: async () => {
      const response = await api.get<World>(`/worlds/${worldId}`);
      return response.data;
    },
    enabled: !!worldId,
    refetchInterval: (query) => {
      // Poll more frequently if running
      return query.state?.data?.status === 'running' ? 1000 : 5000;
    },
  });

  const startMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<World>(`/worlds/${worldId}/start`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['world', worldId] });
    },
  });

  const stopMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<World>(`/worlds/${worldId}/stop`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['world', worldId] });
    },
  });

  const snapshotQuery = useQuery({
    queryKey: ['world', worldId, 'snapshot'],
    queryFn: async () => {
      const response = await api.get<WorldSnapshot>(`/worlds/${worldId}/snapshot`);
      return response.data;
    },
    enabled: !!worldId && worldQuery.data?.status === 'running',
    refetchInterval: 1000, // Real-time updates
  });

  return {
    world: worldQuery,
    snapshot: snapshotQuery,
    start: startMutation,
    stop: stopMutation,
  };
};
