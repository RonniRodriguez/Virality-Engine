"""
Idea Inc - Simulation Manager

Manages multiple simulation worlds and their lifecycle.
Handles concurrent world execution with structured concurrency.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.utils.logging import get_logger

from .world import World, WorldConfig, WorldStatus, NetworkType, WorldSnapshot
from .idea import Idea, IdeaTarget

logger = get_logger(__name__)


class SimulationManager:
    """
    Manages multiple simulation worlds.
    
    Responsibilities:
    - Create and destroy worlds
    - Run simulation loops for active worlds
    - Provide access to world state and snapshots
    - Handle concurrent execution
    """
    
    def __init__(self, max_concurrent_worlds: int = 10):
        self.max_concurrent_worlds = max_concurrent_worlds
        self.worlds: Dict[UUID, World] = {}
        self.world_tasks: Dict[UUID, asyncio.Task] = {}
        self._running = False
        self._lock = asyncio.Lock()
    
    @property
    def active_world_count(self) -> int:
        """Count of currently running worlds"""
        return sum(
            1 for w in self.worlds.values()
            if w.status == WorldStatus.RUNNING
        )
    
    async def start(self) -> None:
        """Start the simulation manager"""
        self._running = True
        logger.info("Simulation manager started")
    
    async def stop(self) -> None:
        """Stop the simulation manager and all worlds"""
        self._running = False
        
        # Cancel all running tasks
        for world_id, task in list(self.world_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.world_tasks.clear()
        logger.info("Simulation manager stopped")
    
    async def create_world(
        self,
        creator_id: UUID,
        name: str,
        description: str = "",
        config: Optional[WorldConfig] = None,
        is_public: bool = True,
    ) -> World:
        """
        Create a new simulation world.
        
        Args:
            creator_id: User ID of the creator
            name: World name
            description: World description
            config: World configuration (uses defaults if None)
            is_public: Whether the world is publicly visible
        
        Returns:
            The created World instance
        """
        async with self._lock:
            if len(self.worlds) >= self.max_concurrent_worlds:
                raise ValueError(
                    f"Maximum concurrent worlds ({self.max_concurrent_worlds}) reached"
                )
            
            world_id = uuid4()
            world_config = config or WorldConfig()
            
            world = World(
                id=world_id,
                creator_id=creator_id,
                name=name,
                description=description,
                config=world_config,
                is_public=is_public,
            )
            
            # Initialize population
            logger.info(
                "Initializing world population",
                world_id=str(world_id),
                population_size=world_config.population_size,
            )
            world.initialize_population()
            
            self.worlds[world_id] = world
            
            logger.info(
                "World created",
                world_id=str(world_id),
                name=name,
                agent_count=world.agent_count,
            )
            
            return world
    
    async def get_world(self, world_id: UUID) -> Optional[World]:
        """Get a world by ID"""
        return self.worlds.get(world_id)
    
    async def delete_world(self, world_id: UUID) -> bool:
        """Delete a world"""
        async with self._lock:
            if world_id not in self.worlds:
                return False
            
            # Stop if running
            await self.stop_world(world_id)
            
            del self.worlds[world_id]
            logger.info("World deleted", world_id=str(world_id))
            return True
    
    async def start_world(self, world_id: UUID) -> bool:
        """
        Start a world's simulation loop.
        
        Returns:
            True if started, False if world not found or already running
        """
        world = self.worlds.get(world_id)
        if not world:
            return False
        
        if world.status == WorldStatus.RUNNING:
            return True  # Already running
        
        world.start()
        
        # Create simulation task
        task = asyncio.create_task(self._run_world_loop(world_id))
        self.world_tasks[world_id] = task
        
        logger.info("World started", world_id=str(world_id))
        return True
    
    async def stop_world(self, world_id: UUID) -> bool:
        """
        Stop a world's simulation loop.
        
        Returns:
            True if stopped, False if world not found
        """
        world = self.worlds.get(world_id)
        if not world:
            return False
        
        world.pause()
        
        # Cancel task if exists
        task = self.world_tasks.pop(world_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("World stopped", world_id=str(world_id))
        return True
    
    async def step_world(self, world_id: UUID, steps: int = 1) -> List[Dict]:
        """
        Run specific number of steps on a world (manual stepping).
        
        Args:
            world_id: World to step
            steps: Number of steps to run
        
        Returns:
            List of step results
        """
        world = self.worlds.get(world_id)
        if not world:
            return [{"error": "World not found"}]
        
        # Temporarily set to running for steps
        original_status = world.status
        world.status = WorldStatus.RUNNING
        
        results = []
        for _ in range(steps):
            result = await world.run_step()
            results.append(result)
            
            # Small delay between steps
            await asyncio.sleep(0.001)
        
        # Restore status if was paused
        if original_status == WorldStatus.PAUSED:
            world.status = WorldStatus.PAUSED
        
        return results
    
    async def inject_idea(
        self,
        world_id: UUID,
        creator_id: UUID,
        text: str,
        tags: List[str] = None,
        target: Optional[IdeaTarget] = None,
        virality_score: float = 0.2,
        emotional_valence: float = 0.5,
        initial_adopters: int = 1,
    ) -> Optional[Idea]:
        """
        Inject an idea into a world.
        
        Args:
            world_id: Target world
            creator_id: User creating the idea
            text: Idea content
            tags: Tags for targeting
            target: Target demographics
            virality_score: Base virality (0-1)
            emotional_valence: Emotional intensity (0-1)
            initial_adopters: Number of seed adopters
        
        Returns:
            The created Idea, or None if world not found
        """
        world = self.worlds.get(world_id)
        if not world:
            return None
        
        idea = Idea(
            creator_id=creator_id,
            world_id=world_id,
            text=text,
            tags=tags or [],
            target=target or IdeaTarget(),
            virality_score=virality_score,
            emotional_valence=emotional_valence,
        )
        
        adopter_ids = world.inject_idea(idea, initial_adopters=initial_adopters)
        
        logger.info(
            "Idea injected",
            world_id=str(world_id),
            idea_id=str(idea.id),
            initial_adopters=len(adopter_ids),
        )
        
        return idea
    
    async def get_snapshot(self, world_id: UUID) -> Optional[WorldSnapshot]:
        """Get current snapshot of a world"""
        world = self.worlds.get(world_id)
        if not world:
            return None
        
        return world.get_snapshot()
    
    async def get_idea(self, world_id: UUID, idea_id: UUID) -> Optional[Idea]:
        """Get an idea from a world"""
        world = self.worlds.get(world_id)
        if not world:
            return None
        
        return world.ideas.get(idea_id)
    
    async def list_worlds(
        self,
        creator_id: Optional[UUID] = None,
        public_only: bool = False,
    ) -> List[Dict]:
        """
        List worlds with optional filters.
        
        Args:
            creator_id: Filter by creator
            public_only: Only show public worlds
        
        Returns:
            List of world summaries
        """
        worlds = []
        for world in self.worlds.values():
            if creator_id and world.creator_id != creator_id:
                continue
            if public_only and not world.is_public:
                continue
            
            worlds.append({
                "id": str(world.id),
                "name": world.name,
                "description": world.description,
                "status": world.status.value,
                "agent_count": world.agent_count,
                "idea_count": world.idea_count,
                "current_step": world.current_step,
                "is_public": world.is_public,
                "creator_id": str(world.creator_id),
                "created_at": world.created_at.isoformat(),
            })
        
        return worlds
    
    async def _run_world_loop(self, world_id: UUID) -> None:
        """
        Background task to run a world's simulation loop.
        
        Runs until the world is stopped or completes.
        """
        world = self.worlds.get(world_id)
        if not world:
            return
        
        logger.info("Starting world loop", world_id=str(world_id))
        
        try:
            while self._running and world.status == WorldStatus.RUNNING:
                # Run a step
                result = await world.run_step()
                
                # Log progress periodically
                if world.current_step % 100 == 0:
                    logger.debug(
                        "World step",
                        world_id=str(world_id),
                        step=world.current_step,
                        adoptions=result.get("adoptions", 0),
                    )
                
                # Wait for next tick
                await asyncio.sleep(world.config.time_step_ms / 1000.0)
                
        except asyncio.CancelledError:
            logger.info("World loop cancelled", world_id=str(world_id))
            raise
        except Exception as e:
            logger.error(
                "World loop error",
                world_id=str(world_id),
                error=str(e),
            )
            world.status = WorldStatus.PAUSED
        finally:
            # Clean up task reference
            self.world_tasks.pop(world_id, None)
            logger.info("World loop ended", world_id=str(world_id))

