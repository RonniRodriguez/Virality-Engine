"""
Idea Inc - Idea Model

Represents an idea/meme in the simulation.
Ideas have virality scores, can mutate, and spread through the population.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class MutationType(str, Enum):
    """Types of idea mutations"""
    SIMPLIFY = "simplify"
    EMOTIONALIZE = "emotionalize"
    LOCALIZE = "localize"
    POLARIZE = "polarize"
    MEMEIFY = "memeify"
    RANDOM = "random"


@dataclass
class IdeaTarget:
    """Target demographics for an idea"""
    age_groups: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    
    def matches_agent(
        self,
        agent_age_group: str,
        agent_interests: List[str],
        agent_region: str,
    ) -> float:
        """
        Calculate how well this idea targets the agent.
        Returns a score from 0 to 1.
        """
        score = 0.0
        checks = 0
        
        # Age group match
        if self.age_groups:
            checks += 1
            if agent_age_group in self.age_groups:
                score += 1.0
        
        # Interest match
        if self.interests:
            checks += 1
            overlap = set(self.interests) & set(agent_interests)
            if overlap:
                score += len(overlap) / len(self.interests)
        
        # Region match
        if self.regions:
            checks += 1
            if agent_region in self.regions:
                score += 1.0
        
        if checks == 0:
            return 1.0  # No targeting = universal appeal
        
        return score / checks


@dataclass
class Idea:
    """
    Represents an idea/meme in the simulation.
    
    Ideas can:
    - Spread from agent to agent
    - Mutate into variants
    - Have varying virality and emotional appeal
    - Target specific demographics
    """
    
    id: UUID = field(default_factory=uuid4)
    creator_id: UUID = field(default_factory=uuid4)
    world_id: UUID = field(default_factory=uuid4)
    
    # Content
    text: str = ""
    tags: List[str] = field(default_factory=list)
    media_refs: List[str] = field(default_factory=list)
    target: IdeaTarget = field(default_factory=IdeaTarget)
    
    # Computed attributes (can be set by AI or calculated)
    virality_score: float = 0.2  # Base transmissibility (0-1)
    emotional_valence: float = 0.5  # Emotional intensity (0-1)
    complexity: float = 0.3  # How complex/nuanced (0-1, lower = easier to spread)
    
    # Mutation tracking
    parent_id: Optional[UUID] = None
    mutation_type: Optional[MutationType] = None
    generation: int = 0  # 0 = original, 1+ = mutations
    mutation_count: int = 0  # How many times this idea has mutated
    mutation_budget: int = 3  # Max mutations allowed
    
    # Vector DB reference
    embedding_id: Optional[str] = None
    
    # Statistics
    adopter_count: int = 0
    reach: int = 0  # Total unique exposures
    rejection_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def adoption_rate(self) -> float:
        """Calculate adoption rate"""
        if self.reach == 0:
            return 0.0
        return self.adopter_count / self.reach
    
    @property
    def effective_virality(self) -> float:
        """
        Calculate effective virality considering complexity.
        Simpler ideas spread more easily.
        """
        complexity_factor = 1.0 - (self.complexity * 0.5)
        return self.virality_score * complexity_factor
    
    @property
    def can_mutate(self) -> bool:
        """Check if idea can still mutate"""
        return self.mutation_count < self.mutation_budget
    
    def record_exposure(self) -> None:
        """Record an exposure (agent saw the idea)"""
        self.reach += 1
    
    def record_adoption(self) -> None:
        """Record an adoption"""
        self.adopter_count += 1
    
    def record_rejection(self) -> None:
        """Record a rejection"""
        self.rejection_count += 1
    
    def create_mutation(
        self,
        mutation_type: MutationType,
        new_text: str,
        virality_change: float = 0.0,
        emotional_change: float = 0.0,
    ) -> "Idea":
        """
        Create a mutated version of this idea.
        
        Args:
            mutation_type: Type of mutation applied
            new_text: New text content
            virality_change: Change in virality (-1 to 1)
            emotional_change: Change in emotional valence (-1 to 1)
        
        Returns:
            New mutated Idea instance
        """
        if not self.can_mutate:
            raise ValueError("Idea has exceeded mutation budget")
        
        # Increment mutation count on parent
        self.mutation_count += 1
        
        # Create mutant
        mutant = Idea(
            creator_id=self.creator_id,
            world_id=self.world_id,
            text=new_text,
            tags=self.tags.copy(),
            media_refs=self.media_refs.copy(),
            target=IdeaTarget(
                age_groups=self.target.age_groups.copy(),
                interests=self.target.interests.copy(),
                regions=self.target.regions.copy(),
            ),
            virality_score=max(0.0, min(1.0, self.virality_score + virality_change)),
            emotional_valence=max(0.0, min(1.0, self.emotional_valence + emotional_change)),
            complexity=self.complexity,
            parent_id=self.id,
            mutation_type=mutation_type,
            generation=self.generation + 1,
            mutation_budget=self.mutation_budget,
        )
        
        return mutant
    
    def calculate_spread_probability(
        self,
        sender_influence: float,
        receiver_openness: float,
        relevance: float,
        trust_factor: float = 1.0,
    ) -> float:
        """
        Calculate probability of spreading from sender to receiver.
        
        Args:
            sender_influence: Sender agent's influence (0-1)
            receiver_openness: Receiver agent's openness (0-1)
            relevance: How relevant to receiver's interests (0-1)
            trust_factor: Trust between agents (0-1)
        
        Returns:
            Spread probability (0-1)
        """
        p = (
            self.effective_virality
            * sender_influence
            * receiver_openness
            * relevance
            * trust_factor
            * (0.5 + self.emotional_valence * 0.5)  # Emotional boost
        )
        return max(0.0, min(1.0, p))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "id": str(self.id),
            "creator_id": str(self.creator_id),
            "world_id": str(self.world_id),
            "text": self.text,
            "tags": self.tags,
            "media_refs": self.media_refs,
            "target": {
                "age_groups": self.target.age_groups,
                "interests": self.target.interests,
                "regions": self.target.regions,
            },
            "virality_score": self.virality_score,
            "emotional_valence": self.emotional_valence,
            "complexity": self.complexity,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "mutation_type": self.mutation_type.value if self.mutation_type else None,
            "generation": self.generation,
            "mutation_count": self.mutation_count,
            "mutation_budget": self.mutation_budget,
            "embedding_id": self.embedding_id,
            "adopter_count": self.adopter_count,
            "reach": self.reach,
            "rejection_count": self.rejection_count,
            "adoption_rate": self.adoption_rate,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Idea":
        """Create idea from dictionary"""
        return cls(
            id=UUID(data["id"]),
            creator_id=UUID(data["creator_id"]),
            world_id=UUID(data["world_id"]),
            text=data["text"],
            tags=data.get("tags", []),
            media_refs=data.get("media_refs", []),
            target=IdeaTarget(
                age_groups=data.get("target", {}).get("age_groups", []),
                interests=data.get("target", {}).get("interests", []),
                regions=data.get("target", {}).get("regions", []),
            ),
            virality_score=data.get("virality_score", 0.2),
            emotional_valence=data.get("emotional_valence", 0.5),
            complexity=data.get("complexity", 0.3),
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            mutation_type=MutationType(data["mutation_type"]) if data.get("mutation_type") else None,
            generation=data.get("generation", 0),
            mutation_count=data.get("mutation_count", 0),
            mutation_budget=data.get("mutation_budget", 3),
            embedding_id=data.get("embedding_id"),
            adopter_count=data.get("adopter_count", 0),
            reach=data.get("reach", 0),
            rejection_count=data.get("rejection_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
        )

