"""
Idea Inc - Agent Model

Represents an individual agent in the simulation.
Agents have profiles, beliefs, connections, and states.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4


@dataclass
class AgentProfile:
    """Agent demographic and personality profile"""
    age_group: str = "25-34"
    interests: List[str] = field(default_factory=list)
    region: str = "NA"
    trust_threshold: float = 0.5  # 0-1: how easily they trust
    openness: float = 0.5  # 0-1: openness to new ideas
    influence: float = 0.1  # 0-1: how influential they are
    
    @classmethod
    def random(cls, region: str = "NA") -> "AgentProfile":
        """Generate a random agent profile"""
        age_groups = ["13-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
        interests_pool = [
            "tech", "music", "sports", "politics", "science", "art",
            "gaming", "fashion", "food", "travel", "health", "finance",
            "entertainment", "education", "environment", "social"
        ]
        
        return cls(
            age_group=random.choice(age_groups),
            interests=random.sample(interests_pool, k=random.randint(2, 5)),
            region=region,
            trust_threshold=random.betavariate(2, 2),  # Bell curve around 0.5
            openness=random.betavariate(2, 2),
            influence=random.betavariate(1, 5),  # Skewed low (few influencers)
        )


@dataclass
class AgentState:
    """Agent's current state"""
    mood: float = 0.0  # -1 to 1: negative to positive
    susceptibility: float = 0.5  # 0-1: current susceptibility to ideas
    last_active_step: int = 0
    exposure_count: int = 0  # Total exposures to ideas
    adoption_count: int = 0  # Ideas adopted
    
    def update_susceptibility(self, adopted: bool) -> None:
        """Update susceptibility based on adoption decision"""
        if adopted:
            # Slightly decrease susceptibility after adoption
            self.susceptibility = max(0.1, self.susceptibility * 0.95)
        else:
            # Slightly increase susceptibility after rejection (openness)
            self.susceptibility = min(0.9, self.susceptibility * 1.02)


@dataclass
class Agent:
    """
    Represents an individual in the simulation.
    
    Agents can:
    - Receive ideas from connections
    - Decide to adopt or reject ideas
    - Spread adopted ideas to connections
    - Have their beliefs decay over time
    """
    
    id: UUID = field(default_factory=uuid4)
    world_id: UUID = field(default_factory=uuid4)
    profile: AgentProfile = field(default_factory=AgentProfile)
    state: AgentState = field(default_factory=AgentState)
    
    # Social graph
    connections: Set[UUID] = field(default_factory=set)
    
    # Beliefs (adopted ideas)
    beliefs: Set[UUID] = field(default_factory=set)
    
    # Memory: idea_id -> exposure count (for reinforcement)
    idea_exposures: Dict[UUID, int] = field(default_factory=dict)
    
    # Vector DB references for RAG (future)
    memory_refs: List[str] = field(default_factory=list)
    
    def add_connection(self, agent_id: UUID) -> None:
        """Add a connection to another agent"""
        if agent_id != self.id:
            self.connections.add(agent_id)
    
    def remove_connection(self, agent_id: UUID) -> None:
        """Remove a connection"""
        self.connections.discard(agent_id)
    
    def has_idea(self, idea_id: UUID) -> bool:
        """Check if agent has adopted an idea"""
        return idea_id in self.beliefs
    
    def expose_to_idea(self, idea_id: UUID) -> int:
        """
        Record exposure to an idea.
        Returns the new exposure count.
        """
        self.state.exposure_count += 1
        current = self.idea_exposures.get(idea_id, 0)
        self.idea_exposures[idea_id] = current + 1
        return current + 1
    
    def adopt_idea(self, idea_id: UUID) -> bool:
        """
        Adopt an idea.
        Returns True if newly adopted, False if already had it.
        """
        if idea_id in self.beliefs:
            return False
        
        self.beliefs.add(idea_id)
        self.state.adoption_count += 1
        self.state.update_susceptibility(adopted=True)
        return True
    
    def forget_idea(self, idea_id: UUID) -> bool:
        """
        Forget an idea (decay).
        Returns True if forgotten, False if didn't have it.
        """
        if idea_id not in self.beliefs:
            return False
        
        self.beliefs.discard(idea_id)
        return True
    
    def calculate_adoption_probability(
        self,
        idea_virality: float,
        idea_relevance: float,
        sender_influence: float,
        trust_factor: float = 1.0,
        context_modifier: float = 1.0,
    ) -> float:
        """
        Calculate probability of adopting an idea.
        
        Formula:
        p = base_virality * sender_influence * openness * relevance * trust * context
        
        Args:
            idea_virality: Base virality of the idea (0-1)
            idea_relevance: How relevant the idea is to agent's interests (0-1)
            sender_influence: Influence of the sending agent (0-1)
            trust_factor: Trust between agents (0-1)
            context_modifier: World/event context modifier (0-2)
        
        Returns:
            Probability of adoption (0-1)
        """
        # Get exposure count for reinforcement
        # Multiple exposures increase adoption probability
        exposure_bonus = 1.0
        
        # Base probability
        p = (
            idea_virality
            * sender_influence
            * self.profile.openness
            * idea_relevance
            * trust_factor
            * context_modifier
            * self.state.susceptibility
            * exposure_bonus
        )
        
        # Clamp to valid probability range
        return max(0.0, min(1.0, p))
    
    def calculate_idea_relevance(self, idea_tags: List[str]) -> float:
        """
        Calculate how relevant an idea is to this agent.
        Based on interest overlap.
        """
        if not idea_tags or not self.profile.interests:
            return 0.3  # Base relevance for untagged ideas
        
        overlap = set(idea_tags) & set(self.profile.interests)
        if not overlap:
            return 0.2  # Minimal relevance
        
        # More overlap = higher relevance
        relevance = len(overlap) / max(len(idea_tags), len(self.profile.interests))
        return 0.2 + (relevance * 0.8)  # Scale to 0.2-1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "id": str(self.id),
            "world_id": str(self.world_id),
            "profile": {
                "age_group": self.profile.age_group,
                "interests": self.profile.interests,
                "region": self.profile.region,
                "trust_threshold": self.profile.trust_threshold,
                "openness": self.profile.openness,
                "influence": self.profile.influence,
            },
            "state": {
                "mood": self.state.mood,
                "susceptibility": self.state.susceptibility,
                "last_active_step": self.state.last_active_step,
                "exposure_count": self.state.exposure_count,
                "adoption_count": self.state.adoption_count,
            },
            "connections": [str(c) for c in self.connections],
            "beliefs": [str(b) for b in self.beliefs],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Agent":
        """Create agent from dictionary"""
        agent = cls(
            id=UUID(data["id"]),
            world_id=UUID(data["world_id"]),
            profile=AgentProfile(
                age_group=data["profile"]["age_group"],
                interests=data["profile"]["interests"],
                region=data["profile"]["region"],
                trust_threshold=data["profile"]["trust_threshold"],
                openness=data["profile"]["openness"],
                influence=data["profile"]["influence"],
            ),
            state=AgentState(
                mood=data["state"]["mood"],
                susceptibility=data["state"]["susceptibility"],
                last_active_step=data["state"]["last_active_step"],
                exposure_count=data["state"]["exposure_count"],
                adoption_count=data["state"]["adoption_count"],
            ),
        )
        agent.connections = {UUID(c) for c in data["connections"]}
        agent.beliefs = {UUID(b) for b in data["beliefs"]}
        return agent

