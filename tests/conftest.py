"""Shared pytest fixtures for all tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.concurrency import ConcurrencyManager
from src.config import AppConfig, LLMConfig
from src.file_manager import FileManager
from src.models import DevPlan, DevPlanPhase, DevPlanStep, ProjectDesign
from src.state_manager import StateManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return AppConfig(
        llm=LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key",
        ),
        max_concurrent_requests=2,
        streaming_enabled=False,
    )


@pytest.fixture
def mock_llm_client():
    """Mock LLM client with async methods."""
    client = AsyncMock()
    client.generate_completion = AsyncMock(return_value="Generated content")
    client.generate_multiple = AsyncMock(
        return_value=["Generated 1", "Generated 2", "Generated 3"]
    )
    return client


@pytest.fixture
def concurrency_manager():
    """Create a ConcurrencyManager for testing."""
    return ConcurrencyManager(max_concurrent=2)


@pytest.fixture
def file_manager():
    """Create a FileManager for testing."""
    return FileManager()


@pytest.fixture
def state_manager(temp_state_dir):
    """Create a StateManager with temporary directory."""
    return StateManager(temp_state_dir)


@pytest.fixture
def sample_project_design():
    """Sample project design for testing."""
    return ProjectDesign(
        project_name="test-project",
        objectives=["Build web application", "Create API"],
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        architecture_overview="Test architecture overview",
        dependencies=["requests", "pydantic", "uvicorn"],
        challenges=["Performance optimization", "Scalability"],
        mitigations=["Use caching", "Load balancing"],
    )


@pytest.fixture
def sample_devplan():
    """Sample development plan for testing."""
    phase = DevPlanPhase(
        number=1,
        title="Setup Phase",
        description="Initial project setup",
        steps=[
            DevPlanStep(
                number="1.1",
                description="Create project structure",
                done=False,
            ),
            DevPlanStep(
                number="1.2",
                description="Set up development environment",
                done=False,
            ),
        ],
    )
    return DevPlan(
        summary="Test development plan summary",
        phases=[phase],
    )


@pytest.fixture
def sample_detailed_devplan():
    """Sample detailed development plan with multiple phases."""
    phases = []
    for i in range(1, 4):
        steps = [
            DevPlanStep(
                number=f"{i}.{j}",
                description=f"Step {j} of phase {i}",
                done=False,
            )
            for j in range(1, 6)
        ]
        phase = DevPlanPhase(
            number=i,
            title=f"Phase {i}",
            description=f"Description for phase {i}",
            steps=steps,
        )
        phases.append(phase)

    return DevPlan(
        summary="Detailed development plan with multiple phases",
        phases=phases,
    )


@pytest.fixture
def mock_handoff_prompt():
    """Mock handoff prompt object."""
    handoff = MagicMock()
    handoff.content = "Test handoff prompt content"
    handoff.model_dump.return_value = {
        "content": "Test handoff prompt content",
        "project_summary": "Test project summary",
        "completed_phases": ["Phase 1", "Phase 2"],
        "next_steps": ["Step 1", "Step 2"],
    }
    return handoff


@pytest.fixture
def mock_project_inputs():
    """Sample project inputs for pipeline testing."""
    return {
        "project_name": "test-project",
        "languages": ["Python", "JavaScript"],
        "requirements": "Build a web application with API backend",
        "frameworks": ["FastAPI", "React"],
        "apis": ["OpenAI", "Stripe"],
    }


@pytest.fixture
def mock_generators():
    """Mock all pipeline generators."""
    return {
        "project_design_gen": MagicMock(),
        "basic_devplan_gen": MagicMock(),
        "detailed_devplan_gen": MagicMock(),
        "handoff_gen": MagicMock(),
    }


# Async test utilities
@pytest.fixture
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio

    return asyncio.get_event_loop_policy()


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require API credentials"
    )
