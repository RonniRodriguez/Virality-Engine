"""
Idea Inc - Test Configuration

Pytest fixtures and configuration for testing.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from httpx import AsyncClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def user_id() -> str:
    """Generate a test user ID"""
    return str(uuid4())


@pytest.fixture
def world_id() -> str:
    """Generate a test world ID"""
    return str(uuid4())


@pytest.fixture
def idea_id() -> str:
    """Generate a test idea ID"""
    return str(uuid4())


# =============================================================================
# Auth Service Fixtures
# =============================================================================

@pytest.fixture
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async client for auth service"""
    from services.auth_service.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user_data() -> dict:
    """Test user registration data"""
    return {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
    }


# =============================================================================
# Simulation Service Fixtures
# =============================================================================

@pytest.fixture
async def simulation_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async client for simulation service"""
    from services.simulation_service.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_world_data() -> dict:
    """Test world creation data"""
    return {
        "name": f"Test World {uuid4().hex[:8]}",
        "description": "A test simulation world",
        "config": {
            "population_size": 1000,
            "network_type": "scale_free",
            "network_density": 0.1,
            "mutation_rate": 0.01,
            "decay_rate": 0.001,
        },
        "is_public": True,
    }


@pytest.fixture
def test_idea_data() -> dict:
    """Test idea creation data"""
    return {
        "text": "Test idea for simulation",
        "tags": ["test", "simulation"],
        "target": {
            "age_groups": ["18-24", "25-34"],
            "interests": ["tech"],
            "regions": ["NA"],
        },
        "virality_score": 0.3,
        "emotional_valence": 0.5,
        "initial_adopters": 5,
    }


# =============================================================================
# AI Service Fixtures
# =============================================================================

@pytest.fixture
async def ai_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async client for AI service"""
    from services.ai_service.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_mutation_data() -> dict:
    """Test mutation request data"""
    return {
        "idea_text": "The future of technology is here",
        "mutation_type": "emotionalize",
        "target_region": None,
    }


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def mock_event_bus():
    """Create a mock event bus for testing"""
    from shared.utils.events import InMemoryEventBus
    return InMemoryEventBus()


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing"""
    from shared.utils.cache import InMemoryCache, Cache
    backend = InMemoryCache()
    return Cache(backend, prefix="test")

