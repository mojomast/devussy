"""Detailed devplan generator pipeline stage."""

from __future__ import annotations

import re
import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional, Callable, Dict
from textwrap import dedent

from ..concurrency import ConcurrencyManager
from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import DevPlan, DevPlanPhase, DevPlanStep
from ..templates import render_template
from .hivemind import HiveMindManager
from ..config import load_config

logger = get_logger(__name__)


@dataclass
class PhaseDetailResult:
    """Metadata for a generated phase, including the raw response payload."""

    phase: DevPlanPhase
    raw_response: str
    response_chars: int


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
        self.hivemind = HiveMindManager(llm_client)

    async def generate(
        self,
        basic_devplan: DevPlan,
        project_name: str,
        tech_stack: List[str] | None = None,
        feedback_manager: Optional[Any] = None,
    on_phase_complete: Optional[Callable[[PhaseDetailResult], None]] = None,
        task_group_size: int = 3,
        repo_analysis: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlan:
        """Generate detailed steps for each phase in the devplan.

        Args:
            basic_devplan: The high-level DevPlan with phases
            project_name: Name of the project
            tech_stack: Optional list of technologies being used
            feedback_manager: Optional FeedbackManager for iterative refinement
            on_phase_complete: Optional callback when each phase completes
            task_group_size: Number of tasks per group before updating artifacts
            repo_analysis: Optional RepoAnalysis for existing project context
            **llm_kwargs: Additional kwargs to pass to the LLM client

        Returns:
            DevPlan with detailed numbered steps for each phase
        """
        logger.info(
            f"Generating detailed devplan for {len(basic_devplan.phases)} phases",
            extra={"suppress_console": True},
        )

        # Deduplicate phases by canonical number to avoid generating the
        # same phase multiple times when the basic devplan contains
        # duplicate phase numbers (which can happen if the model repeats
        # headings). Preserve first occurrence order.
        unique_phases = []
        seen_numbers: Dict[int, DevPlanPhase] = {}
        for phase in basic_devplan.phases:
            if phase.number in seen_numbers:
                logger.warning(
                    "Duplicate phase number %s ('%s') in basic devplan; "
                    "will reuse details from the first occurrence.",
                    phase.number,
                    phase.title,
                )
                continue
            seen_numbers[phase.number] = phase
            unique_phases.append(phase)

        # Generate detailed steps for each unique phase concurrently with progress callbacks
        tasks = [
            asyncio.create_task(
                self.concurrency_manager.run_with_limit(
                    self._generate_phase_details(
                        phase,
                        project_name,
                        tech_stack or [],
                        feedback_manager,
                        task_group_size=task_group_size,
                        repo_analysis=repo_analysis,
                        **llm_kwargs,
                    )
                )
            )
            for phase in unique_phases
        ]

        detailed_by_number: Dict[int, DevPlanPhase] = {}
        raw_detailed_responses: Dict[int, str] = {}
        completed = 0

        for fut in asyncio.as_completed(tasks):
            phase_result = await fut
            detailed_by_number[phase_result.phase.number] = phase_result.phase
            raw_detailed_responses[phase_result.phase.number] = phase_result.raw_response
            completed += 1
            if on_phase_complete:
                try:
                    on_phase_complete(phase_result)
                except Exception:
                    pass

        # Reassemble phases in canonical order (one entry per phase number)
        detailed_phases = [detailed_by_number[p.number] for p in unique_phases]

        logger.info(
            f"Successfully generated details for {len(detailed_phases)} phases",
            extra={"suppress_console": True},
        )

        # Create devplan with detailed phases
        devplan = DevPlan(phases=detailed_phases, summary=basic_devplan.summary)
        if raw_detailed_responses:
            devplan.raw_detailed_responses = raw_detailed_responses
        
        # Preserve the raw LLM response from the basic devplan
        if hasattr(basic_devplan, 'raw_basic_response'):
            devplan.raw_basic_response = basic_devplan.raw_basic_response

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
        task_group_size: int = 3,
        repo_analysis: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlanPhase:
        """Generate detailed steps for a single phase.

        Args:
            phase: The phase to detail
            project_name: Name of the project
            tech_stack: List of technologies
            feedback_manager: Optional FeedbackManager for iterative refinement
            task_group_size: Number of tasks per group before updating artifacts
            repo_analysis: Optional RepoAnalysis for existing project context
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
            "task_group_size": task_group_size,
            "detail_level": llm_kwargs.get("detail_level", "normal"),  # Control template verbosity
        }
        
        # Add repo context if available
        if repo_analysis is not None:
            context["repo_context"] = repo_analysis.to_prompt_context()
        
        # Add code samples if available in llm_kwargs
        if "code_samples" in llm_kwargs:
            context["code_samples"] = llm_kwargs.pop("code_samples")

        # Render the prompt template
        prompt = render_template("detailed_devplan.jinja", context)

        # Apply feedback corrections if available
        if feedback_manager:
            prompt = feedback_manager.apply_corrections_to_prompt(prompt)

        logger.debug(f"Rendered prompt for phase {phase.number}")

        # Check if streaming is enabled and handler is provided
        streaming_handler = llm_kwargs.pop("streaming_handler", None)
        # Only treat streaming as enabled when the flag is an actual bool.
        # This avoids AsyncMock attributes (in tests) being interpreted as
        # truthy and forcing the streaming path with a mocked client.
        raw_stream_flag = getattr(self.llm_client, "streaming_enabled", False)
        streaming_enabled = bool(raw_stream_flag) if isinstance(raw_stream_flag, bool) else False

        # Check HiveMind config
        config = load_config()

        # Primary call uses configured defaults (provider/model-specific)
        if config.hivemind.enabled:
            logger.info(f"HiveMind enabled for phase {phase.number}")
            # Pass streaming handler if available (HiveMind handles it for Arbiter)
            if streaming_handler:
                llm_kwargs["streaming_handler"] = streaming_handler
            
            response = await self.hivemind.run_swarm(
                prompt,
                count=config.hivemind.drone_count,
                temperature_jitter=config.hivemind.temperature_jitter,
                **llm_kwargs
            )
            response_used = response
            print(f"[detailed_devplan] HiveMind complete for phase {phase.number}, got {len(response)} chars")

        elif streaming_enabled and streaming_handler is not None:
            print(f"[detailed_devplan] Using streaming for phase {phase.number}")
            # Use streaming with handler
            response_chunks: list[str] = []

            def token_callback(token: str) -> None:
                """Sync callback invoked by LLM client for each streamed chunk."""
                response_chunks.append(token)
                # Call async handler
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    loop.create_task(streaming_handler.on_token_async(token))

            response = await self.llm_client.generate_completion_streaming(
                prompt,
                callback=token_callback,
                **llm_kwargs,
            )
            response_used = response
            print(f"[detailed_devplan] Streaming complete for phase {phase.number}, got {len(response)} chars")
        else:
            print(f"[detailed_devplan] Using non-streaming for phase {phase.number}")
            response = await self.llm_client.generate_completion(
                prompt, **llm_kwargs
            )
            response_used = response
        
        logger.info(
            f"Received detailed steps for phase {phase.number} ({len(response)} chars)",
            extra={"suppress_console": True},
        )

        # Parse the response into steps
        steps = self._parse_steps(response, phase.number)
        logger.debug(f"Parsed {len(steps)} steps for phase {phase.number}")

        # Fallback: if response is empty or no steps parsed, retry with strict format
        if not response.strip() or not steps:
            logger.warning(
                f"No usable details parsed for phase {phase.number}; attempting fallback prompt"
            )
            fallback_prompt = dedent(
                f"""
                You are generating a detailed implementation plan for a software project.
                Project: {project_name}
                Phase {phase.number}: {phase.title}

                Return ONLY the following strict format in plain text (no headings, no extra prose):
                {phase.number}.1: <short step title>
                - <detail>
                - <detail>
                {phase.number}.2: <short step title>
                - <detail>
                - <detail>

                Provide at least 8 steps. Keep each step concise and actionable.
                Do not include any content other than the numbered steps and their '-' bullet details.
                """
            ).strip()
            try:
                # Reduce temperature and cap tokens to avoid model length cutoffs
                fallback_kwargs = dict(llm_kwargs)
                fallback_kwargs.setdefault("temperature", 0.3)
                # If caller didn't set, use a conservative cap for better reliability
                if "max_tokens" not in fallback_kwargs:
                    fallback_kwargs["max_tokens"] = 1200
                response2 = await self.llm_client.generate_completion(
                    fallback_prompt, **fallback_kwargs
                )
                steps2 = self._parse_steps(response2, phase.number)
                if steps2:
                    logger.info(
                        f"Fallback succeeded: parsed {len(steps2)} steps for phase {phase.number}"
                    )
                    steps = steps2
                    response_used = response2
                else:
                    logger.warning(
                        f"Fallback still produced no steps for phase {phase.number}; using placeholder"
                    )
                    # Second attempt: even stricter formatting and smaller output
                    fallback_prompt2 = dedent(
                        f"""
                        Phase {phase.number}: {phase.title}

                        Return EXACTLY 8 steps in this strict format with no extra text:
                        {phase.number}.1: <title>\n- <detail>\n- <detail>
                        {phase.number}.2: <title>\n- <detail>\n- <detail>
                        ... up to {phase.number}.8
                        """
                    ).strip()
                    fallback_kwargs2 = dict(fallback_kwargs)
                    fallback_kwargs2["max_tokens"] = min(900, fallback_kwargs.get("max_tokens", 1200))
                    fallback_kwargs2["temperature"] = 0.2
                    try:
                        response3 = await self.llm_client.generate_completion(
                            fallback_prompt2, **fallback_kwargs2
                        )
                        steps3 = self._parse_steps(response3, phase.number)
                        if steps3:
                            logger.info(
                                f"Second fallback succeeded: parsed {len(steps3)} steps for phase {phase.number}"
                            )
                            steps = steps3
                            response_used = response3
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(
                    f"Fallback prompt failed for phase {phase.number}: {e}. Using placeholder"
                )

        # Return updated phase with steps
        phase_model = DevPlanPhase(number=phase.number, title=phase.title, steps=steps)
        return PhaseDetailResult(
            phase=phase_model,
            raw_response=response_used,
            response_chars=len(response_used or ""),
        )

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
                            details=current_details[:],
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
                    details=current_details[:],
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
