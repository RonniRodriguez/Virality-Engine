"""
Idea Inc - AI Service API Schemas

Pydantic models for request/response validation.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Mutation Schemas
# =============================================================================

class MutateIdeaRequest(BaseModel):
    """Idea mutation request"""
    idea_text: str = Field(min_length=1, max_length=1000)
    mutation_type: str = Field(
        default="random",
        description="Type: simplify, emotionalize, localize, polarize, memeify, random"
    )
    target_region: Optional[str] = Field(
        default=None,
        description="Target region for localization"
    )


class MutateIdeaResponse(BaseModel):
    """Idea mutation response"""
    original_text: str
    mutated_text: str
    mutation_type: str
    source: str  # llm or fallback
    virality_change: Optional[float] = None
    emotional_change: Optional[float] = None
    model: Optional[str] = None


# =============================================================================
# Generation Schemas
# =============================================================================

class GenerateIdeaRequest(BaseModel):
    """Idea generation request"""
    topic: str = Field(min_length=1, max_length=200)
    audience: str = Field(default="general", max_length=100)
    tone: str = Field(default="neutral", max_length=50)
    virality: str = Field(
        default="medium",
        description="Virality goal: low, medium, high"
    )


class GenerateIdeaResponse(BaseModel):
    """Idea generation response"""
    text: str
    topic: str
    audience: str
    source: str
    model: Optional[str] = None


# =============================================================================
# Analysis Schemas
# =============================================================================

class AnalyzeIdeaRequest(BaseModel):
    """Idea analysis request"""
    idea_text: str = Field(min_length=1, max_length=1000)


class AnalyzeIdeaResponse(BaseModel):
    """Idea analysis response"""
    idea_text: str
    virality_score: float
    emotional_valence: float
    complexity: float
    controversy_level: float
    shareability: float
    target_demographics: List[str]
    source: str


# =============================================================================
# Vector Store Schemas
# =============================================================================

class AddIdeaRequest(BaseModel):
    """Add idea to vector store request"""
    idea_id: UUID
    text: str = Field(min_length=1, max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Vector search request"""
    query: str = Field(min_length=1, max_length=500)
    n_results: int = Field(default=5, ge=1, le=20)
    filter_metadata: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Single search result"""
    idea_id: str
    text: str
    metadata: Dict[str, Any]
    distance: float


class SearchResponse(BaseModel):
    """Vector search response"""
    query: str
    results: List[SearchResult]
    total_results: int


# =============================================================================
# Batch Schemas
# =============================================================================

class BatchMutateRequest(BaseModel):
    """Batch mutation request"""
    ideas: List[MutateIdeaRequest]


class BatchMutateResponse(BaseModel):
    """Batch mutation response"""
    results: List[MutateIdeaResponse]
    total: int
    successful: int


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

