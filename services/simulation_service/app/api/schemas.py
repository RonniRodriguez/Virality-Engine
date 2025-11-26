"""
Idea Inc - Simulation Service API Schemas

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# World Schemas
# =============================================================================

class WorldConfigCreate(BaseModel):
    """World configuration for creation"""
    population_size: int = Field(default=10000, ge=100, le=100000)
    network_type: str = Field(default="scale_free")
    network_density: float = Field(default=0.1, ge=0.01, le=1.0)
    mutation_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    decay_rate: float = Field(default=0.001, ge=0.0, le=1.0)
    time_step_ms: int = Field(default=100, ge=10, le=10000)
    max_steps: Optional[int] = Field(default=None, ge=1)


class WorldCreate(BaseModel):
    """World creation request"""
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    config: WorldConfigCreate = Field(default_factory=WorldConfigCreate)
    is_public: bool = True


class WorldResponse(BaseModel):
    """World response"""
    id: UUID
    creator_id: UUID
    name: str
    description: str
    config: Dict
    status: str
    current_step: int
    agent_count: int
    idea_count: int
    is_public: bool
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_spread_events: int
    total_adoptions: int
    total_mutations: int


class WorldListItem(BaseModel):
    """World list item (summary)"""
    id: UUID
    name: str
    description: str
    status: str
    agent_count: int
    idea_count: int
    current_step: int
    is_public: bool
    creator_id: UUID
    created_at: datetime


# =============================================================================
# Idea Schemas
# =============================================================================

class IdeaTargetCreate(BaseModel):
    """Idea target demographics"""
    age_groups: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)


class IdeaCreate(BaseModel):
    """Idea creation/injection request"""
    text: str = Field(min_length=1, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    target: IdeaTargetCreate = Field(default_factory=IdeaTargetCreate)
    virality_score: float = Field(default=0.2, ge=0.0, le=1.0)
    emotional_valence: float = Field(default=0.5, ge=0.0, le=1.0)
    initial_adopters: int = Field(default=1, ge=1, le=100)


class IdeaResponse(BaseModel):
    """Idea response"""
    id: UUID
    creator_id: UUID
    world_id: UUID
    text: str
    tags: List[str]
    target: Dict
    virality_score: float
    emotional_valence: float
    complexity: float
    parent_id: Optional[UUID]
    mutation_type: Optional[str]
    generation: int
    mutation_count: int
    mutation_budget: int
    adopter_count: int
    reach: int
    rejection_count: int
    adoption_rate: float
    created_at: datetime


# =============================================================================
# Snapshot Schemas
# =============================================================================

class IdeaStats(BaseModel):
    """Per-idea statistics"""
    idea_id: str
    text: str
    adopters: int
    reach: int
    adoption_rate: float
    mutations: int
    generation: int


class RegionalStats(BaseModel):
    """Per-region statistics"""
    total_agents: int
    active_agents: int
    total_adoptions: int
    saturation: float


class SnapshotResponse(BaseModel):
    """World snapshot response"""
    world_id: UUID
    step: int
    timestamp: datetime
    total_agents: int
    active_agents: int
    total_ideas: int
    total_adoptions: int
    idea_stats: List[Dict]
    regional_stats: Dict[str, Dict]


# =============================================================================
# Step Schemas
# =============================================================================

class StepRequest(BaseModel):
    """Manual step request"""
    steps: int = Field(default=1, ge=1, le=1000)


class StepResult(BaseModel):
    """Single step result"""
    step: int
    spread_attempts: int
    adoptions: int
    mutations: int
    decays: int
    duration_ms: float
    active_agents: int


class StepResponse(BaseModel):
    """Step response (multiple steps)"""
    world_id: UUID
    results: List[StepResult]
    final_step: int


# =============================================================================
# Common Schemas
# =============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None

