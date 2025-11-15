"""Phase state management for terminal streaming UI."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class PhaseStatus(Enum):
    """Status of a phase during generation."""
    
    IDLE = "idle"
    STREAMING = "streaming"
    COMPLETE = "complete"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    REGENERATING = "regenerating"


@dataclass
class PhaseStreamState:
    """State of a single phase during streaming generation."""
    
    name: str
    status: PhaseStatus = PhaseStatus.IDLE
    content: str = ""
    token_count: int = 0
    partial_content: str = ""  # Content before cancellation
    error_message: Optional[str] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Steering context
    steering_feedback: Optional[Dict[str, str]] = None
    regeneration_count: int = 0
    
    # Generation context (for regeneration)
    original_prompt: Optional[str] = None
    api_request_context: Optional[Dict] = None


class PhaseStateManager:
    """Manages state for all phases during terminal streaming."""
    
    def __init__(self, phase_names: List[str]):
        """Initialize state manager with phase names.
        
        Args:
            phase_names: List of phase names (e.g., ['plan', 'design', 'implement', 'test', 'review'])
        """
        self.phases: Dict[str, PhaseStreamState] = {
            name: PhaseStreamState(name=name)
            for name in phase_names
        }
    
    def initialize_phase(
        self,
        name: str,
        prompt: str,
        api_context: Optional[Dict] = None
    ) -> None:
        """Initialize a phase for generation.
        
        Args:
            name: Phase name
            prompt: Original prompt for this phase
            api_context: API request context for regeneration
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.content = ""
        phase.token_count = 0
        phase.partial_content = ""
        phase.error_message = None
        phase.completed_at = None
        phase.cancelled_at = None
        phase.status = PhaseStatus.STREAMING
        phase.started_at = datetime.now()
        phase.original_prompt = prompt
        phase.api_request_context = api_context
    
    def get_state(self, name: str) -> PhaseStreamState:
        """Get state for a phase.
        
        Args:
            name: Phase name
            
        Returns:
            PhaseStreamState for the phase
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        return self.phases[name]
    
    def update_status(self, name: str, status: PhaseStatus) -> None:
        """Update phase status.
        
        Args:
            name: Phase name
            status: New status
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.status = status
        
        if status == PhaseStatus.COMPLETE:
            phase.completed_at = datetime.now()
    
    def append_content(self, name: str, token: str) -> None:
        """Append streaming token to phase content.
        
        Args:
            name: Phase name
            token: Token to append
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.content += token
        phase.token_count += 1
    
    def capture_generation_context(
        self,
        name: str,
        prompt: str,
        api_context: Optional[Dict] = None
    ) -> None:
        """Capture context needed for regeneration.
        
        Args:
            name: Phase name
            prompt: Original prompt
            api_context: API request context
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.original_prompt = prompt
        phase.api_request_context = api_context
    
    def record_cancellation(self, name: str) -> None:
        """Record that a phase was cancelled.
        
        Args:
            name: Phase name
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.status = PhaseStatus.INTERRUPTED
        phase.cancelled_at = datetime.now()
        phase.partial_content = phase.content
    
    def record_steering_answers(
        self,
        name: str,
        feedback: Dict[str, str]
    ) -> None:
        """Record steering feedback for a phase.
        
        Args:
            name: Phase name
            feedback: Dictionary of feedback answers
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        self.phases[name].steering_feedback = feedback
    
    def reset_for_regeneration(self, name: str) -> None:
        """Reset phase state for regeneration.
        
        Args:
            name: Phase name
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.status = PhaseStatus.REGENERATING
        phase.content = ""
        phase.token_count = 0
        phase.error_message = None
        phase.started_at = datetime.now()
        phase.completed_at = None
        phase.regeneration_count += 1
    
    def record_error(self, name: str, error: str) -> None:
        """Record an error for a phase.
        
        Args:
            name: Phase name
            error: Error message
        """
        if name not in self.phases:
            raise ValueError(f"Unknown phase: {name}")
        
        phase = self.phases[name]
        phase.status = PhaseStatus.ERROR
        phase.error_message = error
    
    def get_all_states(self) -> Dict[str, PhaseStreamState]:
        """Get all phase states.
        
        Returns:
            Dictionary mapping phase names to states
        """
        return self.phases.copy()
    
    def is_complete(self) -> bool:
        """Check if all phases are complete.
        
        Returns:
            True if all phases are complete or have errors
        """
        return all(
            phase.status in (PhaseStatus.COMPLETE, PhaseStatus.ERROR)
            for phase in self.phases.values()
        )
