export interface WorldConfig {
  population_size: number;
  network_type: 'scale_free' | 'small_world' | 'random';
  network_density: number;
  mutation_rate: number;
  decay_rate: number;
  time_step_ms: number;
  max_steps?: number;
}

export interface World {
  id: string;
  creator_id: string;
  name: string;
  description: string;
  config: WorldConfig;
  status: 'created' | 'running' | 'paused' | 'completed';
  current_step: number;
  agent_count: number;
  idea_count: number;
  is_public: boolean;
  created_at: string;
  total_spread_events: number;
  total_adoptions: number;
}

export interface CreateWorldRequest {
  name: string;
  description?: string;
  config: Partial<WorldConfig>;
  is_public: boolean;
}

export interface WorldSnapshot {
  world_id: string;
  step: number;
  total_agents: number;
  active_agents: number;
  total_ideas: number;
  total_adoptions: number;
  idea_stats: {
    idea_id: string;
    text: string;
    adopters: number;
    reach: number;
    adoption_rate: number;
  }[];
  regional_stats: Record<string, {
    total_agents: number;
    active_agents: number;
    saturation: number;
  }>;
}

