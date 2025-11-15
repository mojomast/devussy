"""Tests for phase state management."""

import pytest
from datetime import datetime

from src.terminal.phase_state import (
    PhaseStateManager,
    PhaseStreamState,
    PhaseStatus,
)


@pytest.fixture
def phase_names():
    """Standard phase names."""
    return ["plan", "design", "implement", "test", "review"]


@pytest.fixture
def state_manager(phase_names):
    """Create a phase state manager."""
    return PhaseStateManager(phase_names)


def test_initialization(state_manager, phase_names):
    """Test state manager initialization."""
    assert len(state_manager.phases) == len(phase_names)
    
    for name in phase_names:
        assert name in state_manager.phases
        state = state_manager.get_state(name)
        assert state.name == name
        assert state.status == PhaseStatus.IDLE
        assert state.content == ""
        assert state.token_count == 0


def test_initialize_phase(state_manager):
    """Test phase initialization for generation."""
    prompt = "Generate plan phase"
    api_context = {"model": "gpt-4", "temperature": 0.7}
    
    state_manager.initialize_phase("plan", prompt, api_context)
    
    state = state_manager.get_state("plan")
    assert state.status == PhaseStatus.STREAMING
    assert state.original_prompt == prompt
    assert state.api_request_context == api_context
    assert state.started_at is not None
    assert isinstance(state.started_at, datetime)
    assert state.token_count == 0


def test_update_status(state_manager):
    """Test status updates."""
    state_manager.update_status("plan", PhaseStatus.STREAMING)
    assert state_manager.get_state("plan").status == PhaseStatus.STREAMING
    
    state_manager.update_status("plan", PhaseStatus.COMPLETE)
    state = state_manager.get_state("plan")
    assert state.status == PhaseStatus.COMPLETE
    assert state.completed_at is not None


def test_append_content(state_manager):
    """Test content streaming."""
    state_manager.append_content("plan", "Hello ")
    state_manager.append_content("plan", "world")
    state_manager.append_content("plan", "!")
    
    state = state_manager.get_state("plan")
    assert state.content == "Hello world!"
    assert state.token_count == 3


def test_record_cancellation(state_manager):
    """Test cancellation recording."""
    # Add some content
    state_manager.append_content("plan", "Partial content")
    
    # Cancel
    state_manager.record_cancellation("plan")
    
    state = state_manager.get_state("plan")
    assert state.status == PhaseStatus.INTERRUPTED
    assert state.cancelled_at is not None
    assert state.partial_content == "Partial content"


def test_record_steering_answers(state_manager):
    """Test steering feedback recording."""
    feedback = {
        "issue": "Too verbose",
        "desired_change": "Make it more concise",
        "constraints": "Keep under 100 lines"
    }
    
    state_manager.record_steering_answers("plan", feedback)
    
    state = state_manager.get_state("plan")
    assert state.steering_feedback == feedback


def test_reset_for_regeneration(state_manager):
    """Test phase reset for regeneration."""
    # Setup initial state
    state_manager.initialize_phase("plan", "Original prompt")
    state_manager.append_content("plan", "Old content")
    state_manager.update_status("plan", PhaseStatus.COMPLETE)
    
    # Reset for regeneration
    state_manager.reset_for_regeneration("plan")
    
    state = state_manager.get_state("plan")
    assert state.status == PhaseStatus.REGENERATING
    assert state.content == ""
    assert state.error_message is None
    assert state.regeneration_count == 1
    assert state.original_prompt == "Original prompt"  # Preserved
    assert state.token_count == 0


def test_record_error(state_manager):
    """Test error recording."""
    error_msg = "API timeout"
    
    state_manager.record_error("plan", error_msg)
    
    state = state_manager.get_state("plan")
    assert state.status == PhaseStatus.ERROR
    assert state.error_message == error_msg


def test_get_all_states(state_manager, phase_names):
    """Test getting all states."""
    states = state_manager.get_all_states()
    
    assert len(states) == len(phase_names)
    for name in phase_names:
        assert name in states
        assert isinstance(states[name], PhaseStreamState)


def test_is_complete(state_manager):
    """Test completion check."""
    # Initially not complete
    assert not state_manager.is_complete()
    
    # Mark some complete
    state_manager.update_status("plan", PhaseStatus.COMPLETE)
    state_manager.update_status("design", PhaseStatus.COMPLETE)
    assert not state_manager.is_complete()
    
    # Mark all complete
    state_manager.update_status("implement", PhaseStatus.COMPLETE)
    state_manager.update_status("test", PhaseStatus.COMPLETE)
    state_manager.update_status("review", PhaseStatus.COMPLETE)
    assert state_manager.is_complete()


def test_is_complete_with_errors(state_manager):
    """Test completion check with errors."""
    # Mark some complete, some with errors
    state_manager.update_status("plan", PhaseStatus.COMPLETE)
    state_manager.update_status("design", PhaseStatus.ERROR)
    state_manager.update_status("implement", PhaseStatus.COMPLETE)
    state_manager.update_status("test", PhaseStatus.ERROR)
    state_manager.update_status("review", PhaseStatus.COMPLETE)
    
    # Should be considered complete (errors are terminal states)
    assert state_manager.is_complete()


def test_unknown_phase_errors(state_manager):
    """Test that operations on unknown phases raise errors."""
    with pytest.raises(ValueError, match="Unknown phase"):
        state_manager.get_state("unknown")
    
    with pytest.raises(ValueError, match="Unknown phase"):
        state_manager.update_status("unknown", PhaseStatus.COMPLETE)
    
    with pytest.raises(ValueError, match="Unknown phase"):
        state_manager.append_content("unknown", "content")


def test_multiple_regenerations(state_manager):
    """Test multiple regeneration cycles."""
    state_manager.initialize_phase("plan", "Original prompt")
    
    # First regeneration
    state_manager.reset_for_regeneration("plan")
    assert state_manager.get_state("plan").regeneration_count == 1
    
    # Second regeneration
    state_manager.reset_for_regeneration("plan")
    assert state_manager.get_state("plan").regeneration_count == 2
    
    # Third regeneration
    state_manager.reset_for_regeneration("plan")
    assert state_manager.get_state("plan").regeneration_count == 3


def test_capture_generation_context(state_manager):
    """Test capturing generation context."""
    prompt = "Generate detailed plan"
    api_context = {
        "model": "gpt-4",
        "temperature": 0.8,
        "max_tokens": 2000
    }
    
    state_manager.capture_generation_context("plan", prompt, api_context)
    
    state = state_manager.get_state("plan")
    assert state.original_prompt == prompt
    assert state.api_request_context == api_context
