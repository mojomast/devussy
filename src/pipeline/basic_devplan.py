"""Basic devplan generator pipeline stage."""

from __future__ import annotations

import re
from typing import Any, Optional

from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import DevPlan, DevPlanPhase, ProjectDesign
from ..templates import render_template

logger = get_logger(__name__)


class BasicDevPlanGenerator:
    """Generate a high-level development plan with phases from a project design."""

    def __init__(self, llm_client: LLMClient):
        """Initialize the generator with an LLM client.

        Args:
            llm_client: The LLM client instance to use for generation.
        """
        self.llm_client = llm_client

    async def generate(
        self,
        project_design: ProjectDesign,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlan:
        """Generate a high-level devplan from a project design.

        Args:
            project_design: The structured project design
            feedback_manager: Optional FeedbackManager for iterative refinement
            **llm_kwargs: Additional kwargs to pass to the LLM client

        Returns:
            DevPlan with high-level phases (without detailed steps yet)
        """
        logger.info(
            f"Generating basic devplan for project: {project_design.project_name}"
        )

        # Prepare template context
        context = {"project_design": project_design}

        # Render the prompt template
        prompt = render_template("basic_devplan.jinja", context)

        # Apply feedback corrections if available
        if feedback_manager:
            prompt = feedback_manager.apply_corrections_to_prompt(prompt)
            logger.info("Applied feedback corrections to prompt")

        logger.debug(f"Rendered prompt: {prompt[:200]}...")

        # Call the LLM
        response = await self.llm_client.generate_completion(prompt, **llm_kwargs)
        logger.info(f"Received LLM response ({len(response)} chars)")

        # Parse the response into a DevPlan model
        devplan = self._parse_response(response, project_design.project_name)
        logger.info(f"Successfully parsed devplan with {len(devplan.phases)} phases")

        return devplan

    def _parse_response(self, response: str, project_name: str) -> DevPlan:
        """Parse the LLM response into a structured DevPlan.

        Args:
            response: The raw markdown response from the LLM
            project_name: The project name for context

        Returns:
            Parsed DevPlan model with phases
        """
        phases = []
        current_phase = None
        current_items = []

        lines = response.split("\n")

        # Regex to match phase headers like "Phase 1:", "**Phase 1:**", etc.
        phase_pattern = re.compile(
            r"\*?\*?Phase\s+(\d+):?\s*(.+?)(?:\*\*)?$", re.IGNORECASE
        )

        for line in lines:
            stripped = line.strip()

            # Try to match a phase header
            phase_match = phase_pattern.match(stripped)

            if phase_match:
                # Save previous phase if it exists
                if current_phase is not None:
                    phases.append(
                        DevPlanPhase(
                            number=current_phase["number"],
                            title=current_phase["title"],
                            steps=[],  # Steps will be added in detailed phase
                        )
                    )

                # Start new phase
                phase_num = int(phase_match.group(1))
                phase_title = phase_match.group(2).strip()
                # Remove trailing asterisks if present
                phase_title = phase_title.rstrip("*").strip()

                current_phase = {"number": phase_num, "title": phase_title}
                current_items = []
                logger.debug(f"Found phase {phase_num}: {phase_title}")

            elif stripped.startswith("-") and current_phase:
                # This is a component/item for the current phase
                item = stripped[1:].strip()
                if item:
                    current_items.append(item)

        # Don't forget the last phase
        if current_phase is not None:
            phases.append(
                DevPlanPhase(
                    number=current_phase["number"],
                    title=current_phase["title"],
                    steps=[],  # Steps will be added in detailed phase
                )
            )

        # If no phases were parsed, create a default one
        if not phases:
            logger.warning("No phases parsed from response, creating default phase")
            phases.append(
                DevPlanPhase(
                    number=1,
                    title="Implementation",
                    steps=[],
                )
            )

        summary = f"Development plan for {project_name} with {len(phases)} phases"

        return DevPlan(phases=phases, summary=summary)
