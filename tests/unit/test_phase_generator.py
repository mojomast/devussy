"""Unit tests for TerminalPhaseGenerator."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.terminal.phase_generator import TerminalPhaseGenerator
from src.terminal.phase_state import PhaseStateManager, PhaseStatus
from src.models import DevPlan, DevPlanPhase


@pytest.fixture
def sample_devplan():
    """Create a sample devplan for testing."""
    return DevPlan(
        phases=[
            DevPlanPhase(
                number=1,
                title="Plan",
                description="Planning phase",
                steps=[
                    {"number": "1.1", "description": "Task 1"},
                    {"number": "1.2", "description": "Task 2"},
                ],
            ),
            DevPlanPhase(
                number=2,
                title="Design",
                description="Design phase",
                steps=[
                    {"number": "2.1", "description": "Design task 1"},
                ],
            ),
        ],
        summary="Test devplan for phase generator",
    )


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock()
    client.generate_completion_streaming = AsyncMock()
    return client


@pytest.fixture
def state_manager():
    """Create a state manager."""
    return PhaseStateManager(["plan", "design", "implement", "test", "review"])


@pytest.fixture
def phase_generator(mock_llm_client, state_manager):
    """Create a phase generator with mocked dependencies."""
    return TerminalPhaseGenerator(mock_llm_client, state_manager)


class TestPhaseGenerator:
    """Tests for TerminalPhaseGenerator."""
    
    def test_initialization(self, phase_generator, mock_llm_client, state_manager):
        """Test phase generator initialization."""
        assert phase_generator.llm_client == mock_llm_client
        assert phase_generator.state_manager == state_manager
        assert phase_generator._abort_controllers == {}
    
    def test_build_phase_prompt_basic(self, phase_generator, sample_devplan):
        """Test basic prompt building."""
        prompt = phase_generator._build_phase_prompt("plan", sample_devplan)
        
        assert "PLAN Phase Generation" in prompt
        assert "Planning phase" in prompt
        assert "1.1" in prompt
        assert "Task 1" in prompt
        assert "Task 2" in prompt
    
    def test_build_phase_prompt_with_steering(self, phase_generator, sample_devplan):
        """Test prompt building with steering feedback."""
        context = {
            "steering_feedback": {
                "issue": "Too vague",
                "desired_change": "More specific",
                "constraints": "Keep it short",
            }
        }
        
        prompt = phase_generator._build_phase_prompt("plan", sample_devplan, context)
        
        assert "Steering Feedback" in prompt
        assert "Too vague" in prompt
        assert "More specific" in prompt
        assert "Keep it short" in prompt
    
    def test_build_phase_prompt_unknown_phase(self, phase_generator, sample_devplan):
        """Test prompt building for unknown phase."""
        prompt = phase_generator._build_phase_prompt("unknown", sample_devplan)
        
        assert "unknown phase" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_phase_streaming_success(
        self, phase_generator, sample_devplan, mock_llm_client, state_manager
    ):
        """Test successful phase generation with streaming."""
        # Mock streaming to return content
        async def mock_streaming(prompt, callback, **kwargs):
            tokens = ["Hello", " ", "world", "!"]
            for token in tokens:
                await callback(token)
            return "Hello world!"
        
        mock_llm_client.generate_completion_streaming.side_effect = mock_streaming
        
        # Generate phase
        result = await phase_generator.generate_phase_streaming(
            "plan",
            sample_devplan,
        )
        
        # Verify result
        assert result == "Hello world!"
        
        # Verify state updates
        state = state_manager.get_state("plan")
        assert state.status == PhaseStatus.COMPLETE
        assert state.content == "Hello world!"
        assert state.started_at is not None
    
    @pytest.mark.asyncio
    async def test_generate_phase_streaming_with_callback(
        self, phase_generator, sample_devplan, mock_llm_client
    ):
        """Test phase generation with custom token callback."""
        # Mock streaming
        async def mock_streaming(prompt, callback, **kwargs):
            tokens = ["A", "B", "C"]
            for token in tokens:
                await callback(token)
            return "ABC"
        
        mock_llm_client.generate_completion_streaming.side_effect = mock_streaming
        
        # Track tokens
        received_tokens = []
        
        def on_token(token):
            received_tokens.append(token)
        
        # Generate phase
        await phase_generator.generate_phase_streaming(
            "plan",
            sample_devplan,
            on_token=on_token,
        )
        
        # Verify callback was called
        assert received_tokens == ["A", "B", "C"]
    
    @pytest.mark.asyncio
    async def test_generate_phase_streaming_cancellation(
        self, phase_generator, sample_devplan, mock_llm_client, state_manager
    ):
        """Test phase cancellation during streaming."""
        # Mock streaming that can be cancelled
        async def mock_streaming(prompt, callback, **kwargs):
            tokens = ["Token"] * 100
            for token in tokens:
                await callback(token)
                await asyncio.sleep(0.01)
            return "".join(tokens)
        
        mock_llm_client.generate_completion_streaming.side_effect = mock_streaming
        
        # Start generation
        task = asyncio.create_task(
            phase_generator.generate_phase_streaming("plan", sample_devplan)
        )
        
        # Wait a bit then cancel
        await asyncio.sleep(0.05)
        phase_generator.cancel_phase("plan")
        
        # Wait for task to complete
        with pytest.raises(asyncio.CancelledError):
            await task
        
        # Verify state
        state = state_manager.get_state("plan")
        assert state.status == PhaseStatus.INTERRUPTED
        assert state.cancelled_at is not None
    
    @pytest.mark.asyncio
    async def test_generate_phase_streaming_error(
        self, phase_generator, sample_devplan, mock_llm_client, state_manager
    ):
        """Test error handling during phase generation."""
        # Mock streaming that raises error
        mock_llm_client.generate_completion_streaming.side_effect = Exception(
            "API Error"
        )
        
        # Generate phase
        with pytest.raises(Exception, match="API Error"):
            await phase_generator.generate_phase_streaming("plan", sample_devplan)
        
        # Verify error state
        state = state_manager.get_state("plan")
        assert state.status == PhaseStatus.ERROR
        assert "API Error" in state.error_message
    
    @pytest.mark.asyncio
    async def test_regenerate_phase_with_steering(
        self, phase_generator, sample_devplan, mock_llm_client, state_manager
    ):
        """Test phase regeneration with steering feedback."""
        # Mock streaming
        async def mock_streaming(prompt, callback, **kwargs):
            await callback("Regenerated content")
            return "Regenerated content"
        
        mock_llm_client.generate_completion_streaming.side_effect = mock_streaming
        
        # Regenerate with feedback
        feedback = {
            "issue": "Not detailed enough",
            "desired_change": "Add more examples",
            "constraints": "Keep under 500 words",
        }
        
        result = await phase_generator.regenerate_phase_with_steering(
            "plan",
            sample_devplan,
            feedback,
        )
        
        # Verify result
        assert result == "Regenerated content"
        
        # Verify state
        state = state_manager.get_state("plan")
        assert state.status == PhaseStatus.COMPLETE
        assert state.steering_feedback == feedback
        assert state.regeneration_count == 1
    
    @pytest.mark.asyncio
    async def test_generate_all_phases(
        self, phase_generator, sample_devplan, mock_llm_client
    ):
        """Test concurrent generation of all phases."""
        # Mock streaming
        call_count = 0
        
        async def mock_streaming(prompt, callback, **kwargs):
            nonlocal call_count
            call_count += 1
            content = f"Phase {call_count} content"
            await callback(content)
            return content
        
        mock_llm_client.generate_completion_streaming.side_effect = mock_streaming
        
        # Generate all phases
        results = await phase_generator.generate_all_phases(
            sample_devplan,
            phase_names=["plan", "design"],
        )
        
        # Verify results
        assert len(results) == 2
        assert "plan" in results
        assert "design" in results
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_all_phases_with_callback(
        self, phase_generator, sample_devplan, mock_llm_client
    ):
        """Test concurrent generation with per-phase callbacks."""
        # Mock streaming
        async def mock_streaming(prompt, callback, **kwargs):
            await callback("token")
            return "content"
        
        mock_llm_client.generate_completion_streaming.side_effect = mock_streaming
        
        # Track callbacks
        callbacks = []
        
        def on_token(phase_name, token):
            callbacks.append((phase_name, token))
        
        # Generate all phases
        await phase_generator.generate_all_phases(
            sample_devplan,
            phase_names=["plan", "design"],
            on_token=on_token,
        )
        
        # Verify callbacks
        assert len(callbacks) == 2
        phase_names = [cb[0] for cb in callbacks]
        assert "plan" in phase_names
        assert "design" in phase_names
    
    def test_cancel_phase_not_running(self, phase_generator):
        """Test cancelling a phase that's not running."""
        # Should not raise error
        phase_generator.cancel_phase("plan")
        
        # Verify no abort controller exists
        assert "plan" not in phase_generator._abort_controllers
