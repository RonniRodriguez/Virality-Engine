"""
Idea Inc - Simulation Engine Tests

Unit tests for the core simulation engine.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.simulation_service.app.engine.agent import Agent, AgentProfile, AgentState
from services.simulation_service.app.engine.idea import Idea, IdeaTarget, MutationType
from services.simulation_service.app.engine.world import World, WorldConfig, NetworkType, WorldStatus


class TestAgent:
    """Tests for Agent class"""
    
    def test_agent_creation(self):
        """Test basic agent creation"""
        agent = Agent(world_id=uuid4())
        
        assert agent.id is not None
        assert agent.world_id is not None
        assert len(agent.beliefs) == 0
        assert len(agent.connections) == 0
    
    def test_agent_random_profile(self):
        """Test random profile generation"""
        profile = AgentProfile.random(region="EU")
        
        assert profile.region == "EU"
        assert 0 <= profile.trust_threshold <= 1
        assert 0 <= profile.openness <= 1
        assert 0 <= profile.influence <= 1
        assert len(profile.interests) >= 2
    
    def test_agent_adopt_idea(self):
        """Test idea adoption"""
        agent = Agent(world_id=uuid4())
        idea_id = uuid4()
        
        # First adoption should succeed
        assert agent.adopt_idea(idea_id) is True
        assert idea_id in agent.beliefs
        
        # Second adoption should fail (already has it)
        assert agent.adopt_idea(idea_id) is False
    
    def test_agent_forget_idea(self):
        """Test idea forgetting"""
        agent = Agent(world_id=uuid4())
        idea_id = uuid4()
        
        agent.adopt_idea(idea_id)
        assert agent.forget_idea(idea_id) is True
        assert idea_id not in agent.beliefs
        
        # Forgetting non-existent idea should fail
        assert agent.forget_idea(idea_id) is False
    
    def test_agent_connections(self):
        """Test connection management"""
        agent = Agent(world_id=uuid4())
        other_id = uuid4()
        
        agent.add_connection(other_id)
        assert other_id in agent.connections
        
        agent.remove_connection(other_id)
        assert other_id not in agent.connections
    
    def test_agent_self_connection_prevented(self):
        """Test that agents can't connect to themselves"""
        agent = Agent(world_id=uuid4())
        agent.add_connection(agent.id)
        assert agent.id not in agent.connections
    
    def test_adoption_probability_calculation(self):
        """Test adoption probability calculation"""
        agent = Agent(world_id=uuid4())
        agent.profile.openness = 0.8
        agent.state.susceptibility = 0.5
        
        prob = agent.calculate_adoption_probability(
            idea_virality=0.5,
            idea_relevance=0.7,
            sender_influence=0.3,
            trust_factor=1.0,
        )
        
        assert 0 <= prob <= 1
    
    def test_idea_relevance_calculation(self):
        """Test idea relevance calculation"""
        agent = Agent(world_id=uuid4())
        agent.profile.interests = ["tech", "music", "gaming"]
        
        # High overlap
        relevance = agent.calculate_idea_relevance(["tech", "gaming"])
        assert relevance > 0.5
        
        # No overlap
        relevance = agent.calculate_idea_relevance(["sports", "politics"])
        assert relevance < 0.3
        
        # Empty tags
        relevance = agent.calculate_idea_relevance([])
        assert relevance == 0.3


class TestIdea:
    """Tests for Idea class"""
    
    def test_idea_creation(self):
        """Test basic idea creation"""
        idea = Idea(
            creator_id=uuid4(),
            world_id=uuid4(),
            text="Test idea",
        )
        
        assert idea.id is not None
        assert idea.text == "Test idea"
        assert idea.virality_score == 0.2
        assert idea.adopter_count == 0
    
    def test_idea_mutation(self):
        """Test idea mutation"""
        idea = Idea(
            creator_id=uuid4(),
            world_id=uuid4(),
            text="Original idea",
            mutation_budget=3,
        )
        
        mutant = idea.create_mutation(
            mutation_type=MutationType.SIMPLIFY,
            new_text="Simplified idea",
            virality_change=0.05,
        )
        
        assert mutant.parent_id == idea.id
        assert mutant.generation == 1
        assert mutant.mutation_type == MutationType.SIMPLIFY
        assert idea.mutation_count == 1
    
    def test_mutation_budget_enforcement(self):
        """Test mutation budget is enforced"""
        idea = Idea(
            creator_id=uuid4(),
            world_id=uuid4(),
            text="Original",
            mutation_budget=1,
        )
        
        # First mutation should succeed
        idea.create_mutation(MutationType.RANDOM, "Variant 1")
        
        # Second should fail
        with pytest.raises(ValueError):
            idea.create_mutation(MutationType.RANDOM, "Variant 2")
    
    def test_idea_stats_tracking(self):
        """Test idea statistics tracking"""
        idea = Idea(creator_id=uuid4(), world_id=uuid4(), text="Test")
        
        idea.record_exposure()
        idea.record_exposure()
        idea.record_adoption()
        
        assert idea.reach == 2
        assert idea.adopter_count == 1
        assert idea.adoption_rate == 0.5
    
    def test_idea_target_matching(self):
        """Test idea target matching"""
        target = IdeaTarget(
            age_groups=["18-24"],
            interests=["tech"],
            regions=["NA"],
        )
        
        # Perfect match
        score = target.matches_agent("18-24", ["tech", "music"], "NA")
        assert score > 0.8
        
        # No match
        score = target.matches_agent("65+", ["sports"], "EU")
        assert score < 0.3


class TestWorld:
    """Tests for World class"""
    
    def test_world_creation(self):
        """Test basic world creation"""
        config = WorldConfig(population_size=100)
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=config,
        )
        
        assert world.status == WorldStatus.CREATED
        assert world.current_step == 0
        assert world.agent_count == 0
    
    def test_world_population_initialization(self):
        """Test population initialization"""
        config = WorldConfig(
            population_size=100,
            network_type=NetworkType.RANDOM,
            network_density=0.1,
        )
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=config,
        )
        
        world.initialize_population()
        
        assert world.agent_count == 100
        # Check that agents have connections
        total_connections = sum(len(a.connections) for a in world.agents.values())
        assert total_connections > 0
    
    def test_idea_injection(self):
        """Test idea injection into world"""
        config = WorldConfig(population_size=100)
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=config,
        )
        world.initialize_population()
        
        idea = Idea(
            creator_id=uuid4(),
            world_id=world.id,
            text="Test idea",
        )
        
        adopter_ids = world.inject_idea(idea, initial_adopters=5)
        
        assert len(adopter_ids) == 5
        assert idea.id in world.ideas
        assert idea.adopter_count == 5
    
    @pytest.mark.asyncio
    async def test_simulation_step(self):
        """Test running a simulation step"""
        config = WorldConfig(
            population_size=50,
            network_density=0.2,
        )
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=config,
        )
        world.initialize_population()
        world.start()
        
        # Inject an idea
        idea = Idea(
            creator_id=uuid4(),
            world_id=world.id,
            text="Viral idea",
            virality_score=0.5,
        )
        world.inject_idea(idea, initial_adopters=3)
        
        # Run a step
        result = await world.run_step()
        
        assert "step" in result
        assert "adoptions" in result
        assert world.current_step == 1
    
    def test_world_snapshot(self):
        """Test snapshot generation"""
        config = WorldConfig(population_size=50)
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=config,
        )
        world.initialize_population()
        
        snapshot = world.get_snapshot()
        
        assert snapshot.world_id == world.id
        assert snapshot.total_agents == 50
        assert "NA" in snapshot.regional_stats
    
    def test_world_status_transitions(self):
        """Test world status transitions"""
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=WorldConfig(),
        )
        
        assert world.status == WorldStatus.CREATED
        
        world.start()
        assert world.status == WorldStatus.RUNNING
        
        world.pause()
        assert world.status == WorldStatus.PAUSED
        
        world.resume()
        assert world.status == WorldStatus.RUNNING


class TestNetworkTopologies:
    """Tests for different network topologies"""
    
    @pytest.mark.parametrize("network_type", [
        NetworkType.SCALE_FREE,
        NetworkType.SMALL_WORLD,
        NetworkType.RANDOM,
    ])
    def test_network_creation(self, network_type):
        """Test that different network types create valid networks"""
        config = WorldConfig(
            population_size=100,
            network_type=network_type,
            network_density=0.1,
        )
        world = World(
            id=uuid4(),
            creator_id=uuid4(),
            name="Test World",
            config=config,
        )
        world.initialize_population()
        
        # All agents should exist
        assert world.agent_count == 100
        
        # Network should have edges
        assert world.network.number_of_edges() > 0
        
        # Agents should have connections
        agents_with_connections = sum(
            1 for a in world.agents.values() if a.connections
        )
        assert agents_with_connections > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

