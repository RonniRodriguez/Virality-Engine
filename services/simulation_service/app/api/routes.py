"""
Idea Inc - Simulation Service API Routes

REST API endpoints for simulation management.
"""

import sys
from pathlib import Path
from typing import Annotated, List, Optional
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from shared.utils.logging import get_logger

from app.api.schemas import (
    ErrorResponse,
    IdeaCreate,
    IdeaResponse,
    MessageResponse,
    SnapshotResponse,
    StepRequest,
    StepResponse,
    StepResult,
    WorldCreate,
    WorldListItem,
    WorldResponse,
)
from app.engine.manager import SimulationManager
from app.engine.world import WorldConfig, NetworkType
from app.engine.idea import IdeaTarget

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Dependencies
# =============================================================================

def get_manager(request: Request) -> SimulationManager:
    """Get simulation manager from app state"""
    return request.app.state.simulation_manager


# =============================================================================
# World Routes
# =============================================================================

@router.post(
    "/worlds",
    response_model=WorldResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["worlds"],
)
async def create_world(
    data: WorldCreate,
    manager: Annotated[SimulationManager, Depends(get_manager)],
    creator_id: UUID = Query(default=None, description="Creator user ID (temporary, will use JWT)"),
):
    """
    Create a new simulation world.
    
    Creates a world with the specified configuration and initializes
    the agent population with network connections.
    """
    # Use a default creator ID for now (will be replaced with JWT auth)
    if not creator_id:
        creator_id = UUID("00000000-0000-0000-0000-000000000001")
    
    try:
        # Convert network type string to enum
        network_type = NetworkType(data.config.network_type)
    except ValueError:
        network_type = NetworkType.SCALE_FREE
    
    config = WorldConfig(
        population_size=data.config.population_size,
        network_type=network_type,
        network_density=data.config.network_density,
        mutation_rate=data.config.mutation_rate,
        decay_rate=data.config.decay_rate,
        time_step_ms=data.config.time_step_ms,
        max_steps=data.config.max_steps,
    )
    
    try:
        world = await manager.create_world(
            creator_id=creator_id,
            name=data.name,
            description=data.description,
            config=config,
            is_public=data.is_public,
        )
        
        return WorldResponse(**world.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/worlds",
    response_model=List[WorldListItem],
    tags=["worlds"],
)
async def list_worlds(
    manager: Annotated[SimulationManager, Depends(get_manager)],
    creator_id: Optional[UUID] = None,
    public_only: bool = False,
):
    """
    List all worlds.
    
    Can filter by creator or show only public worlds.
    """
    worlds = await manager.list_worlds(
        creator_id=creator_id,
        public_only=public_only,
    )
    return worlds


@router.get(
    "/worlds/{world_id}",
    response_model=WorldResponse,
    tags=["worlds"],
    responses={404: {"model": ErrorResponse}},
)
async def get_world(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """Get a world by ID"""
    world = await manager.get_world(world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    return WorldResponse(**world.to_dict())


@router.delete(
    "/worlds/{world_id}",
    response_model=MessageResponse,
    tags=["worlds"],
    responses={404: {"model": ErrorResponse}},
)
async def delete_world(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """Delete a world"""
    success = await manager.delete_world(world_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    return MessageResponse(message="World deleted")


# =============================================================================
# Simulation Control Routes
# =============================================================================

@router.post(
    "/worlds/{world_id}/start",
    response_model=WorldResponse,
    tags=["simulation"],
    responses={404: {"model": ErrorResponse}},
)
async def start_world(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """
    Start a world's simulation.
    
    The simulation will run in the background until stopped or completed.
    """
    success = await manager.start_world(world_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    world = await manager.get_world(world_id)
    return WorldResponse(**world.to_dict())


@router.post(
    "/worlds/{world_id}/stop",
    response_model=WorldResponse,
    tags=["simulation"],
    responses={404: {"model": ErrorResponse}},
)
async def stop_world(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """Stop a world's simulation"""
    success = await manager.stop_world(world_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    world = await manager.get_world(world_id)
    return WorldResponse(**world.to_dict())


@router.post(
    "/worlds/{world_id}/step",
    response_model=StepResponse,
    tags=["simulation"],
    responses={404: {"model": ErrorResponse}},
)
async def step_world(
    world_id: UUID,
    data: StepRequest,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """
    Manually step a world's simulation.
    
    Runs the specified number of simulation steps and returns results.
    Useful for debugging or step-by-step analysis.
    """
    world = await manager.get_world(world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    results = await manager.step_world(world_id, steps=data.steps)
    
    return StepResponse(
        world_id=world_id,
        results=[StepResult(**r) for r in results if "error" not in r],
        final_step=world.current_step,
    )


@router.get(
    "/worlds/{world_id}/snapshot",
    response_model=SnapshotResponse,
    tags=["simulation"],
    responses={404: {"model": ErrorResponse}},
)
async def get_snapshot(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """
    Get current snapshot of a world.
    
    Returns the current state including agent counts, idea statistics,
    and regional breakdowns.
    """
    snapshot = await manager.get_snapshot(world_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    return SnapshotResponse(**snapshot.to_dict())


# =============================================================================
# Idea Routes
# =============================================================================

@router.post(
    "/worlds/{world_id}/ideas",
    response_model=IdeaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["ideas"],
    responses={404: {"model": ErrorResponse}},
)
async def inject_idea(
    world_id: UUID,
    data: IdeaCreate,
    manager: Annotated[SimulationManager, Depends(get_manager)],
    creator_id: UUID = Query(default=None, description="Creator user ID (temporary)"),
):
    """
    Inject an idea into a world.
    
    The idea will be seeded to a number of initial adopters who will
    then spread it through the network.
    """
    if not creator_id:
        creator_id = UUID("00000000-0000-0000-0000-000000000001")
    
    world = await manager.get_world(world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    target = IdeaTarget(
        age_groups=data.target.age_groups,
        interests=data.target.interests,
        regions=data.target.regions,
    )
    
    idea = await manager.inject_idea(
        world_id=world_id,
        creator_id=creator_id,
        text=data.text,
        tags=data.tags,
        target=target,
        virality_score=data.virality_score,
        emotional_valence=data.emotional_valence,
        initial_adopters=data.initial_adopters,
    )
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to inject idea",
        )
    
    return IdeaResponse(**idea.to_dict())


@router.get(
    "/worlds/{world_id}/ideas",
    response_model=List[IdeaResponse],
    tags=["ideas"],
    responses={404: {"model": ErrorResponse}},
)
async def list_ideas(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
    limit: int = Query(default=50, ge=1, le=100),
    sort_by: str = Query(default="adopters", regex="^(adopters|reach|created_at)$"),
):
    """
    List ideas in a world.
    
    Returns ideas sorted by the specified field.
    """
    world = await manager.get_world(world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    ideas = list(world.ideas.values())
    
    # Sort
    if sort_by == "adopters":
        ideas.sort(key=lambda x: x.adopter_count, reverse=True)
    elif sort_by == "reach":
        ideas.sort(key=lambda x: x.reach, reverse=True)
    else:
        ideas.sort(key=lambda x: x.created_at, reverse=True)
    
    # Limit
    ideas = ideas[:limit]
    
    return [IdeaResponse(**idea.to_dict()) for idea in ideas]


@router.get(
    "/worlds/{world_id}/ideas/{idea_id}",
    response_model=IdeaResponse,
    tags=["ideas"],
    responses={404: {"model": ErrorResponse}},
)
async def get_idea(
    world_id: UUID,
    idea_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """Get a specific idea from a world"""
    idea = await manager.get_idea(world_id, idea_id)
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )
    
    return IdeaResponse(**idea.to_dict())


# =============================================================================
# Analytics Routes (Basic)
# =============================================================================

@router.get(
    "/worlds/{world_id}/leaderboard",
    tags=["analytics"],
    responses={404: {"model": ErrorResponse}},
)
async def get_leaderboard(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get idea leaderboard for a world.
    
    Returns top ideas by adoption count.
    """
    world = await manager.get_world(world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    ideas = sorted(
        world.ideas.values(),
        key=lambda x: x.adopter_count,
        reverse=True,
    )[:limit]
    
    leaderboard = []
    for rank, idea in enumerate(ideas, 1):
        leaderboard.append({
            "rank": rank,
            "idea_id": str(idea.id),
            "text": idea.text[:100],
            "creator_id": str(idea.creator_id),
            "adopters": idea.adopter_count,
            "reach": idea.reach,
            "adoption_rate": idea.adoption_rate,
            "generation": idea.generation,
        })
    
    return {
        "world_id": str(world_id),
        "step": world.current_step,
        "leaderboard": leaderboard,
    }


@router.get(
    "/worlds/{world_id}/stats",
    tags=["analytics"],
    responses={404: {"model": ErrorResponse}},
)
async def get_world_stats(
    world_id: UUID,
    manager: Annotated[SimulationManager, Depends(get_manager)],
):
    """
    Get aggregate statistics for a world.
    """
    world = await manager.get_world(world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    
    # Calculate R0 (basic reproduction number)
    # Average secondary adoptions per idea
    total_adoptions = sum(idea.adopter_count for idea in world.ideas.values())
    total_ideas = len(world.ideas)
    avg_r0 = total_adoptions / total_ideas if total_ideas > 0 else 0
    
    # Saturation
    active_agents = sum(1 for a in world.agents.values() if a.beliefs)
    saturation = active_agents / len(world.agents) if world.agents else 0
    
    return {
        "world_id": str(world_id),
        "step": world.current_step,
        "status": world.status.value,
        "total_agents": len(world.agents),
        "active_agents": active_agents,
        "saturation": round(saturation, 4),
        "total_ideas": total_ideas,
        "total_adoptions": total_adoptions,
        "total_mutations": world.total_mutations,
        "total_spread_events": world.total_spread_events,
        "average_r0": round(avg_r0, 2),
    }

