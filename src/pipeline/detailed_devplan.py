"""Detailed devplan generator pipeline stage."""

from __future__ import annotations

import re
from typing import Any, List, Optional

from ..concurrency import ConcurrencyManager
from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import DevPlan, DevPlanPhase, DevPlanStep
from ..templates import render_template

logger = get_logger(__name__)


class DetailedDevPlanGenerator:
    """Generate detailed step-by-step plans for each phase.

    Uses concurrent LLM calls for efficiency.
    """

    def __init__(self, llm_client: LLMClient, concurrency_manager: ConcurrencyManager):
        """Initialize the generator with an LLM client and concurrency manager.

        Args:
            llm_client: The LLM client instance to use for generation.
            concurrency_manager: Manager to control concurrent LLM requests.
        """
        self.llm_client = llm_client
        self.concurrency_manager = concurrency_manager

    async def generate(
        self,
        basic_devplan: DevPlan,
        project_name: str,
        tech_stack: List[str] | None = None,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlan:
        """Generate detailed steps for each phase in the devplan.

        Args:
            basic_devplan: The high-level DevPlan with phases
            project_name: Name of the project
            tech_stack: Optional list of technologies being used
            feedback_manager: Optional FeedbackManager for iterative refinement
            **llm_kwargs: Additional kwargs to pass to the LLM client

        Returns:
            DevPlan with detailed numbered steps for each phase
        """
        logger.info(
            f"Generating detailed devplan for {len(basic_devplan.phases)} phases"
        )

        # Generate detailed steps for each phase concurrently
        phase_coros = [
            self._generate_phase_details(
                phase, project_name, tech_stack or [], feedback_manager, **llm_kwargs
            )
            for phase in basic_devplan.phases
        ]

        detailed_phases = await self.concurrency_manager.gather_with_limit(phase_coros)

        logger.info(f"Successfully generated details for {len(detailed_phases)} phases")

        # Create devplan with detailed phases
        devplan = DevPlan(phases=detailed_phases, summary=basic_devplan.summary)

        # Apply manual edits if feedback manager is provided
        if feedback_manager:
            devplan = feedback_manager.preserve_manual_edits(devplan)
            logger.info("Preserved manual edits in devplan")

        return devplan

    async def _generate_phase_details(
        self,
        phase: DevPlanPhase,
        project_name: str,
        tech_stack: List[str],
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlanPhase:
        """Generate detailed steps for a single phase.

        Args:
            phase: The phase to detail
            project_name: Name of the project
            tech_stack: List of technologies
            feedback_manager: Optional FeedbackManager for iterative refinement
            **llm_kwargs: Additional kwargs for LLM

        Returns:
            DevPlanPhase with detailed steps
        """
        logger.debug(f"Generating details for Phase {phase.number}: {phase.title}")

        # Prepare template context
        context = {
            "phase_number": phase.number,
            "phase_title": phase.title,
            "phase_description": "",  # Could add this to the model
            "project_name": project_name,
            "tech_stack": tech_stack,
        }

        # Render the prompt template
        prompt = render_template("detailed_devplan.jinja", context)

        # Apply feedback corrections if available
        if feedback_manager:
            prompt = feedback_manager.apply_corrections_to_prompt(prompt)

        logger.debug(f"Rendered prompt for phase {phase.number}")

        # Call the LLM
        response = await self.llm_client.generate_completion(prompt, **llm_kwargs)
        logger.info(
            f"Received detailed steps for phase {phase.number} ({len(response)} chars)"
        )

        # Parse the response into steps
        steps = self._parse_steps(response, phase.number)
        logger.debug(f"Parsed {len(steps)} steps for phase {phase.number}")

        # Return updated phase with steps
        return DevPlanPhase(number=phase.number, title=phase.title, steps=steps)

    def _parse_steps(self, response: str, phase_number: int) -> List[DevPlanStep]:
        """Parse numbered steps from the LLM response.

        Args:
            response: The raw markdown response from the LLM
            phase_number: The phase number for validation

        Returns:
            List of parsed DevPlanStep objects
        """
        steps = []
        lines = response.split("\n")

        # Regex to match steps like "2.1:", "2.10:", etc.
        step_pattern = re.compile(
            rf"^{phase_number}\.(\d+):?\s*(.+)$",
            re.IGNORECASE,
        )

        current_step = None
        current_details = []

        for line in lines:
            stripped = line.strip()

            # Try to match a step number
            step_match = step_pattern.match(stripped)

            if step_match:
                # Save previous step if it exists
                if current_step is not None:
                    steps.append(
                        DevPlanStep(
                            number=current_step["number"],
                            description=current_step["description"],
                        )
                    )

                # Start new step
                sub_num = int(step_match.group(1))
                description = step_match.group(2).strip()

                current_step = {
                    "number": f"{phase_number}.{sub_num}",
                    "description": description,
                }
                current_details = []
                logger.debug(f"Found step {phase_number}.{sub_num}")

            elif stripped.startswith("-") and current_step:
                # This is a detail/sub-point for the current step
                detail = stripped[1:].strip()
                if detail:
                    current_details.append(detail)

        # Don't forget the last step
        if current_step is not None:
            steps.append(
                DevPlanStep(
                    number=current_step["number"],
                    description=current_step["description"],
                )
            )

        # If no steps were parsed, create a placeholder
        if not steps:
            logger.warning(
                f"No steps parsed for phase {phase_number}, creating placeholder"
            )
            steps.append(
                DevPlanStep(
                    number=f"{phase_number}.1",
                    description="Implement phase requirements",
                )
            )

        return steps
