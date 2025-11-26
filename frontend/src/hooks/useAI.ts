and import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

export interface GenerateIdeaRequest {
  topic: string;
  audience: string;
  tone: string;
  virality: 'low' | 'medium' | 'high';
}

export interface AnalyzeIdeaRequest {
  idea_text: string;
}

export interface AIAnalysisResponse {
  virality_score: number;
  emotional_valence: number;
  complexity: number;
  controversy_level: number;
  shareability: number;
  target_demographics: string[];
}

export const useAI = () => {
  const generateMutation = useMutation({
    mutationFn: async (data: GenerateIdeaRequest) => {
      const response = await api.post('/ai/generate', data);
      return response.data;
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: async (data: AnalyzeIdeaRequest) => {
      const response = await api.post<AIAnalysisResponse>('/ai/analyze', data);
      return response.data;
    },
  });

  return {
    generate: generateMutation,
    analyze: analyzeMutation,
  };
};

