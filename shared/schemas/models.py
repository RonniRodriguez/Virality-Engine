"""
Idea Inc - Core Data Models

These models are shared across all microservices to ensure consistency.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    PLAYER = "player"
    GUEST = "guest"


class AuthProvider(str, Enum):
    """Supported authentication providers"""
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    LOCAL = "local"
    PASSKEY = "passkey"


class WorldStatus(str, Enum):
    """Simulation world status"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NetworkType(str, Enum):
    """Agent network topology types"""
    SCALE_FREE = "scale_free"      # Power-law distribution (hubs)
    SMALL_WORLD = "small_world"    # High clustering, short paths
    RANDOM = "random"              # Erdős–Rényi random graph
    GEO_LOCAL = "geo_local"        # Geographic proximity based


class MutationType(str, Enum):
    """Types of idea mutations"""
    SIMPLIFY = "simplify"          # Make more accessible
    EMOTIONALIZE = "emotionalize"  # Increase emotional appeal
    LOCALIZE = "localize"          # Adapt for specific region
    POLARIZE = "polarize"          # Make more controversial
    MEMEIFY = "memeify"            # Convert to meme format
    RANDOM = "random"              # Random variation


class EventType(str, Enum):
    """Kafka event types"""
    # Idea events
    IDEA_INJECTED = "idea_injected"
    IDEA_SPREAD = "idea_spread"
    IDEA_MUTATED = "idea_mutated"
    IDEA_DECAYED = "idea_decayed"
    
    # Agent events
    AGENT_CREATED = "agent_created"
    AGENT_ADOPTED = "agent_adopted"
    AGENT_REJECTED = "agent_rejected"
    
    # World events
    WORLD_CREATED = "world_created"
    WORLD_STARTED = "world_started"
    WORLD_PAUSED = "world_paused"
    WORLD_COMPLETED = "world_completed"
    SNAPSHOT_READY = "snapshot_ready"
    
    # User events
    USER_CREATED = "user_created"
    USER_LOGGED_IN = "user_logged_in"
    USER_LOGGED_OUT = "user_logged_out"


# ============================================================================
# USER & AUTH MODELS
# ============================================================================

class UserBase(BaseModel):
    """Base user model"""
    email: str
    display_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation request"""
    provider: AuthProvider = AuthProvider.LOCAL
    provider_id: Optional[str] = None
    password: Optional[str] = None  # Only for local auth


class User(UserBase):
    """Full user model"""
    id: UUID = Field(default_factory=uuid4)
    provider: AuthProvider
    provider_id: Optional[str] = None
    roles: List[UserRole] = [UserRole.PLAYER]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    email: str
    roles: List[str]
    exp: datetime
    iat: datetime
    jti: str  # unique token id


class TokenResponse(BaseModel):
    """Token response to client"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# ============================================================================
# WORLD & SIMULATION MODELS
# ============================================================================

class WorldConfig(BaseModel):
    """World configuration parameters"""
    population_size: int = Field(default=10000, ge=100, le=1000000)
    network_type: NetworkType = NetworkType.SCALE_FREE
    network_density: float = Field(default=0.1, ge=0.01, le=1.0)
    mutation_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    decay_rate: float = Field(default=0.001, ge=0.0, le=1.0)
    time_step_ms: int = Field(default=100, ge=10, le=10000)
    max_steps: Optional[int] = None  # None = infinite


class WorldCreate(BaseModel):
    """World creation request"""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    config: WorldConfig = Field(default_factory=WorldConfig)
    is_public: bool = True


class World(BaseModel):
    """Full world model"""
    id: UUID = Field(default_factory=uuid4)
    creator_id: UUID
    name: str
    description: Optional[str] = None
    config: WorldConfig
    status: WorldStatus = WorldStatus.CREATED
    current_step: int = 0
    agent_count: int = 0
    idea_count: int = 0
    is_public: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# AGENT MODELS
# ============================================================================

class AgentProfile(BaseModel):
    """Agent demographic and personality profile"""
    age_group: str = Field(default="25-34")  # e.g., "18-24", "25-34"
    interests: List[str] = Field(default_factory=list)
    region: str = Field(default="NA")  # Geographic region
    trust_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    openness: float = Field(default=0.5, ge=0.0, le=1.0)
    influence: float = Field(default=0.1, ge=0.0, le=1.0)


class AgentState(BaseModel):
    """Agent current state"""
    mood: float = Field(default=0.0, ge=-1.0, le=1.0)
    susceptibility: float = Field(default=0.5, ge=0.0, le=1.0)
    last_active_step: int = 0


class Agent(BaseModel):
    """Full agent model"""
    id: UUID = Field(default_factory=uuid4)
    world_id: UUID
    profile: AgentProfile = Field(default_factory=AgentProfile)
    connections: List[UUID] = Field(default_factory=list)
    beliefs: List[UUID] = Field(default_factory=list)  # Adopted idea IDs
    state: AgentState = Field(default_factory=AgentState)
    memory_refs: List[str] = Field(default_factory=list)  # Vector DB refs
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# IDEA MODELS
# ============================================================================

class IdeaTarget(BaseModel):
    """Target demographics for an idea"""
    age_groups: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)


class IdeaCreate(BaseModel):
    """Idea creation/injection request"""
    text: str = Field(min_length=1, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    target: IdeaTarget = Field(default_factory=IdeaTarget)
    media_refs: List[str] = Field(default_factory=list)
    mutation_budget: int = Field(default=3, ge=0, le=100)


class Idea(BaseModel):
    """Full idea model"""
    id: UUID = Field(default_factory=uuid4)
    creator_id: UUID
    world_id: UUID
    text: str
    tags: List[str] = Field(default_factory=list)
    target: IdeaTarget = Field(default_factory=IdeaTarget)
    media_refs: List[str] = Field(default_factory=list)
    
    # Computed attributes
    virality_score: float = Field(default=0.2, ge=0.0, le=1.0)
    emotional_valence: float = Field(default=0.5, ge=0.0, le=1.0)
    complexity: float = Field(default=0.3, ge=0.0, le=1.0)
    
    # Mutation tracking
    parent_id: Optional[UUID] = None
    mutation_type: Optional[MutationType] = None
    mutation_count: int = 0
    mutation_budget: int = 3
    
    # Vector DB reference
    embedding_id: Optional[str] = None
    
    # Stats
    adopter_count: int = 0
    reach: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# EVENT MODELS
# ============================================================================

class BaseEvent(BaseModel):
    """Base event model for Kafka"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class IdeaInjectedEvent(BaseEvent):
    """Event: idea injected into world"""
    event_type: EventType = EventType.IDEA_INJECTED
    idea_id: UUID
    world_id: UUID
    user_id: UUID


class IdeaSpreadEvent(BaseEvent):
    """Event: idea spread from one agent to another"""
    event_type: EventType = EventType.IDEA_SPREAD
    idea_id: UUID
    world_id: UUID
    from_agent_id: UUID
    to_agent_id: UUID
    probability: float
    accepted: bool


class IdeaMutatedEvent(BaseEvent):
    """Event: idea mutated into new variant"""
    event_type: EventType = EventType.IDEA_MUTATED
    parent_idea_id: UUID
    new_idea_id: UUID
    world_id: UUID
    mutation_type: MutationType
    virality_change: float


class SnapshotReadyEvent(BaseEvent):
    """Event: world snapshot is ready"""
    event_type: EventType = EventType.SNAPSHOT_READY
    world_id: UUID
    step: int
    snapshot_url: Optional[str] = None


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class WorldSnapshot(BaseModel):
    """Point-in-time snapshot of world state"""
    world_id: UUID
    step: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_agents: int
    active_agents: int
    total_ideas: int
    total_adoptions: int
    
    # Per-idea stats
    ideas: List[Dict] = Field(default_factory=list)
    # [{"idea_id": uuid, "adopters": int, "reach": int, "mutations": int}]
    
    # Regional breakdown
    regional_stats: Dict[str, Dict] = Field(default_factory=dict)
    # {"NA": {"adopters": 100, "ideas": 5}, ...}


class IdeaMetrics(BaseModel):
    """Metrics for a single idea"""
    idea_id: UUID
    world_id: UUID
    
    # Core metrics
    r0: float = 0.0  # Basic reproduction number
    reach: int = 0
    adoption_rate: float = 0.0
    saturation: float = 0.0
    
    # Time series (last N steps)
    adoption_curve: List[int] = Field(default_factory=list)
    
    # Mutation metrics
    mutation_count: int = 0
    mutation_advantage: float = 0.0  # Virality gain from mutations


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    idea_id: UUID
    idea_text: str
    creator_id: UUID
    creator_name: str
    reach: int
    adoption_rate: float
    r0: float


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List
    total: int
    page: int
    page_size: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

