"""
Idea Inc - AI Service API Routes

REST API endpoints for AI/LLM operations.
"""

import sys
from pathlib import Path
from typing import Annotated, List
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException, Request, status

from shared.utils.logging import get_logger

from app.api.schemas import (
    AddIdeaRequest,
    AnalyzeIdeaRequest,
    AnalyzeIdeaResponse,
    BatchMutateRequest,
    BatchMutateResponse,
    ErrorResponse,
    GenerateIdeaRequest,
    GenerateIdeaResponse,
    MessageResponse,
    MutateIdeaRequest,
    MutateIdeaResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.llm.client import LLMClient
from app.llm.prompts import MutationType
from app.vector.store import VectorStore

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Dependencies
# =============================================================================

def get_llm_client(request: Request) -> LLMClient:
    """Get LLM client from app state"""
    return request.app.state.llm_client


def get_vector_store(request: Request) -> VectorStore:
    """Get vector store from app state"""
    return request.app.state.vector_store


# =============================================================================
# Mutation Routes
# =============================================================================

@router.post(
    "/mutate",
    response_model=MutateIdeaResponse,
    tags=["mutation"],
)
async def mutate_idea(
    data: MutateIdeaRequest,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    """
    Mutate an idea using LLM or fallback.
    
    Applies the specified mutation type to transform the idea
    for different viral characteristics.
    """
    try:
        mutation_type = MutationType(data.mutation_type)
    except ValueError:
        mutation_type = MutationType.RANDOM
    
    result = await llm.mutate_idea(
        idea_text=data.idea_text,
        mutation_type=mutation_type,
        region=data.target_region,
    )
    
    return MutateIdeaResponse(
        original_text=data.idea_text,
        mutated_text=result["text"],
        mutation_type=result["mutation_type"],
        source=result["source"],
        virality_change=result.get("virality_change"),
        emotional_change=result.get("emotional_change"),
        model=result.get("model"),
    )


@router.post(
    "/mutate/batch",
    response_model=BatchMutateResponse,
    tags=["mutation"],
)
async def batch_mutate_ideas(
    data: BatchMutateRequest,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    """
    Mutate multiple ideas in batch.
    
    Processes each idea with its specified mutation type.
    """
    results = []
    successful = 0
    
    for idea_request in data.ideas:
        try:
            mutation_type = MutationType(idea_request.mutation_type)
        except ValueError:
            mutation_type = MutationType.RANDOM
        
        try:
            result = await llm.mutate_idea(
                idea_text=idea_request.idea_text,
                mutation_type=mutation_type,
                region=idea_request.target_region,
            )
            
            results.append(MutateIdeaResponse(
                original_text=idea_request.idea_text,
                mutated_text=result["text"],
                mutation_type=result["mutation_type"],
                source=result["source"],
                virality_change=result.get("virality_change"),
                emotional_change=result.get("emotional_change"),
                model=result.get("model"),
            ))
            successful += 1
            
        except Exception as e:
            logger.error("Batch mutation failed for idea", error=str(e))
            results.append(MutateIdeaResponse(
                original_text=idea_request.idea_text,
                mutated_text=idea_request.idea_text,  # Return original on error
                mutation_type="error",
                source="error",
            ))
    
    return BatchMutateResponse(
        results=results,
        total=len(data.ideas),
        successful=successful,
    )


# =============================================================================
# Generation Routes
# =============================================================================

@router.post(
    "/generate",
    response_model=GenerateIdeaResponse,
    tags=["generation"],
)
async def generate_idea(
    data: GenerateIdeaRequest,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    """
    Generate a new idea based on parameters.
    
    Creates an original idea targeting the specified topic,
    audience, and virality level.
    """
    result = await llm.generate_idea(
        topic=data.topic,
        audience=data.audience,
        tone=data.tone,
        virality=data.virality,
    )
    
    return GenerateIdeaResponse(
        text=result["text"],
        topic=result["topic"],
        audience=result["audience"],
        source=result["source"],
        model=result.get("model"),
    )


# =============================================================================
# Analysis Routes
# =============================================================================

@router.post(
    "/analyze",
    response_model=AnalyzeIdeaResponse,
    tags=["analysis"],
)
async def analyze_idea(
    data: AnalyzeIdeaRequest,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    """
    Analyze an idea for viral potential.
    
    Returns scores for virality, emotional valence, complexity,
    controversy, and shareability.
    """
    result = await llm.analyze_idea(data.idea_text)
    
    return AnalyzeIdeaResponse(
        idea_text=data.idea_text,
        virality_score=result.get("virality_score", 0.5),
        emotional_valence=result.get("emotional_valence", 0.5),
        complexity=result.get("complexity", 0.5),
        controversy_level=result.get("controversy_level", 0.2),
        shareability=result.get("shareability", 0.5),
        target_demographics=result.get("target_demographics", ["general"]),
        source=result.get("source", "unknown"),
    )


# =============================================================================
# Vector Store Routes
# =============================================================================

@router.post(
    "/vectors/add",
    response_model=MessageResponse,
    tags=["vectors"],
)
async def add_idea_to_vectors(
    data: AddIdeaRequest,
    store: Annotated[VectorStore, Depends(get_vector_store)],
):
    """
    Add an idea to the vector store.
    
    Stores the idea embedding for semantic search and RAG.
    """
    embedding_id = await store.add_idea(
        idea_id=data.idea_id,
        text=data.text,
        metadata=data.metadata,
    )
    
    return MessageResponse(
        message=f"Idea added with embedding ID: {embedding_id}",
        success=True,
    )


@router.post(
    "/vectors/search",
    response_model=SearchResponse,
    tags=["vectors"],
)
async def search_similar_ideas(
    data: SearchRequest,
    store: Annotated[VectorStore, Depends(get_vector_store)],
):
    """
    Search for similar ideas using semantic search.
    
    Returns ideas ranked by similarity to the query.
    """
    results = await store.search_similar(
        query=data.query,
        n_results=data.n_results,
        filter_metadata=data.filter_metadata,
    )
    
    return SearchResponse(
        query=data.query,
        results=[SearchResult(**r) for r in results],
        total_results=len(results),
    )


@router.get(
    "/vectors/{idea_id}",
    tags=["vectors"],
    responses={404: {"model": ErrorResponse}},
)
async def get_idea_from_vectors(
    idea_id: UUID,
    store: Annotated[VectorStore, Depends(get_vector_store)],
):
    """
    Get an idea from the vector store by ID.
    """
    result = await store.get_idea(idea_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found in vector store",
        )
    
    return result


@router.delete(
    "/vectors/{idea_id}",
    response_model=MessageResponse,
    tags=["vectors"],
)
async def delete_idea_from_vectors(
    idea_id: UUID,
    store: Annotated[VectorStore, Depends(get_vector_store)],
):
    """
    Delete an idea from the vector store.
    """
    success = await store.delete_idea(idea_id)
    
    return MessageResponse(
        message="Idea deleted" if success else "Idea not found",
        success=success,
    )


@router.get(
    "/vectors/stats",
    tags=["vectors"],
)
async def get_vector_store_stats(
    store: Annotated[VectorStore, Depends(get_vector_store)],
):
    """
    Get vector store statistics.
    """
    return {
        "total_ideas": store.count,
        "enabled": store.enabled,
    }


# =============================================================================
# RAG Routes
# =============================================================================

@router.post(
    "/rag/context",
    tags=["rag"],
)
async def get_rag_context(
    data: AnalyzeIdeaRequest,
    store: Annotated[VectorStore, Depends(get_vector_store)],
):
    """
    Get RAG context for an idea.
    
    Retrieves similar ideas to provide context for LLM operations.
    """
    context = await store.get_context_for_idea(
        idea_text=data.idea_text,
        n_context=3,
    )
    
    return {
        "idea_text": data.idea_text,
        "context": context,
    }


# =============================================================================
# Utility Routes
# =============================================================================

@router.get(
    "/mutation-types",
    tags=["utility"],
)
async def list_mutation_types():
    """
    List available mutation types.
    """
    return {
        "mutation_types": [
            {
                "type": mt.value,
                "description": {
                    "simplify": "Make the idea simpler and more accessible",
                    "emotionalize": "Add emotional appeal and intensity",
                    "localize": "Adapt for a specific region",
                    "polarize": "Make more divisive and controversial",
                    "memeify": "Convert to meme format",
                    "random": "Apply a random variation",
                }.get(mt.value, "Unknown"),
            }
            for mt in MutationType
        ]
    }

