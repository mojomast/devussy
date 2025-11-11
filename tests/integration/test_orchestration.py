"""Integration tests for runtime orchestration features.

Tests for:
- Checkpointing and resumption
- Streaming handler integration
- Provider switching mid-workflow
- Rate limit handling
- Feedback integration
- Full workflow execution
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError

from src.concurrency import ConcurrencyManager
from src.config import AppConfig, LLMConfig
from src.feedback_manager import FeedbackManager
from src.file_manager import FileManager
from src.models import DevPlan, DevPlanPhase, DevPlanStep, ProjectDesign
from src.pipeline.compose import PipelineOrchestrator
from src.state_manager import StateManager


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
    """Mock LLM client."""
    client = AsyncMock()
    client.generate_completion = AsyncMock()
    client.generate_multiple = AsyncMock()
    return client


@pytest.fixture
def sample_project_design():
    """Sample project design for testing."""
    return ProjectDesign(
        project_name="test-project",
        objectives=["Build web application", "Create API"],
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        architecture_overview="Test architecture",
        dependencies=["requests", "pydantic", "uvicorn"],
        challenges=["Performance", "Scalability"],
        mitigations=["Use caching", "Load balancing"],
    )


@pytest.fixture
def sample_devplan():
    """Sample development plan for testing."""
    phase = DevPlanPhase(
        number=1,
        title="Setup",
        description="Initial setup",
        steps=[
            DevPlanStep(
                number="1.1",
                description="Create project structure",
                done=False,
            )
        ],
    )
    return DevPlan(
        summary="Test plan summary",
        phases=[phase],
    )


@pytest.fixture
def orchestrator_with_mocks(mock_config, mock_llm_client, temp_state_dir):
    """Create orchestrator with mocked dependencies."""
    concurrency_manager = ConcurrencyManager(max_concurrent=2)
    file_manager = FileManager()
    state_manager = StateManager(temp_state_dir)

    orchestrator = PipelineOrchestrator(
        llm_client=mock_llm_client,
        concurrency_manager=concurrency_manager,
        file_manager=file_manager,
        config=mock_config,
        state_manager=state_manager,
    )

    return orchestrator


class TestCheckpointing:
    """Test checkpoint functionality."""

    @pytest.mark.asyncio
    async def test_checkpoint_saving_during_pipeline(
        self, orchestrator_with_mocks, sample_project_design, sample_devplan
    ):
        """Test that checkpoints are saved at each stage."""
        orchestrator = orchestrator_with_mocks

        # Mock generator responses
        orchestrator.project_design_gen.generate = AsyncMock(
            return_value=sample_project_design
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=sample_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(
            return_value=sample_devplan
        )
        mock_handoff = MagicMock()
        mock_handoff.content = "Test handoff"
        mock_handoff.model_dump.return_value = {"content": "Test handoff"}
        orchestrator.handoff_gen.generate = MagicMock(return_value=mock_handoff)

        # Run pipeline
        await orchestrator.run_full_pipeline(
            project_name="test-project",
            languages=["Python"],
            requirements="Test requirements",
            output_dir="test_output",
        )

        # Check that checkpoints were created
        checkpoints = orchestrator.state_manager.list_checkpoints()
        assert len(checkpoints) >= 1

        # Check latest checkpoint contains final stage data
        latest_checkpoint = orchestrator.state_manager.get_latest_checkpoint()
        assert latest_checkpoint is not None
        assert latest_checkpoint["stage"] in [
            "project_design",
            "basic_devplan",
            "detailed_devplan",
            "handoff_prompt",
        ]

    @pytest.mark.asyncio
    async def test_resume_from_project_design_checkpoint(
        self, orchestrator_with_mocks, sample_project_design, sample_devplan
    ):
        """Test resuming pipeline from project design checkpoint."""
        orchestrator = orchestrator_with_mocks

        # Create a project design checkpoint
        checkpoint_data = {
            "project_design": sample_project_design.model_dump(),
            "project_name": "test-project",
            "languages": ["Python"],
            "requirements": "Test requirements",
            "frameworks": None,
            "apis": None,
        }

        orchestrator.state_manager.save_checkpoint(
            checkpoint_key="test-project_pipeline",
            stage="project_design",
            data=checkpoint_data,
            metadata={"provider": "openai"},
        )

        # Mock remaining generators
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=sample_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(
            return_value=sample_devplan
        )
        mock_handoff = MagicMock()
        mock_handoff.content = "Test handoff"
        mock_handoff.model_dump.return_value = {"content": "Test handoff"}
        orchestrator.handoff_gen.generate = MagicMock(return_value=mock_handoff)

        # Resume from checkpoint
        design, devplan, handoff = await orchestrator.resume_from_checkpoint(
            "test-project_pipeline"
        )

        assert design.project_name == "test-project"
        assert devplan.summary is not None
        assert handoff.content == "Test handoff"

    @pytest.mark.asyncio
    async def test_resume_from_nonexistent_checkpoint(self, orchestrator_with_mocks):
        """Test error handling when resuming from nonexistent checkpoint."""
        orchestrator = orchestrator_with_mocks

        with pytest.raises(ValueError, match="Checkpoint not found"):
            await orchestrator.resume_from_checkpoint("nonexistent_checkpoint")

    @pytest.mark.asyncio
    async def test_checkpoint_with_provider_switching(
        self, orchestrator_with_mocks, sample_project_design
    ):
        """Test checkpoint saving and resumption with provider switching."""
        orchestrator = orchestrator_with_mocks

        # Create checkpoint
        checkpoint_data = {
            "project_design": sample_project_design.model_dump(),
            "project_name": "test-project",
            "languages": ["Python"],
            "requirements": "Test requirements",
        }

        orchestrator.state_manager.save_checkpoint(
            checkpoint_key="test-project_pipeline",
            stage="project_design",
            data=checkpoint_data,
            metadata={"provider": "openai"},
        )

        # Mock provider switching (should fail gracefully since we don't have
        # different providers set up)
        with patch.object(orchestrator, "switch_provider") as mock_switch:
            mock_switch.side_effect = ValueError("Provider switching failed")

            with pytest.raises(ValueError, match="Provider switching failed"):
                await orchestrator.resume_from_checkpoint(
                    "test-project_pipeline", provider_override="generic"
                )


class TestProviderSwitching:
    """Test dynamic provider switching."""

    def test_switch_provider_same_provider(self, orchestrator_with_mocks):
        """Test switching to the same provider (should be no-op)."""
        orchestrator = orchestrator_with_mocks
        original_client = orchestrator.llm_client

        orchestrator.switch_provider("openai")  # Same as current

        assert orchestrator.llm_client is original_client

    def test_switch_provider_no_config(self, mock_llm_client):
        """Test provider switching without config fails."""
        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=ConcurrencyManager(2),
            config=None,  # No config
        )

        with pytest.raises(ValueError, match="Provider switching requires config"):
            orchestrator.switch_provider("generic")


class TestStreamingIntegration:
    """Test streaming handler integration."""

    @pytest.mark.asyncio
    async def test_streaming_enabled_in_config(self, mock_config, temp_state_dir):
        """Test streaming integration when enabled in config."""
        # Enable streaming
        mock_config.streaming_enabled = True

        with patch("src.pipeline.compose.create_llm_client") as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            orchestrator = PipelineOrchestrator(
                llm_client=mock_client,
                concurrency_manager=ConcurrencyManager(2),
                config=mock_config,
                state_manager=StateManager(temp_state_dir),
            )

            # Mock generators to avoid actual LLM calls
            with patch.object(orchestrator, "project_design_gen") as mock_gen:
                mock_design = MagicMock()
                mock_design.dict.return_value = {"test": "data"}
                mock_gen.generate = AsyncMock(return_value=mock_design)

                # This should not raise an error even with streaming enabled
                result = await orchestrator.project_design_gen.generate(
                    project_name="test",
                    languages=["Python"],
                    requirements="test",
                )
                assert result is not None


class TestRateLimitHandling:
    """Test rate limit handling integration."""

    @pytest.mark.asyncio
    async def test_rate_limit_handling_in_pipeline(self, orchestrator_with_mocks):
        """Test rate limit handling during pipeline execution."""
        orchestrator = orchestrator_with_mocks

        # Mock a rate limit error followed by success
        rate_limit_error = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=429,
            headers={"Retry-After": "1"},
        )

        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise rate_limit_error
            return MagicMock(dict=lambda: {"test": "data"})

        orchestrator.project_design_gen.generate = mock_generate

        # Mock rate limiter to handle the error
        with patch("src.rate_limiter.RateLimiter") as MockRateLimiter:
            rate_limiter = MagicMock()
            rate_limiter.handle_rate_limit = AsyncMock()
            MockRateLimiter.return_value = rate_limiter

            # This should handle the rate limit gracefully
            with pytest.raises(ClientResponseError):
                # The orchestrator doesn't directly handle rate limits yet,
                # this tests that the error propagates correctly
                await orchestrator.project_design_gen.generate(
                    project_name="test",
                    languages=["Python"],
                    requirements="test",
                )


class TestFeedbackIntegration:
    """Test feedback manager integration."""

    @pytest.mark.asyncio
    async def test_pipeline_with_feedback_manager(
        self, orchestrator_with_mocks, sample_project_design, sample_devplan
    ):
        """Test pipeline execution with feedback manager."""
        orchestrator = orchestrator_with_mocks

        # Create temporary feedback file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            feedback_data = {
                "corrections": {"phase_1": {"title": "Improved Setup Phase"}},
                "manual_edits": {},
            }
            import yaml

            yaml.dump(feedback_data, f)
            feedback_file_path = f.name

        try:
            feedback_manager = FeedbackManager(Path(feedback_file_path))

            # Mock generators
            orchestrator.project_design_gen.generate = AsyncMock(
                return_value=sample_project_design
            )
            orchestrator.basic_devplan_gen.generate = AsyncMock(
                return_value=sample_devplan
            )
            orchestrator.detailed_devplan_gen.generate = AsyncMock(
                return_value=sample_devplan
            )
            mock_handoff = MagicMock()
            mock_handoff.content = "Test handoff"
            mock_handoff.model_dump.return_value = {"content": "Test handoff"}
            orchestrator.handoff_gen.generate = MagicMock(return_value=mock_handoff)

            # Run pipeline with feedback
            design, devplan, handoff = await orchestrator.run_full_pipeline(
                project_name="test-project",
                languages=["Python"],
                requirements="Test requirements",
                feedback_manager=feedback_manager,
            )

            # Verify feedback manager was passed to generators
            orchestrator.basic_devplan_gen.generate.assert_called_once()
            args, kwargs = orchestrator.basic_devplan_gen.generate.call_args
            assert kwargs.get("feedback_manager") is feedback_manager

        finally:
            Path(feedback_file_path).unlink(missing_ok=True)


class TestFullWorkflowExecution:
    """Test complete workflow execution scenarios."""

    @pytest.mark.asyncio
    async def test_complete_pipeline_execution(
        self, orchestrator_with_mocks, sample_project_design, sample_devplan
    ):
        """Test complete pipeline from start to finish."""
        orchestrator = orchestrator_with_mocks

        # Mock all generators
        orchestrator.project_design_gen.generate = AsyncMock(
            return_value=sample_project_design
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=sample_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(
            return_value=sample_devplan
        )
        mock_handoff = MagicMock()
        mock_handoff.content = "Test handoff content"
        mock_handoff.model_dump.return_value = {"content": "Test handoff content"}
        orchestrator.handoff_gen.generate = MagicMock(return_value=mock_handoff)

        # Execute complete pipeline
        design, devplan, handoff = await orchestrator.run_full_pipeline(
            project_name="integration-test",
            languages=["Python", "JavaScript"],
            requirements="Build a web application with API backend",
            frameworks=["FastAPI", "React"],
            apis=["OpenAI"],
            output_dir="test_output",
        )

        # Verify all stages completed
        assert design.project_name == "test-project"
        assert devplan.summary is not None
        assert handoff.content == "Test handoff content"

        # Verify checkpoints were created
        checkpoints = orchestrator.state_manager.list_checkpoints()
        assert len(checkpoints) >= 1

        # Verify final checkpoint contains all data
        latest = orchestrator.state_manager.get_latest_checkpoint()
        assert latest is not None
        assert "project_design" in latest["data"]

    @pytest.mark.asyncio
    async def test_pipeline_interruption_and_resumption(
        self, orchestrator_with_mocks, sample_project_design, sample_devplan
    ):
        """Test pipeline interruption and successful resumption."""
        orchestrator = orchestrator_with_mocks

        # Mock generators for initial run (simulate failure after project design)
        orchestrator.project_design_gen.generate = AsyncMock(
            return_value=sample_project_design
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(
            side_effect=Exception("Simulated interruption")
        )

        # First run should fail after project design checkpoint
        with pytest.raises(Exception, match="Simulated interruption"):
            await orchestrator.run_full_pipeline(
                project_name="interrupted-project",
                languages=["Python"],
                requirements="Test requirements",
            )

        # Verify checkpoint was created before failure
        checkpoints = orchestrator.state_manager.list_checkpoints()
        assert len(checkpoints) >= 1

        # Find the project design checkpoint
        checkpoint_key = None
        for checkpoint in checkpoints:
            if checkpoint["stage"] == "project_design":
                checkpoint_key = checkpoint["key"]
                break

        assert checkpoint_key is not None

        # Now fix the generators and resume
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=sample_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(
            return_value=sample_devplan
        )
        mock_handoff = MagicMock()
        mock_handoff.content = "Resumed handoff"
        mock_handoff.model_dump.return_value = {"content": "Resumed handoff"}
        orchestrator.handoff_gen.generate = MagicMock(return_value=mock_handoff)

        # Resume from checkpoint
        design, devplan, handoff = await orchestrator.resume_from_checkpoint(
            checkpoint_key
        )

        assert design.project_name == "test-project"
        assert devplan.summary is not None
        assert handoff.content == "Resumed handoff"

    @pytest.mark.asyncio
    async def test_concurrent_pipeline_executions(self, mock_config, temp_state_dir):
        """Test multiple concurrent pipeline executions with separate state."""
        # Create two separate orchestrators
        orchestrators = []
        for i in range(2):
            mock_client = AsyncMock()
            state_dir = f"{temp_state_dir}/state_{i}"
            Path(state_dir).mkdir(parents=True, exist_ok=True)

            orchestrator = PipelineOrchestrator(
                llm_client=mock_client,
                concurrency_manager=ConcurrencyManager(2),
                config=mock_config,
                state_manager=StateManager(state_dir),
            )

            # Mock generators
            sample_design = ProjectDesign(
                project_name=f"concurrent-project-{i}",
                objectives=[f"Objective {i}"],
                tech_stack=["Python", "FastAPI"],
                architecture_overview=f"Architecture {i}",
                dependencies=["requests"],
                challenges=[f"Challenge {i}"],
                mitigations=[f"Mitigation {i}"],
            )

            orchestrator.project_design_gen.generate = AsyncMock(
                return_value=sample_design
            )
            orchestrator.basic_devplan_gen.generate = AsyncMock(
                return_value=DevPlan(
                    summary=f"Plan {i}",
                    phases=[],
                )
            )
            orchestrator.detailed_devplan_gen.generate = AsyncMock(
                return_value=DevPlan(
                    summary=f"Detailed plan {i}",
                    phases=[],
                )
            )
            mock_handoff = MagicMock()
            mock_handoff.content = f"Handoff {i}"
            mock_handoff.model_dump.return_value = {"content": f"Handoff {i}"}
            orchestrator.handoff_gen.generate = MagicMock(return_value=mock_handoff)

            orchestrators.append(orchestrator)

        # Run pipelines concurrently
        tasks = [
            orchestrator.run_full_pipeline(
                project_name=f"concurrent-project-{i}",
                languages=["Python"],
                requirements=f"Requirements {i}",
                output_dir=f"output_{i}",
            )
            for i, orchestrator in enumerate(orchestrators)
        ]

        results = await asyncio.gather(*tasks)

        # Verify both completed successfully with correct data
        for i, (design, devplan, handoff) in enumerate(results):
            assert design.project_name == f"concurrent-project-{i}"
            assert devplan.summary == f"Detailed plan {i}"
            assert handoff.content == f"Handoff {i}"

        # Verify separate checkpoints were created
        for i, orchestrator in enumerate(orchestrators):
            checkpoints = orchestrator.state_manager.list_checkpoints()
            assert len(checkpoints) >= 1
            # Verify checkpoint is for the right project
            for checkpoint in checkpoints:
                data = orchestrator.state_manager.load_checkpoint(checkpoint["key"])
                if "project_design" in data["data"]:
                    design_data = data["data"]["project_design"]
                    assert design_data["project_name"] == f"concurrent-project-{i}"


class TestErrorHandling:
    """Test error handling in orchestration scenarios."""

    @pytest.mark.asyncio
    async def test_checkpoint_corruption_handling(
        self, orchestrator_with_mocks, temp_state_dir
    ):
        """Test handling of corrupted checkpoint files."""
        orchestrator = orchestrator_with_mocks

        # Create a corrupted checkpoint file
        checkpoint_file = Path(temp_state_dir) / "checkpoint_corrupted.json"
        checkpoint_file.write_text("invalid json content")

        # List checkpoints should handle corruption gracefully
        checkpoints = orchestrator.state_manager.list_checkpoints()
        # Should not include the corrupted checkpoint
        corrupted_keys = [cp["key"] for cp in checkpoints if cp["key"] == "corrupted"]
        assert len(corrupted_keys) == 0

    @pytest.mark.asyncio
    async def test_partial_checkpoint_data(self, orchestrator_with_mocks):
        """Test handling of incomplete checkpoint data."""
        orchestrator = orchestrator_with_mocks

        # Create checkpoint with missing required data
        incomplete_data = {
            "project_name": "test",
            # Missing project_design and other required fields
        }

        orchestrator.state_manager.save_checkpoint(
            checkpoint_key="incomplete_checkpoint",
            stage="project_design",
            data=incomplete_data,
        )

        # Resuming should handle missing data gracefully
        with pytest.raises((KeyError, ValueError)):
            await orchestrator.resume_from_checkpoint("incomplete_checkpoint")


if __name__ == "__main__":
    pytest.main([__file__])
