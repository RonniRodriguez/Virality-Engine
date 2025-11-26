"""
Idea Inc - World Model

Represents a simulation world with agents, ideas, and network topology.
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import networkx as nx

from .agent import Agent, AgentProfile
from .idea import Idea, MutationType


class WorldStatus(str, Enum):
    """World status states"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NetworkType(str, Enum):
    """Network topology types"""
    SCALE_FREE = "scale_free"
    SMALL_WORLD = "small_world"
    RANDOM = "random"
    GEO_LOCAL = "geo_local"


@dataclass
class WorldConfig:
    """World configuration parameters"""
    population_size: int = 10000
    network_type: NetworkType = NetworkType.SCALE_FREE
    network_density: float = 0.1  # Average connections / population
    mutation_rate: float = 0.01  # Probability of mutation per spread
    decay_rate: float = 0.001  # Probability of forgetting per step
    time_step_ms: int = 100  # Milliseconds per simulation step
    max_steps: Optional[int] = None  # None = infinite
    
    # Regional distribution
    regions: List[str] = field(default_factory=lambda: ["NA", "EU", "ASIA", "LATAM", "AFRICA", "OCEANIA"])
    region_weights: List[float] = field(default_factory=lambda: [0.2, 0.25, 0.35, 0.1, 0.05, 0.05])


@dataclass
class WorldSnapshot:
    """Point-in-time snapshot of world state"""
    world_id: UUID
    step: int
    timestamp: datetime
    total_agents: int
    active_agents: int  # Agents with at least one belief
    total_ideas: int
    total_adoptions: int
    
    # Per-idea stats
    idea_stats: List[Dict] = field(default_factory=list)
    
    # Regional breakdown
    regional_stats: Dict[str, Dict] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "world_id": str(self.world_id),
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "total_ideas": self.total_ideas,
            "total_adoptions": self.total_adoptions,
            "idea_stats": self.idea_stats,
            "regional_stats": self.regional_stats,
        }


@dataclass
class SpreadEvent:
    """Event recording an idea spread attempt"""
    idea_id: UUID
    from_agent_id: UUID
    to_agent_id: UUID
    probability: float
    accepted: bool
    step: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class World:
    """
    Simulation world containing agents and ideas.
    
    Manages:
    - Agent population and network
    - Idea propagation
    - Mutation triggers
    - Snapshot generation
    """
    
    def __init__(
        self,
        id: UUID,
        creator_id: UUID,
        name: str,
        config: WorldConfig,
        description: str = "",
        is_public: bool = True,
    ):
        self.id = id
        self.creator_id = creator_id
        self.name = name
        self.description = description
        self.config = config
        self.is_public = is_public
        
        self.status = WorldStatus.CREATED
        self.current_step = 0
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Population
        self.agents: Dict[UUID, Agent] = {}
        self.ideas: Dict[UUID, Idea] = {}
        
        # Network graph
        self.network: nx.Graph = nx.Graph()
        
        # Event log (recent events, could be sent to Kafka)
        self.recent_events: List[SpreadEvent] = []
        self.max_recent_events = 1000
        
        # Statistics
        self.total_spread_events = 0
        self.total_adoptions = 0
        self.total_mutations = 0
    
    @property
    def agent_count(self) -> int:
        return len(self.agents)
    
    @property
    def idea_count(self) -> int:
        return len(self.ideas)
    
    def initialize_population(self) -> None:
        """Create initial agent population with network connections"""
        # Create agents
        for i in range(self.config.population_size):
            # Assign region based on weights
            region = random.choices(
                self.config.regions,
                weights=self.config.region_weights,
            )[0]
            
            agent = Agent(
                world_id=self.id,
                profile=AgentProfile.random(region=region),
            )
            self.agents[agent.id] = agent
            self.network.add_node(agent.id)
        
        # Create network connections based on topology
        self._create_network()
    
    def _create_network(self) -> None:
        """Create network connections between agents"""
        agent_ids = list(self.agents.keys())
        n = len(agent_ids)
        
        if self.config.network_type == NetworkType.SCALE_FREE:
            # Barabási–Albert model: preferential attachment
            # Creates hubs (influencers)
            m = max(2, int(n * self.config.network_density / 2))
            temp_graph = nx.barabasi_albert_graph(n, m)
            
        elif self.config.network_type == NetworkType.SMALL_WORLD:
            # Watts-Strogatz model: high clustering, short paths
            k = max(4, int(n * self.config.network_density))
            temp_graph = nx.watts_strogatz_graph(n, k, 0.3)
            
        elif self.config.network_type == NetworkType.RANDOM:
            # Erdős–Rényi random graph
            p = self.config.network_density
            temp_graph = nx.erdos_renyi_graph(n, p)
            
        else:  # GEO_LOCAL
            # Geographic proximity (simplified)
            # Connect agents in same region more often
            temp_graph = nx.Graph()
            temp_graph.add_nodes_from(range(n))
            
            for i in range(n):
                agent_i = self.agents[agent_ids[i]]
                connections_to_make = max(1, int(n * self.config.network_density))
                
                for _ in range(connections_to_make):
                    j = random.randint(0, n - 1)
                    if i != j:
                        agent_j = self.agents[agent_ids[j]]
                        # Higher probability if same region
                        if agent_i.profile.region == agent_j.profile.region:
                            if random.random() < 0.7:
                                temp_graph.add_edge(i, j)
                        else:
                            if random.random() < 0.3:
                                temp_graph.add_edge(i, j)
        
        # Map temp graph edges to actual agent IDs
        for i, j in temp_graph.edges():
            agent_i_id = agent_ids[i]
            agent_j_id = agent_ids[j]
            
            self.network.add_edge(agent_i_id, agent_j_id)
            self.agents[agent_i_id].add_connection(agent_j_id)
            self.agents[agent_j_id].add_connection(agent_i_id)
    
    def inject_idea(self, idea: Idea, initial_adopters: int = 1) -> List[UUID]:
        """
        Inject an idea into the world.
        
        Args:
            idea: The idea to inject
            initial_adopters: Number of random agents to seed with the idea
        
        Returns:
            List of agent IDs that initially adopted the idea
        """
        idea.world_id = self.id
        self.ideas[idea.id] = idea
        
        # Select random initial adopters
        # Prefer agents matching target demographics
        candidates = list(self.agents.values())
        
        # Score candidates by target match
        scored = []
        for agent in candidates:
            score = idea.target.matches_agent(
                agent.profile.age_group,
                agent.profile.interests,
                agent.profile.region,
            )
            # Weight by influence (influencers more likely to be seeds)
            score *= (0.5 + agent.profile.influence)
            scored.append((agent, score))
        
        # Sort by score and select top candidates
        scored.sort(key=lambda x: x[1], reverse=True)
        top_candidates = [a for a, _ in scored[:max(initial_adopters * 10, 100)]]
        
        # Randomly select from top candidates
        adopters = random.sample(
            top_candidates,
            min(initial_adopters, len(top_candidates)),
        )
        
        adopted_ids = []
        for agent in adopters:
            if agent.adopt_idea(idea.id):
                idea.record_adoption()
                adopted_ids.append(agent.id)
        
        return adopted_ids
    
    async def run_step(self) -> Dict:
        """
        Run a single simulation step.
        
        Returns:
            Statistics about the step
        """
        if self.status != WorldStatus.RUNNING:
            return {"error": "World is not running"}
        
        start_time = time.time()
        
        spread_attempts = 0
        adoptions = 0
        mutations = 0
        decays = 0
        
        # Get all agents with beliefs (potential spreaders)
        spreaders = [
            agent for agent in self.agents.values()
            if agent.beliefs
        ]
        
        # Shuffle for randomness
        random.shuffle(spreaders)
        
        for spreader in spreaders:
            # For each idea the spreader has
            for idea_id in list(spreader.beliefs):
                idea = self.ideas.get(idea_id)
                if not idea:
                    continue
                
                # Try to spread to each connection
                for connection_id in spreader.connections:
                    receiver = self.agents.get(connection_id)
                    if not receiver or receiver.has_idea(idea_id):
                        continue
                    
                    # Calculate spread probability
                    relevance = receiver.calculate_idea_relevance(idea.tags)
                    probability = idea.calculate_spread_probability(
                        sender_influence=spreader.profile.influence,
                        receiver_openness=receiver.profile.openness,
                        relevance=relevance,
                    )
                    
                    spread_attempts += 1
                    idea.record_exposure()
                    receiver.expose_to_idea(idea_id)
                    
                    # Attempt spread
                    if random.random() < probability:
                        receiver.adopt_idea(idea_id)
                        idea.record_adoption()
                        adoptions += 1
                        self.total_adoptions += 1
                        
                        # Record event
                        event = SpreadEvent(
                            idea_id=idea_id,
                            from_agent_id=spreader.id,
                            to_agent_id=receiver.id,
                            probability=probability,
                            accepted=True,
                            step=self.current_step,
                        )
                        self._record_event(event)
                        
                        # Check for mutation
                        if (
                            idea.can_mutate
                            and random.random() < self.config.mutation_rate
                        ):
                            mutant = self._trigger_mutation(idea)
                            if mutant:
                                mutations += 1
                                self.total_mutations += 1
                    else:
                        idea.record_rejection()
        
        # Apply decay (forgetting)
        for agent in self.agents.values():
            for idea_id in list(agent.beliefs):
                if random.random() < self.config.decay_rate:
                    if agent.forget_idea(idea_id):
                        decays += 1
        
        # Update step counter
        self.current_step += 1
        
        # Check completion
        if self.config.max_steps and self.current_step >= self.config.max_steps:
            self.status = WorldStatus.COMPLETED
            self.completed_at = datetime.utcnow()
        
        duration_ms = (time.time() - start_time) * 1000
        
        return {
            "step": self.current_step,
            "spread_attempts": spread_attempts,
            "adoptions": adoptions,
            "mutations": mutations,
            "decays": decays,
            "duration_ms": round(duration_ms, 2),
            "active_agents": sum(1 for a in self.agents.values() if a.beliefs),
        }
    
    def _trigger_mutation(self, idea: Idea) -> Optional[Idea]:
        """
        Trigger a mutation on an idea.
        
        For MVP, this creates a simple deterministic mutation.
        In v1+, this would call the AI service.
        """
        if not idea.can_mutate:
            return None
        
        # Simple mutation: slightly modify virality and emotional valence
        mutation_type = random.choice(list(MutationType))
        
        # Determine changes based on mutation type
        virality_change = 0.0
        emotional_change = 0.0
        new_text = idea.text
        
        if mutation_type == MutationType.SIMPLIFY:
            virality_change = 0.05
            new_text = f"[Simplified] {idea.text[:100]}..."
        elif mutation_type == MutationType.EMOTIONALIZE:
            emotional_change = 0.1
            virality_change = 0.02
            new_text = f"[Emotional] {idea.text}"
        elif mutation_type == MutationType.POLARIZE:
            emotional_change = 0.15
            virality_change = 0.08
            new_text = f"[Polarized] {idea.text}"
        elif mutation_type == MutationType.MEMEIFY:
            virality_change = 0.1
            new_text = f"[Meme] {idea.text[:50]}... 🔥"
        else:
            virality_change = random.uniform(-0.05, 0.1)
            emotional_change = random.uniform(-0.05, 0.1)
            new_text = f"[Variant] {idea.text}"
        
        try:
            mutant = idea.create_mutation(
                mutation_type=mutation_type,
                new_text=new_text,
                virality_change=virality_change,
                emotional_change=emotional_change,
            )
            self.ideas[mutant.id] = mutant
            return mutant
        except ValueError:
            return None
    
    def _record_event(self, event: SpreadEvent) -> None:
        """Record a spread event"""
        self.recent_events.append(event)
        self.total_spread_events += 1
        
        # Trim old events
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events = self.recent_events[-self.max_recent_events:]
    
    def get_snapshot(self) -> WorldSnapshot:
        """Generate a snapshot of current world state"""
        # Calculate per-idea stats
        idea_stats = []
        for idea in self.ideas.values():
            idea_stats.append({
                "idea_id": str(idea.id),
                "text": idea.text[:100],
                "adopters": idea.adopter_count,
                "reach": idea.reach,
                "adoption_rate": idea.adoption_rate,
                "mutations": idea.mutation_count,
                "generation": idea.generation,
            })
        
        # Sort by adopters
        idea_stats.sort(key=lambda x: x["adopters"], reverse=True)
        
        # Calculate regional stats
        regional_stats = {}
        for region in self.config.regions:
            region_agents = [
                a for a in self.agents.values()
                if a.profile.region == region
            ]
            active = sum(1 for a in region_agents if a.beliefs)
            total_adoptions = sum(len(a.beliefs) for a in region_agents)
            
            regional_stats[region] = {
                "total_agents": len(region_agents),
                "active_agents": active,
                "total_adoptions": total_adoptions,
                "saturation": active / len(region_agents) if region_agents else 0,
            }
        
        return WorldSnapshot(
            world_id=self.id,
            step=self.current_step,
            timestamp=datetime.utcnow(),
            total_agents=len(self.agents),
            active_agents=sum(1 for a in self.agents.values() if a.beliefs),
            total_ideas=len(self.ideas),
            total_adoptions=self.total_adoptions,
            idea_stats=idea_stats,
            regional_stats=regional_stats,
        )
    
    def start(self) -> None:
        """Start the simulation"""
        if self.status == WorldStatus.CREATED:
            self.status = WorldStatus.RUNNING
            self.started_at = datetime.utcnow()
    
    def pause(self) -> None:
        """Pause the simulation"""
        if self.status == WorldStatus.RUNNING:
            self.status = WorldStatus.PAUSED
    
    def resume(self) -> None:
        """Resume the simulation"""
        if self.status == WorldStatus.PAUSED:
            self.status = WorldStatus.RUNNING
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "id": str(self.id),
            "creator_id": str(self.creator_id),
            "name": self.name,
            "description": self.description,
            "config": {
                "population_size": self.config.population_size,
                "network_type": self.config.network_type.value,
                "network_density": self.config.network_density,
                "mutation_rate": self.config.mutation_rate,
                "decay_rate": self.config.decay_rate,
                "time_step_ms": self.config.time_step_ms,
                "max_steps": self.config.max_steps,
            },
            "status": self.status.value,
            "current_step": self.current_step,
            "agent_count": self.agent_count,
            "idea_count": self.idea_count,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_spread_events": self.total_spread_events,
            "total_adoptions": self.total_adoptions,
            "total_mutations": self.total_mutations,
        }

