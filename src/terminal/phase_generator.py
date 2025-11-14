"""Terminal-aware phase generator with streaming support.

This module provides phase generation that streams LLM tokens directly to the
terminal UI via PhaseStateManager, with support for cancellation and regeneration.
"""

import asyncio
from typing import Any, Callable, Dict, Optional

from ..llm_client import LLMClient
from ..models import DevPlan
from .phase_state import PhaseStateManager, PhaseStatus


class TerminalPhaseGenerator:
    """Generates phases with streaming output to terminal UI."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        state_manager: PhaseStateManager,
    ):
        """Initialize terminal phase generator.
        
        Args:
            llm_client: LLM client for generation
            state_manager: Phase state manager for UI updates
        """
        self.llm_client = llm_client
        self.state_manager = state_manager
        self._abort_controllers: Dict[str, asyncio.Event] = {}
    
    def _build_phase_prompt(
        self,
        phase_name: str,
        devplan: DevPlan,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build prompt for a specific phase.
        
        Args:
            phase_name: Name of phase to generate
            devplan: Development plan with project context
            context: Additional context (e.g., steering feedback)
            
        Returns:
            Formatted prompt string
        """
        # Find the phase in the devplan
        phase_obj = None
        for phase in devplan.phases:
            if phase.title.lower() == phase_name.lower():
                phase_obj = phase
                break
        
        if not phase_obj:
            return f"Generate detailed content for the {phase_name} phase."
        
        # Build base prompt
        prompt_parts = [
            f"# {phase_name.upper()} Phase Generation",
            "",
        ]
        
        # Add project summary if available
        if devplan.summary:
            prompt_parts.extend([
                f"## Project Summary",
                devplan.summary,
                "",
            ])
        
        # Add phase overview
        prompt_parts.extend([
            f"## Phase Overview",
            f"**Phase {phase_obj.number}:** {phase_obj.title}",
        ])
        
        if phase_obj.description:
            prompt_parts.append(f"**Description:** {phase_obj.description}")
        
        prompt_parts.append("")
        
        # Add steps if available
        if phase_obj.steps:
            prompt_parts.append("## Steps")
            for step in phase_obj.steps:
                prompt_parts.append(f"{step.number}. {step.description}")
                if step.details:
                    for detail in step.details:
                        prompt_parts.append(f"   - {detail}")
            prompt_parts.append("")
        
        # Add steering context if regenerating
        if context and context.get("steering_feedback"):
            feedback = context["steering_feedback"]
            prompt_parts.extend([
                "## Steering Feedback",
                "",
                f"**Issue:** {feedback.get('issue', 'N/A')}",
                f"**Desired Change:** {feedback.get('desired_change', 'N/A')}",
                f"**Constraints:** {feedback.get('constraints', 'N/A')}",
                "",
                "Please regenerate this phase incorporating the feedback above.",
                "",
            ])
        
        # Add generation instructions
        prompt_parts.extend([
            "## Instructions",
            f"Generate comprehensive, detailed content for the {phase_name} phase.",
            "Include:",
            "- Clear objectives and goals",
            "- Step-by-step implementation details",
            "- Code examples where relevant",
            "- Testing strategies",
            "- Potential challenges and solutions",
            "",
            "Format the output in clear markdown with proper headings and structure.",
        ])
        
        return "\n".join(prompt_parts)
    
    async def generate_phase_streaming(
        self,
        phase_name: str,
        devplan: DevPlan,
        on_token: Optional[Callable[[str], Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a phase with streaming tokens to UI.
        
        Args:
            phase_name: Name of phase to generate
            devplan: Development plan with project context
            on_token: Optional additional token callback
            **kwargs: Additional LLM parameters
            
        Returns:
            Complete generated content
            
        Raises:
            asyncio.CancelledError: If generation is cancelled
        """
        # Build prompt
        prompt = self._build_phase_prompt(phase_name, devplan)
        
        # Initialize phase state
        self.state_manager.initialize_phase(
            phase_name,
            prompt=prompt,
            api_context={"model": kwargs.get("model", "gpt-4o-mini")},
        )
        
        # Create abort controller
        abort_event = asyncio.Event()
        self._abort_controllers[phase_name] = abort_event
        
        try:
            # Define streaming callback
            async def token_callback(token: str) -> None:
                # Check for cancellation
                if abort_event.is_set():
                    raise asyncio.CancelledError(f"Phase {phase_name} cancelled")
                
                # Update state manager
                self.state_manager.append_content(phase_name, token)
                
                # Call additional callback if provided
                if on_token:
                    if asyncio.iscoroutinefunction(on_token):
                        await on_token(token)
                    else:
                        on_token(token)
            
            # Generate with streaming
            full_content = await self.llm_client.generate_completion_streaming(
                prompt,
                callback=token_callback,
                **kwargs,
            )
            
            # Mark complete
            self.state_manager.update_status(phase_name, PhaseStatus.COMPLETE)
            
            return full_content
            
        except asyncio.CancelledError:
            # Record cancellation
            self.state_manager.record_cancellation(phase_name)
            raise
            
        except Exception as e:
            # Record error
            self.state_manager.record_error(phase_name, str(e))
            raise
            
        finally:
            # Clean up abort controller
            if phase_name in self._abort_controllers:
                del self._abort_controllers[phase_name]
    
    def cancel_phase(self, phase_name: str) -> None:
        """Cancel a streaming phase generation.
        
        Args:
            phase_name: Name of phase to cancel
        """
        if phase_name in self._abort_controllers:
            self._abort_controllers[phase_name].set()
    
    async def regenerate_phase_with_steering(
        self,
        phase_name: str,
        devplan: DevPlan,
        steering_feedback: Dict[str, str],
        on_token: Optional[Callable[[str], Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Regenerate a phase with steering feedback.
        
        Args:
            phase_name: Name of phase to regenerate
            devplan: Development plan with project context
            steering_feedback: User feedback for regeneration
            on_token: Optional additional token callback
            **kwargs: Additional LLM parameters
            
        Returns:
            Complete regenerated content
        """
        # Record steering feedback
        self.state_manager.record_steering_answers(phase_name, steering_feedback)
        
        # Reset for regeneration
        self.state_manager.reset_for_regeneration(phase_name)
        
        # Build prompt with steering context
        context = {"steering_feedback": steering_feedback}
        prompt = self._build_phase_prompt(phase_name, devplan, context)
        
        # Update generation context
        self.state_manager.capture_generation_context(
            phase_name,
            prompt=prompt,
            api_context={"model": kwargs.get("model", "gpt-4o-mini")},
        )
        
        # Create abort controller
        abort_event = asyncio.Event()
        self._abort_controllers[phase_name] = abort_event
        
        try:
            # Define streaming callback
            async def token_callback(token: str) -> None:
                if abort_event.is_set():
                    raise asyncio.CancelledError(f"Phase {phase_name} cancelled")
                
                self.state_manager.append_content(phase_name, token)
                
                if on_token:
                    if asyncio.iscoroutinefunction(on_token):
                        await on_token(token)
                    else:
                        on_token(token)
            
            # Generate with streaming
            full_content = await self.llm_client.generate_completion_streaming(
                prompt,
                callback=token_callback,
                **kwargs,
            )
            
            # Mark complete
            self.state_manager.update_status(phase_name, PhaseStatus.COMPLETE)
            
            return full_content
            
        except asyncio.CancelledError:
            self.state_manager.record_cancellation(phase_name)
            raise
            
        except Exception as e:
            self.state_manager.record_error(phase_name, str(e))
            raise
            
        finally:
            if phase_name in self._abort_controllers:
                del self._abort_controllers[phase_name]
    
    async def generate_all_phases(
        self,
        devplan: DevPlan,
        phase_names: Optional[list[str]] = None,
        on_token: Optional[Callable[[str, str], Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, str]:
        """Generate all phases concurrently with streaming.
        
        Args:
            devplan: Development plan with project context
            phase_names: List of phase names (default: all phases in devplan)
            on_token: Optional callback(phase_name, token)
            **kwargs: Additional LLM parameters
            
        Returns:
            Dictionary mapping phase names to generated content
        """
        if phase_names is None:
            phase_names = [phase.title.lower() for phase in devplan.phases]
        
        # Create tasks for all phases
        async def generate_one(phase_name: str) -> tuple[str, str]:
            phase_callback = None
            if on_token:
                phase_callback = lambda token: on_token(phase_name, token)
            
            content = await self.generate_phase_streaming(
                phase_name,
                devplan,
                on_token=phase_callback,
                **kwargs,
            )
            return phase_name, content
        
        # Run all phases concurrently
        tasks = [generate_one(name) for name in phase_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        output = {}
        for result in results:
            if isinstance(result, Exception):
                # Log error but continue
                continue
            phase_name, content = result
            output[phase_name] = content
        
        return output
