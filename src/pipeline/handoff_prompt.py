"""Handoff prompt generator pipeline stage."""

from __future__ import annotations

from typing import Any, Dict, List

from ..logger import get_logger
from ..models import DevPlan, DevPlanPhase, HandoffPrompt
from ..templates import render_template
from ..utils.anchor_utils import ensure_anchors_exist

logger = get_logger(__name__)


class HandoffPromptGenerator:
    """Generate handoff prompts that summarize progress and next steps."""

    def generate(
        self,
        devplan: DevPlan,
        project_name: str,
        project_summary: str = "",
        architecture_notes: str = "",
        dependencies_notes: str = "",
        config_notes: str = "",
        task_group_size: int = 5,
        repo_analysis: Any = None,
        **kwargs: Any,
    ) -> HandoffPrompt:
        """Generate a handoff prompt from a devplan and progress state.

        Args:
            devplan: The development plan
            project_name: Name of the project
            project_summary: Summary of the project
            architecture_notes: Notes about architecture
            dependencies_notes: Notes about dependencies
            config_notes: Notes about configuration
            task_group_size: Number of upcoming tasks to execute before the next mandatory update
            repo_analysis: Optional RepoAnalysis for existing project context
            **kwargs: Additional context

        Returns:
            HandoffPrompt model with content and next steps
        """
        logger.info(f"Generating handoff prompt for project: {project_name}")

        # Separate completed and in-progress phases
        completed_phases = [p for p in devplan.phases if self._is_phase_complete(p)]
        in_progress_phase = self._get_in_progress_phase(devplan.phases)

        # Get next steps to work on (limited by task_group_size)
        next_steps = self._get_next_steps(devplan.phases, limit=task_group_size)

        # Derive quick status fields for the clean template
        if in_progress_phase:
            current_phase_number = in_progress_phase["number"]
            current_phase_name = in_progress_phase["title"]
        else:
            current_phase_number = "None"
            current_phase_name = "No active phase"

        if next_steps:
            next_task_id = next_steps[0]["number"]
            next_task_description = next_steps[0]["description"]
        else:
            next_task_id = "None"
            next_task_description = "No remaining steps"

        # Prepare template context for minimal handoff
        context: Dict[str, Any] = {
            "project_name": project_name,
            "current_phase_number": current_phase_number,
            "current_phase_name": current_phase_name,
            "next_task_id": next_task_id,
            "next_task_description": next_task_description,
            "blockers": kwargs.get("blockers", "None known"),
            "detail_level": kwargs.get("detail_level", "normal"),  # Control template verbosity
        }
        
        # Add repo context if available
        if repo_analysis is not None:
            context["repo_context"] = repo_analysis.to_prompt_context()
        
        # Add code samples if available in kwargs
        if "code_samples" in kwargs:
            context["code_samples"] = kwargs.get("code_samples")

        # Render the template
        content = render_template("handoff_prompt.jinja", context)
        # Ensure critical anchors exist for downstream agents
        content = ensure_anchors_exist(
            content,
            ["QUICK_STATUS", "DEV_INSTRUCTIONS", "TOKEN_RULES", "HANDOFF_NOTES"],
        )
        logger.info("Successfully generated handoff prompt")

        # Extract next step summaries for the model
        next_step_summaries = [f"{s['number']}: {s['title']}" for s in next_steps]

        return HandoffPrompt(content=content, next_steps=next_step_summaries)

    def _is_phase_complete(self, phase: DevPlanPhase) -> bool:
        """Check if a phase is fully complete."""
        if not phase.steps:
            return False
        return all(step.done for step in phase.steps)

    def _get_in_progress_phase(
        self, phases: List[DevPlanPhase]
    ) -> Dict[str, Any] | None:
        """Find the phase currently in progress."""
        for phase in phases:
            if not self._is_phase_complete(phase) and any(
                step.done for step in phase.steps
            ):
                completed_steps = [s for s in phase.steps if s.done]
                remaining_steps = [s for s in phase.steps if not s.done]

                return {
                    "number": phase.number,
                    "title": phase.title,
                    "completed_steps": completed_steps,
                    "remaining_steps": remaining_steps,
                }
        return None

    def _get_next_steps(
        self, phases: List[DevPlanPhase], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get the next N steps to work on."""
        next_steps = []

        for phase in phases:
            for step in phase.steps:
                if not step.done:
                    next_steps.append(
                        {
                            "number": step.number,
                            "title": step.description[:80],  # Truncate if too long
                            "description": step.description,
                            "notes": None,  # Could add notes in the future
                        }
                    )
                    if len(next_steps) >= limit:
                        return next_steps

        return next_steps
