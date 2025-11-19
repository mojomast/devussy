"""Basic devplan generator pipeline stage."""

from __future__ import annotations

import asyncio
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
        task_group_size: int = 3,
        repo_analysis: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlan:
        """Generate a high-level devplan from a project design.

        Args:
            project_design: The structured project design
            feedback_manager: Optional FeedbackManager for iterative refinement
            task_group_size: Number of tasks per group before updating artifacts
            repo_analysis: Optional RepoAnalysis for existing project context
            **llm_kwargs: Additional kwargs to pass to the LLM client

        Returns:
            DevPlan with high-level phases (without detailed steps yet)
        """
        logger.info(
            f"Generating basic devplan for project: {project_design.project_name}"
        )

        # Prepare template context
        context = {
            "project_design": project_design,
            "task_group_size": task_group_size,
        }
        
        # Add repo context if available
        if repo_analysis is not None:
            context["repo_context"] = repo_analysis.to_prompt_context()
        
        # Add code samples if available in llm_kwargs
        if "code_samples" in llm_kwargs:
            context["code_samples"] = llm_kwargs.pop("code_samples")

        # Render the prompt template
        prompt = render_template("basic_devplan.jinja", context)

        # Apply feedback corrections if available
        if feedback_manager:
            prompt = feedback_manager.apply_corrections_to_prompt(prompt)
            logger.info("Applied feedback corrections to prompt")

        logger.debug(f"Rendered prompt: {prompt[:200]}...")

        # Optional streaming handler for console output
        streaming_handler = llm_kwargs.pop("streaming_handler", None)

        # Call the LLM
        streaming_enabled = hasattr(self.llm_client, "streaming_enabled") and getattr(
            self.llm_client, "streaming_enabled", False
        )

        if streaming_enabled and streaming_handler is not None:
            # Use streaming with console/token handler
            async with streaming_handler:
                response_chunks: list[str] = []

                def token_callback(token: str) -> None:
                    """Sync callback invoked by LLM client for each streamed chunk."""
                    response_chunks.append(token)
                    # Call async handler properly like project_design does
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    if loop and loop.is_running():
                        loop.create_task(streaming_handler.on_token_async(token))
                    else:
                        # Fallback: best-effort synchronous run
                        asyncio.run(streaming_handler.on_token_async(token))

                full_response = await self.llm_client.generate_completion_streaming(
                    prompt,
                    callback=token_callback,
                    **llm_kwargs,
                )

                await streaming_handler.on_completion_async(full_response)

            response = full_response

        elif streaming_enabled:
            # Use streaming without external handler
            response = ""

            def token_callback(token: str) -> None:
                nonlocal response
                response += token

            response = await self.llm_client.generate_completion_streaming(
                prompt, callback=token_callback, **llm_kwargs
            )
        else:
            # Use non-streaming for backwards compatibility
            response = await self.llm_client.generate_completion(prompt, **llm_kwargs)
            
        logger.info(f"Received LLM response ({len(response)} chars)")
        logger.debug(f"Devplan response preview: {response[:800]}...")
        
        # Save full response for debugging
        import os
        debug_dir = ".devussy_state"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        with open(os.path.join(debug_dir, "last_devplan_response.txt"), "w", encoding="utf-8") as f:
            f.write(response)

        # Parse the response into a DevPlan model
        devplan = self._parse_response(response, project_design.project_name)
        
        # Store the raw LLM response for full documentation
        devplan.raw_basic_response = response
        
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
        current_description = ""  # Track description text
        # Assign canonical phase numbers sequentially in order of appearance,
        # regardless of what the model wrote in the heading.
        next_phase_number = 1

        lines = response.split("\n")

        # Try multiple patterns for phase headers to handle varied LLM formats
        phase_patterns = [
            # 1) N. **Phase N: Title** (numbered with bold phase)
            re.compile(
                r"^\d+\.\s*\*\*\s*Phase\s+0*(\d+)\s*[:\-–—]\s*(.+?)\s*\*\*\s*$",
                re.IGNORECASE,
            ),
            # 2) **Phase N: Title** (bold with asterisks)
            re.compile(
                r"^\*\*\s*Phase\s+0*(\d+)\s*[:\-–—]\s*(.+?)\s*\*\*\s*$",
                re.IGNORECASE,
            ),
            # 3) Phase N: Title (plain text)
            re.compile(
                r"^Phase\s+0*(\d+)\s*[:\-–—]\s*(.+)$",
                re.IGNORECASE,
            ),
            # 4) ## Phase N: Title (markdown header)
            re.compile(
                r"^#{1,6}\s*Phase\s+0*(\d+)\s*[:\-–—]\s*(.+)$",
                re.IGNORECASE,
            ),
            # 5) N. Title or N) Title (generic numbered)
            re.compile(r"^(\d+)\s*[\.)]\s*(.+)$", re.IGNORECASE),
        ]
        
        logger.info(f"Parsing response with {len(lines)} lines")
        non_empty = [l for l in lines[:30] if l.strip()][:15]
        logger.info(f"First 15 non-empty lines: {non_empty}")

        for line in lines:
            stripped = line.strip()

            # Try to match a phase header with any known pattern
            phase_match = None
            model_phase_num = None
            match_title = None
            for pat in phase_patterns:
                m = pat.match(stripped)
                if m:
                    phase_match = m
                    try:
                        model_phase_num = int(m.group(1))
                        match_title = m.group(2).strip()
                    except Exception:
                        phase_match = None
                        continue
                    break

            if phase_match:
                logger.debug(f"Matched phase header: '{stripped}' -> Phase {next_phase_number}: {match_title}")
                # Save previous phase if it exists
                if current_phase is not None:
                    # Clean up description: strip whitespace and markdown formatting
                    description = current_description.strip()
                    # Remove markdown bold/italic markers
                    description = re.sub(r'\*+', '', description)
                    
                    phases.append(
                        DevPlanPhase(
                            number=current_phase["number"],
                            title=current_phase["title"],
                            description=description if description else None,
                            steps=[],  # Steps will be added in detailed phase
                        )
                    )

                # Assign a canonical phase number based on order of appearance,
                # ignoring whatever number the model wrote. This prevents
                # duplicate phase numbers from leaking into the devplan.
                phase_num = next_phase_number
                next_phase_number += 1

                phase_title = match_title or f"Phase {phase_num}"
                # Remove trailing asterisks if present
                phase_title = phase_title.rstrip("*").strip()

                current_phase = {"number": phase_num, "title": phase_title}
                current_items = []
                current_description = ""  # Reset description for new phase
                if model_phase_num is not None and model_phase_num != phase_num:
                    logger.debug(
                        f"Found phase heading '{phase_title}' with model number {model_phase_num}; "
                        f"assigned canonical phase {phase_num}"
                    )
                else:
                    logger.debug(f"Found phase {phase_num}: {phase_title}")

            elif stripped.startswith("-") and current_phase:
                # Check if this is a "Summary:" line
                if stripped.startswith("- Summary:") or stripped.startswith("- summary:"):
                    # Extract the summary text after "Summary:"
                    summary_text = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
                    if summary_text:
                        current_description = summary_text
                else:
                    # This is a component/item for the current phase
                    item = stripped[1:].strip()
                    if item and not item.lower().startswith("summary:") and not item.lower().startswith("major components:"):
                        current_items.append(item)

            elif stripped and not stripped.startswith("#") and current_phase and not current_items and not current_description:
                # This is description text (appears after header, before first bullet)
                # Concatenate non-empty lines that aren't headers or bullets
                if current_description:
                    current_description += " " + stripped
                else:
                    current_description = stripped

        # Don't forget the last phase
        if current_phase is not None:
            # Clean up description for last phase
            description = current_description.strip()
            description = re.sub(r'\*+', '', description)
            
            phases.append(
                DevPlanPhase(
                    number=current_phase["number"],
                    title=current_phase["title"],
                    description=description if description else None,
                    steps=[],  # Steps will be added in detailed phase
                )
            )

        # If no phases were parsed, create a default one
        if not phases:
            print("=" * 80)
            print("WARNING: No phases parsed from response, creating default phase")
            print(f"Response preview (first 800 chars):\n{response[:800]}")
            print("=" * 80)
            potential_headers = [l for l in lines if 'phase' in l.lower() or re.match(r'^\d+[\.)]\s', l)][:10]
            print(f"Lines that might be phase headers: {potential_headers}")
            print("=" * 80)
            phases.append(
                DevPlanPhase(
                    number=1,
                    title="Implementation",
                    steps=[],
                )
            )

        summary = f"Development plan for {project_name} with {len(phases)} phases"

        return DevPlan(phases=phases, summary=summary)
