"""LLM-driven interactive interview system for project requirements gathering.

This module provides a conversational alternative to the scripted YAML questionnaire,
allowing users to have natural conversations with an LLM while gathering project
requirements for the devplan pipeline.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Literal
import sys

from rich.console import Console
from rich.console import Group
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt
from prompt_toolkit import prompt as pt_prompt
import shutil
import yaml

from .clients.factory import create_llm_client
from .config import AppConfig
from .ui.menu import run_menu, SessionSettings, apply_settings_to_config
from .interview import RepoAnalysis
from .interview.code_sample_extractor import CodeSampleExtractor, CodeSample
from .interview.complexity_analyzer import ComplexityProfile
from .markdown_output_manager import MarkdownOutputManager

console = Console()
logger = logging.getLogger(__name__)


class LLMInterviewManager:
    """Conducts conversational interviews using LLM.

    The manager supports three modes:
    - ``"initial"`` (default): requirements-gathering interview
    - ``"design_review"``: focused review of an existing design/devplan
    - ``"follow_up"``: clarification questions when complexity analysis has low confidence
    """

    SYSTEM_PROMPT = """You are a helpful development planning assistant for DevUssY, a circular development system. Your goal is to gather project requirements through natural conversation.

IMPORTANT: Do NOT trigger any generation automatically. When you have all required information, clearly ask the user to confirm by typing '/done' to finalize the interview. Wait for '/done' before ending the interview.

REQUIRED INFORMATION TO COLLECT:
1. Project name (short, descriptive)
2. Primary programming language(s)
3. Project description/requirements (1-2 sentences minimum)
4. Project type (Web App, API, CLI, Game, etc.)

OPTIONAL INFORMATION:
- Frontend/backend frameworks
- Database choice
- Authentication needs
- External APIs to integrate
- Deployment platform
- Testing requirements
- CI/CD preferences
- Documentation level

CONVERSATION GUIDELINES:
- Ask questions naturally, one at a time
- Provide suggestions and recommendations when asked
- Explain tradeoffs between technology choices
- Be flexible with answers - accept variations (e.g., "FastAPI" or "FastApi")
- If user asks for advice, provide thoughtful recommendations
- Periodically summarize what you've gathered
- When you have all REQUIRED information, summarize and ask the user to type '/done' to finalize
- Do not end the interview until the user explicitly types '/done'

RESPONSE FORMAT:
- Speak directly to the user in second person ("you")
- Keep responses concise and helpful
- Show enthusiasm for their project ideas
- Use emojis sparingly for key moments

When interview is complete, output a JSON block with extracted data:
{
    "project_name": "...",
    "primary_language": "...",
    "requirements": "...",
    "project_type": "...",
    "frameworks": [...],
    "database": "...",
    "authentication": false,
    "deployment_platform": "...",
    "testing_requirements": "...",
    "ci_cd": true
}"""

    # Design-review specific system prompt used when mode="design_review".
    DESIGN_REVIEW_SYSTEM_PROMPT = """You are a senior software architect for DevUssY conducting a focused DESIGN REVIEW of an existing proposal.

You are NOT gathering first-pass requirements. Instead, you are reviewing an existing project design and devplan for risks, gaps, and inconsistencies.

You will receive design artifacts as context (project design, devplan summary, automatic design review, repo analysis). Read them carefully before asking questions.

INTERVIEW GOAL:
- Help the user refine the design so it is realistic, internally consistent, and implementation-ready.
- Identify missing requirements or constraints.
- Surface architectural risks, integration issues, and tech stack concerns.

GUIDELINES:
- Do NOT re-ask basic project name or language unless there is a clear conflict in the artifacts.
- Focus questions on:
    - Risky or ambiguous architectural choices
    - Integration points between components/services
    - Performance, scalability, and reliability concerns
    - Data model and storage decisions
    - Testing and observability strategies
- Periodically summarize key risks and decisions.
- When you have enough information, ask the user to type '/done' to finalize the review.

FINAL OUTPUT REQUIREMENT:
At the end of the review (after the user types /done), you MUST produce ONE final JSON summary with this exact shape:
{
    "status": "ok" | "needs-changes",
    "updated_requirements": "...",   // markdown or text, can be empty
    "new_constraints": ["..."],      // list of new or clarified constraints
    "updated_tech_stack": ["..."],   // updated languages/frameworks/tools
    "integration_risks": ["..."],    // notable integration/architecture risks
    "notes": "..."                   // any other guidance or comments
}

Always output that JSON block clearly (optionally inside ```json fences) once the review is complete.
"""

    # Follow-up mode system prompt for clarification questions
    FOLLOW_UP_SYSTEM_PROMPT = """You are a helpful development planning assistant for DevUssY. The complexity analysis of the project has identified areas that need clarification.

You have been given specific questions to ask the user. Your goal is to gather the missing information efficiently without re-doing the entire interview.

GUIDELINES:
- Ask the provided clarification questions one at a time
- Be direct and specific - the user has already provided initial project information
- Accept brief answers - you're filling in gaps, not gathering all requirements
- If the user says "skip" or "proceed anyway", respect that and move to the next question
- When all clarifications are gathered (or skipped), ask the user to type '/done'

RESPONSE FORMAT:
- Keep responses concise
- Show which clarification you're asking about
- Don't repeat questions the user has already answered

When clarifications are complete, output a JSON block with the clarified data:
{
    "clarifications": {
        "question_key": "user_answer",
        ...
    },
    "confidence_boost": 0.1  // estimated improvement to confidence
}
"""

    def __init__(
        self,
        config: AppConfig,
        verbose: bool = False,
        repo_analysis: "RepoAnalysis | None" = None,
        markdown_output_manager: "MarkdownOutputManager | None" = None,
        mode: Literal["initial", "design_review", "follow_up"] = "initial",
    ):
        """Initialize with app config containing LLM settings.

        Args:
            config: Application configuration.
            verbose: Enable verbose logging / debug output.
            repo_analysis: Optional repository analysis used to prime the
                conversation with concrete project context.
            markdown_output_manager: Optional markdown output manager for
                saving responses.
            mode: "initial" for requirements gathering, "design_review" for
                review of an existing design/devplan, or "follow_up" for
                clarification questions.
        """
        self.config = config
        self.verbose = verbose
        self.repo_analysis = repo_analysis
        self.markdown_output_manager = markdown_output_manager
        self.mode: Literal["initial", "design_review", "follow_up"] = mode

        self.llm_client = create_llm_client(config)

        # Apply debug/verbose flag to client (robust attribute discovery)
        self._apply_client_debug(verbose)

        # Core interview state
        self.conversation_history = []
        self.extracted_data = {}
        self.code_samples: list[CodeSample] = []

        # Session-scoped interactive settings (not persisted)
        self.session_settings = SessionSettings()

        # Optional design-review specific context and extracted feedback
        self._design_review_context_md = None
        self._design_review_feedback = None

        # Track question counter for markdown output
        self.question_counter = 0

        # Setup logging
        self._setup_logging()

        # Add system prompt (core behavior), switched by mode
        if self.mode == "design_review":
            system_prompt = self.DESIGN_REVIEW_SYSTEM_PROMPT
        elif self.mode == "follow_up":
            system_prompt = self.FOLLOW_UP_SYSTEM_PROMPT
        else:
            system_prompt = self.SYSTEM_PROMPT

        self.conversation_history.append({"role": "system", "content": system_prompt})

        # Store follow-up questions for follow_up mode
        self._follow_up_questions: list[str] = []
        self._complexity_profile: ComplexityProfile | None = None

        # If repository analysis is available, prepend a concise summary so the
        # interview is repo-aware without changing the primary instructions.
        if self.repo_analysis is not None:
            summary = self._build_repo_summary(self.repo_analysis)
            if summary:
                self.conversation_history.append(
                    {
                        "role": "system",
                        "content": (
                            "The user is working in the following existing project. "
                            "Use this context when asking questions and giving guidance.\n\n"
                            f"{summary}"
                        ),
                    }
                )

        logger.info("LLM Interview Manager initialized")
        logger.info(f"Verbose mode: {self.verbose}")
        logger.info(f"Provider: {config.llm.provider}")
        logger.info(f"Model: {config.llm.model}")

    # ------------------------------------------------------------------
    # Design-review specific helpers
    # ------------------------------------------------------------------

    def set_design_review_context(
        self,
        design_md: str,
        devplan_md: Optional[str] = None,
        review_md: Optional[str] = None,
        repo_summary_md: Optional[str] = None,
    ) -> None:
        """Attach rich markdown context for design-review mode.

        The context is provided to the LLM at the beginning of the
        conversation when running in ``mode="design_review"`` so the
        assistant can act as a senior architect reviewing an existing
        proposal instead of gathering fresh requirements.
        """

        sections: list[str] = []

        # Artifact 1: Initial Project Design
        sections.append("## Artifact 1: Initial Project Design (v1)\n\n")
        sections.append((design_md or "_No design available._").strip())

        # Artifact 2: DevPlan Summary
        sections.append("\n\n## Artifact 2: DevPlan Summary\n\n")
        devplan_text = (devplan_md or "").strip() or "_No devplan summary available yet._"
        sections.append(devplan_text)

        # Artifact 3: Automatic Design Review
        sections.append("\n\n## Artifact 3: Automatic Design Review\n\n")
        review_text = (review_md or "").strip() or "_No automatic design review available._"
        sections.append(review_text)

        # Artifact 4: Repo Analysis Summary
        sections.append("\n\n## Artifact 4: Repo Analysis Summary\n\n")
        repo_text = (repo_summary_md or "").strip() or "_No repo analysis summary available._"
        sections.append(repo_text)

        preamble = (
            "Here is the current design and related context. "
            "Read this fully, then ask me clarifying questions as a senior "
            "architect before we finalize adjustments.\n\n"
        )

        self._design_review_context_md = preamble + "".join(sections)

    # ------------------------------------------------------------------
    # Follow-up mode helpers (for complexity-driven clarifications)
    # ------------------------------------------------------------------

    def switch_mode(self, new_mode: Literal["initial", "design_review", "follow_up"]) -> None:
        """Switch the interview mode and update the system prompt.

        This allows transitioning from initial interview to follow-up mode
        when the complexity analyzer detects low confidence and needs
        clarification questions.

        Args:
            new_mode: The new mode to switch to.
        """
        if new_mode == self.mode:
            return

        self.mode = new_mode

        # Select the appropriate system prompt
        if new_mode == "design_review":
            system_prompt = self.DESIGN_REVIEW_SYSTEM_PROMPT
        elif new_mode == "follow_up":
            system_prompt = self.FOLLOW_UP_SYSTEM_PROMPT
        else:
            system_prompt = self.SYSTEM_PROMPT

        # Update the first system message in conversation history
        for i, msg in enumerate(self.conversation_history):
            if msg.get("role") == "system":
                self.conversation_history[i] = {"role": "system", "content": system_prompt}
                break

        logger.info(f"Switched interview mode to: {new_mode}")

    def set_follow_up_context(
        self,
        complexity_profile: ComplexityProfile,
        follow_up_questions: list[str],
        interview_data: Dict[str, Any] | None = None,
    ) -> None:
        """Set context for follow-up mode.

        Args:
            complexity_profile: The complexity profile with low confidence.
            follow_up_questions: List of clarification questions to ask.
            interview_data: Optional previous interview data for context.
        """
        self._complexity_profile = complexity_profile
        self._follow_up_questions = follow_up_questions

        # Build context message for the LLM
        context_parts = [
            "The complexity analysis has identified areas needing clarification.",
            f"Current confidence: {complexity_profile.confidence:.2f}",
            f"Complexity score: {complexity_profile.complexity_score}",
            f"Estimated phases: {complexity_profile.estimated_phases}",
            "",
            "Please ask the following clarification questions:",
        ]

        for i, q in enumerate(follow_up_questions, 1):
            context_parts.append(f"{i}. {q}")

        if interview_data:
            context_parts.append("")
            context_parts.append("Previous interview data collected:")
            for key, value in interview_data.items():
                if value:
                    context_parts.append(f"- {key}: {value}")

        context_md = "\n".join(context_parts)

        # Add as a system message for context
        self.conversation_history.append({
            "role": "system",
            "content": context_md
        })

        logger.info(f"Set follow-up context with {len(follow_up_questions)} questions")

    def request_clarifications(self, missing_context: list[str]) -> Dict[str, Any]:
        """Request clarifications for missing context and return gathered data.

        This is a simplified flow that asks follow-up questions and returns
        the clarified data without running a full interactive loop.

        Args:
            missing_context: List of areas needing clarification.

        Returns:
            Dict with clarification responses.
        """
        if not missing_context:
            return {}

        self._follow_up_questions = missing_context
        clarifications: Dict[str, Any] = {}

        console.print(Panel.fit(
            "[bold cyan]Clarification Questions[/bold cyan]\n"
            "The complexity analysis needs more information.\n"
            "[dim]Type 'skip' to proceed without answering.[/dim]",
            border_style="cyan"
        ))

        for i, question in enumerate(missing_context, 1):
            console.print(f"\n[yellow]Question {i}/{len(missing_context)}:[/yellow]")
            console.print(f"[white]{question}[/white]")

            try:
                if sys.stdin.isatty() and sys.stdout.isatty():
                    answer = pt_prompt("Your answer: ")
                else:
                    answer = Prompt.ask("Your answer", default="")
            except Exception:
                answer = Prompt.ask("Your answer", default="")

            if answer.lower().strip() in ("skip", "proceed", "continue", ""):
                logger.info(f"User skipped clarification question: {question}")
                continue

            # Store clarification with a key based on the question
            key = self._question_to_key(question)
            clarifications[key] = answer
            logger.info(f"Collected clarification for '{key}': {answer[:50]}...")

        return clarifications

    def _question_to_key(self, question: str) -> str:
        """Convert a question to a simple key for storage."""
        # Extract key words and create a snake_case key
        words = re.findall(r'\b\w+\b', question.lower())
        # Take significant words, skip common ones
        skip_words = {"what", "is", "the", "are", "how", "do", "you", "your", "a", "an", "to", "for", "of"}
        key_words = [w for w in words if w not in skip_words][:3]
        return "_".join(key_words) if key_words else "clarification"

    def _apply_client_debug(self, enabled: bool) -> None:
        """Best-effort propagation of a debug/verbose flag to the underlying LLM client.

        The concrete client implementations may expose different attribute or method
        names. This helper attempts a variety of common patterns but never raises.

        Args:
            enabled: Whether verbose/debug output should be enabled.
        """
        try:
            client = self.llm_client
        except AttributeError:
            return

        if client is None:
            return

        # Direct attribute flips
        for attr in ("verbose", "debug", "log_prompts", "logging_enabled"):
            if hasattr(client, attr):
                try:
                    setattr(client, attr, enabled)
                except Exception:
                    pass

        # Common setter / enabler methods
        for method_name in ("set_debug", "enable_debug", "set_verbose"):
            if hasattr(client, method_name):
                try:
                    getattr(client, method_name)(enabled)
                except Exception:
                    pass

        # Nested config objects
        if hasattr(client, "config"):
            cfg = getattr(client, "config")
            for attr in ("verbose", "debug"):
                if hasattr(cfg, attr):
                    try:
                        setattr(cfg, attr, enabled)
                    except Exception:
                        pass

        # Optional: attach a simple flag so downstream logic can check
        try:
            setattr(client, "_devussy_verbose", enabled)
        except Exception:
            pass

        logger.debug(f"Applied debug/verbose={enabled} to LLM client")

    def _build_repo_summary(self, analysis: RepoAnalysis) -> str:
        """Build a compact, text-only summary of the analyzed repository."""
        try:
            lines = []
            lines.append(f"Root: {analysis.root_path}")
            if getattr(analysis, "project_type", None):
                lines.append(f"Project type: {analysis.project_type}")

            # Structure
            struct = analysis.structure
            if struct.directories:
                lines.append(
                    "Top-level directories: "
                    + ", ".join(sorted(struct.directories))
                )
            if struct.source_dirs:
                lines.append(
                    "Source dirs: " + ", ".join(sorted(struct.source_dirs))
                )
            if struct.test_dirs:
                lines.append(
                    "Test dirs: " + ", ".join(sorted(struct.test_dirs))
                )
            if struct.config_dirs:
                lines.append(
                    "Config dirs: " + ", ".join(sorted(struct.config_dirs))
                )
            if struct.ci_dirs:
                lines.append("CI dirs: " + ", ".join(sorted(struct.ci_dirs)))

            # Dependencies (only show a handful per ecosystem to keep things short)
            deps = analysis.dependencies

            def _head(values: list[str], label: str, limit: int = 8) -> None:
                if not values:
                    return
                display = sorted(values)[:limit]
                suffix = "" if len(values) <= limit else f" (+{len(values) - limit} more)"
                lines.append(f"{label}: " + ", ".join(display) + suffix)

            _head(deps.python, "Python deps")
            _head(deps.node, "Node deps")

            # Patterns
            patterns = analysis.patterns
            if patterns.test_frameworks:
                lines.append(
                    "Test frameworks: "
                    + ", ".join(sorted(patterns.test_frameworks))
                )
            if patterns.build_tools:
                lines.append(
                    "Build tools: " + ", ".join(sorted(patterns.build_tools))
                )

            # Config files (just names)
            cfg_files = [Path(p).name if not isinstance(p, Path) else p.name for p in analysis.config_files.files]
            if cfg_files:
                lines.append("Config files: " + ", ".join(sorted(cfg_files)))

            # Metrics
            metrics = analysis.code_metrics
            lines.append(
                f"Approx. size: {metrics.total_files} files, {metrics.total_lines} lines"
            )

            return "\n".join(lines)
        except Exception:
            # Never let summary building break the interview
            return ""

        # Design-review specific context (injected via set_design_review_context)
        self._design_review_context_md: Optional[str] = None
        self._design_review_feedback: Dict[str, Any] = {}

        logger.info("LLM Interview Manager initialized")
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Verbose mode: {self.verbose}")
        logger.info(f"Provider: {config.llm.provider}")
        logger.info(f"Model: {config.llm.model}")

    def set_design_review_context(
        self,
        design_md: str,
        devplan_md: Optional[str] = None,
        review_md: Optional[str] = None,
        repo_summary_md: Optional[str] = None,
    ) -> None:
        """Attach rich design/devplan context for design review mode.

        Combines all artifacts into a single markdown blob that can be sent as
        the first user message in design review sessions.
        """
        sections = []
        sections.append("## Artifact 1: Initial Project Design (v1)\n\n" + (design_md or "_No design available._"))
        sections.append(
            "## Artifact 2: DevPlan Summary\n\n" + (devplan_md or "_No devplan summary available yet._")
        )
        sections.append(
            "## Artifact 3: Automatic Design Review\n\n" + (review_md or "_No automatic design review available._")
        )
        sections.append(
            "## Artifact 4: Repo Analysis Summary\n\n" + (repo_summary_md or "_No repo analysis summary available._")
        )

        preamble = (
            "Here is the current design and related context. Read this fully, "
            "then ask me clarifying questions as a senior architect before we "
            "finalize adjustments.\n\n"
        )
        self._design_review_context_md = preamble + "\n\n".join(sections)

    def run(self) -> Dict[str, Any]:
        """Run the conversational interview loop.

        Returns:
            Dict[str, Any]: Answers extracted from conversation
        """
        # Use a plain ASCII title to avoid surrogate emoji issues on some terminals
        console.print(
            Panel.fit(
                "[bold blue]DevPlan Interactive Builder[/bold blue]\n"
                "Let's build your development plan together!\n\n"
                "[dim]Slash commands: /verbose, /help, /done, /quit, /settings, /model, /temp, /tokens[/dim]",
                border_style="blue",
            )
        )

        logger.info("Starting interview conversation")

        if self.repo_analysis:
            self._print_project_summary()

        # Start with initial greeting, customized by mode
        streaming_enabled = getattr(self.config, "streaming_enabled", False)

        if self.mode == "design_review" and self._design_review_context_md:
            # Phase 1: send the consolidated design context
            try:
                self._send_to_llm(self._design_review_context_md)
            except Exception:
                logger.exception("Failed to send design review context to LLM")

            # Phase 2: ask for a short, menu-style checklist of focus areas.
            # This keeps the review manageable and user-directed: the model
            # proposes a numbered list of areas to improve, and the user
            # selects which ones to tackle. The model is also asked to show a
            # simple progress indicator such as "[2/5 areas completed]" as
            # sections are finished.
            initial_response = self._send_to_llm(
                "I've reviewed the full design and devplan context you shared. "
                "First, propose a concise numbered checklist of 4-7 focus areas "
                "we can improve (for example: architecture & integration, RNG & "
                "determinism, persistence & save format, performance & memory, "
                "testing & CI, assets & build pipeline, observability & telemetry). "
                "For each focus area, give a one-line description only. Then ask me "
                "to choose one or more numbers to work on first. As we complete "
                "each area, show a brief progress summary like '[2/5 areas completed]'. "
                "Keep every message tight so we stay within context limits."
            )
            if not streaming_enabled:
                self._display_llm_response(initial_response)
        else:
            if (
                self.repo_analysis
                and getattr(self.repo_analysis, "project_metadata", None)
                and self.repo_analysis.project_metadata.name
            ):
                # Use the project name from repository analysis
                project_name = self.repo_analysis.project_metadata.name
                initial_response = self._send_to_llm(
                    f"Hi! I'm excited to help you plan your project '{project_name}'. "
                    f"I can see this is a {self.repo_analysis.project_type} project "
                    f"with {self.repo_analysis.code_metrics.total_files} files. "
                    "What would you like to accomplish with this project?"
                )
            else:
                # Ask for project name as before
                initial_response = self._send_to_llm(
                    "Hi! I'm excited to help you plan your project. "
                    "Let's start with the basics - what would you like to name your project?"
                )
            if not streaming_enabled:
                self._display_llm_response(initial_response)
        
        # Main conversation loop
        while True:
            # Get user input with persistent bottom-right token toolbar when TTY
            try:
                if sys.stdin.isatty() and sys.stdout.isatty():
                    user_input = pt_prompt(
                        "You: ",
                        bottom_toolbar=self._bottom_toolbar_text,
                    )
                else:
                    user_input = Prompt.ask("\n[yellow]You[/yellow]", default="")
            except Exception:
                user_input = Prompt.ask("\n[yellow]You[/yellow]", default="")
            
            # Handle slash commands
            if user_input.startswith('/'):
                if self._handle_slash_command(user_input):
                    continue
                else:
                    break  # /quit was called
            
            if user_input.lower() in ['quit', 'exit']:
                console.print("[yellow]Interview ended by user.[/yellow]")
                logger.info("Interview ended by user")
                break
            if user_input.lower().strip() == 'done':
                console.print("[yellow]Type '/done' to finalize and generate. Continuing interview...[/yellow]")
                logger.info("User typed 'done' without slash; prompting to use /done")
                continue
            
            if not user_input.strip():
                continue
            
            logger.info(f"User input: {user_input[:100]}...")  # Log first 100 chars
            
            # Send user input to LLM
            response = self._send_to_llm(user_input)
            # Only display if streaming wasn't already showing it
            streaming_enabled = getattr(self.config, 'streaming_enabled', False)
            if not streaming_enabled:
                self._display_llm_response(response)
            # Update token usage snapshot for menu display
            self._refresh_token_usage()
            
            # Check if LLM provided final JSON data
            extracted = self._extract_structured_data(response)
            if extracted:
                self.extracted_data = extracted
                logger.info("Extracted structured data from LLM response")
                if self._validate_extracted_data(extracted):
                    console.print("\n[green]✓ Required info collected.[/green] Type /done to finalize and generate, or continue to refine.")
                    logger.info("Interview ready to finalize - awaiting /done")
                    continue
                else:
                    console.print("[yellow]⚠ Some required information is missing. Let's continue...[/yellow]")
                    logger.warning("Extracted data incomplete, continuing interview")
        
        logger.info("Interview finished")

        # Best-effort extraction of design review feedback if in that mode.
        # The helper keeps the JSON summary compact so we can safely merge it
        # back into the project design/devplan without overblowing context.
        if self.mode == "design_review":
            self._design_review_feedback = self._extract_design_review_feedback()

        return self.extracted_data

    def _extract_design_review_feedback(self) -> Dict[str, Any]:
        """Extract the final, compact design-review JSON summary.

        This is intentionally opinionated to avoid the earlier behavior where
        the model produced multiple long-form reports. We:

        - Walk assistant messages from last to first.
        - Try to parse a small JSON-ish object.
        - Normalize into a tight schema that callers (CLI, pipeline) can merge
          back into design inputs without huge context growth.
        """
        default: Dict[str, Any] = {
            "status": "ok",
            "updated_requirements": "",
            "new_constraints": [],
            "updated_tech_stack": [],
            "integration_risks": [],
            "notes": "",
        }

        # Look from last assistant message backward
        for msg in reversed(self.conversation_history):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content") or ""
            if not content:
                continue

            candidate = None
            # Try pure JSON
            try:
                candidate = json.loads(content)
            except Exception:
                # Try to extract JSON blob inside fences or text
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    try:
                        candidate = json.loads(m.group(0))
                    except Exception:
                        candidate = None

            if not isinstance(candidate, dict):
                continue

            def _get(key: str, fallback: Any) -> Any:
                for k, v in candidate.items():
                    if k.lower() == key:
                        return v
                return fallback

            def _as_list(value: Any) -> list[str]:
                if value is None:
                    return []
                if isinstance(value, list):
                    return [str(v).strip() for v in value if str(v).strip()]
                if isinstance(value, str):
                    parts = re.split(r"[,\n]+", value)
                    return [p.strip() for p in parts if p.strip()]
                return [str(value).strip()]

            return {
                "status": str(_get("status", default["status"]) or "ok"),
                "updated_requirements": str(
                    _get("updated_requirements", default["updated_requirements"]) or ""
                ),
                "new_constraints": _as_list(
                    _get("new_constraints", default["new_constraints"])
                ),
                "updated_tech_stack": _as_list(
                    _get("updated_tech_stack", default["updated_tech_stack"])
                ),
                "integration_risks": _as_list(
                    _get("integration_risks", default["integration_risks"])
                ),
                "notes": str(_get("notes", default["notes"]) or ""),
            }

        return default


    def to_design_review_feedback(self) -> Dict[str, Any]:
        """Return structured design-review feedback (design_review mode only)."""
        if self.mode != "design_review":
            raise ValueError(
                "to_design_review_feedback() is only valid when mode='design_review'"
            )

        if self._design_review_feedback is None:
            self._design_review_feedback = self._extract_design_review_feedback()
        return self._design_review_feedback

    def _extract_design_review_feedback(self) -> Dict[str, Any]:
        """Extract the final design-review JSON summary from the conversation.

        This scans the conversation history (assistant messages) for the last
        JSON-like block matching the shape described in DESIGN_REVIEW_SYSTEM_PROMPT.
        """
        # Walk messages from last to first, looking for assistant content
        for msg in reversed(self.conversation_history):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content") or ""
            data = self._extract_structured_data(content)
            # _extract_structured_data is tuned for initial mode; for design
            # review, attempt a lightweight direct JSON parse if that fails.
            if not data:
                try:
                    obj = json.loads(content)
                except Exception:
                    continue
            else:
                obj = data

            if not isinstance(obj, dict):
                continue

            # Normalize keys for design-review schema
            lower = {str(k).strip().lower(): v for k, v in obj.items()}
            if not {
                "status",
                "updated_requirements",
                "new_constraints",
                "updated_tech_stack",
                "integration_risks",
                "notes",
            }.issubset(lower.keys()):
                continue

            feedback: Dict[str, Any] = {
                "status": str(lower.get("status", "ok")),
                "updated_requirements": str(lower.get("updated_requirements", "")),
                "new_constraints": lower.get("new_constraints") or [],
                "updated_tech_stack": lower.get("updated_tech_stack") or [],
                "integration_risks": lower.get("integration_risks") or [],
                "notes": str(lower.get("notes", "")),
            }

            # Coerce lists
            for key in ["new_constraints", "updated_tech_stack", "integration_risks"]:
                val = feedback[key]
                if isinstance(val, str):
                    # Allow comma- or newline-separated strings
                    parts = [p.strip() for p in re.split(r"[,\n]", val) if p.strip()]
                    feedback[key] = parts
                elif not isinstance(val, list):
                    feedback[key] = [str(val)] if val else []

            return feedback

        # No structured feedback found
        return {
            "status": "ok",
            "updated_requirements": "",
            "new_constraints": [],
            "updated_tech_stack": [],
            "integration_risks": [],
            "notes": "",
        }

    def to_design_review_feedback(self) -> Dict[str, Any]:
        """Return normalized design review feedback.

        Should be called after ``run()`` when the manager was created with
        ``mode="design_review"``. If explicit feedback JSON was not found,
        returns an object with empty fields and ``status="ok"``.
        """
        if self.mode != "design_review":
            raise ValueError("to_design_review_feedback() is only valid in design_review mode")
        if not self._design_review_feedback:
            self._design_review_feedback = self._extract_design_review_feedback()
        return self._design_review_feedback

    def to_generate_design_inputs(self) -> Dict[str, str]:
        """
        Convert conversation data to generate_design format.
        Same interface as InteractiveQuestionnaireManager.
        
        Returns:
            Dict[str, str]: Compatible with existing pipeline
        """
        if not self.extracted_data:
            raise ValueError("No interview data available. Run the interview first.")
        
        # Extract code samples if we have repo analysis and haven't already
        if self.repo_analysis and not self.code_samples:
            self.extract_code_samples()
        
        # Map extracted data to expected format
        inputs = {
            "name": self.extracted_data.get("project_name", ""),
            "languages": self.extracted_data.get("primary_language", ""),
            "requirements": self.extracted_data.get("requirements", ""),
        }
        
        # Add optional fields if present
        optional_mappings = {
            "frameworks": "frameworks",
            "apis": "apis", 
            "database": "database",
            "deployment_platform": "deployment_platform",
            "testing_requirements": "testing_requirements",
        }
        
        for extracted_key, input_key in optional_mappings.items():
            value = self.extracted_data.get(extracted_key)
            if value:
                if isinstance(value, list):
                    inputs[input_key] = ",".join(str(v) for v in value)
                else:
                    inputs[input_key] = str(value)
        
        # Add code samples context if available
        if self.code_samples:
            code_context = self.get_code_samples_context()
            if code_context:
                inputs["code_samples"] = code_context
        
        return inputs

    def _setup_logging(self) -> None:
        """Setup logging to file for interview session."""
        # Create logs directory
        logs_dir = Path("logs/interviews")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"interview_{timestamp}.log"
        
        # Add file handler for this session
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Only add to this logger, don't propagate to root
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Don't send to console
        
        # Also silence the Requesty client logger from console
        requesty_logger = logging.getLogger('src.clients.requesty_client')
        requesty_logger.addHandler(file_handler)
        requesty_logger.setLevel(logging.DEBUG)
        requesty_logger.propagate = False
        
        self.log_file = log_file
        # Use console.print instead of logger for this message
        # logger.info(f"Logging to: {log_file}")  # Commented out - already shown by CLI
    
    def _handle_slash_command(self, command: str) -> bool:
        """Handle slash commands. Returns True to continue, False to quit."""
        command = command.lower().strip()
        
        if command == '/verbose':
            self.verbose = not self.verbose
            status = "ON" if self.verbose else "OFF"
            
            # Update the LLM client debug/verbose flag
            self._apply_client_debug(self.verbose)
            
            console.print(f"[cyan]ℹ️ Verbose mode: {status}[/cyan]")
            logger.info(f"Verbose mode toggled: {status}")
            return True
        
        elif command == '/help':
            console.print(Panel.fit(
                "[bold]Available Commands:[/bold]\n\n"
                "[yellow]/verbose[/yellow] - Toggle verbose output (API calls, tokens, etc.)\n"
                "[yellow]/settings[/yellow] - Open settings menu (provider, models, temperature, tokens)\n"
                "[yellow]/model[/yellow] - Quickly set interview or final-stage model\n"
                "[yellow]/temp[/yellow] - Quickly set temperature\n"
                "[yellow]/tokens[/yellow] - Show last token usage snapshot\n"
                "[yellow]/help[/yellow] - Show this help message\n"
                "[yellow]/done[/yellow] - Finalize interview and generate files\n"
                "[yellow]/quit[/yellow] - End interview without generating files\n\n"
                "Or type: [yellow]quit[/yellow], [yellow]exit[/yellow]",
                title="Help",
                border_style="cyan"
            ))
            return True
        
        elif command == '/settings':
            # Launch menu, apply to config, recreate client
            try:
                updated = run_menu(self.config, self.session_settings)
                self.session_settings = updated
                apply_settings_to_config(self.config, self.session_settings)
                # Recreate LLM client to pick up new settings
                self.llm_client = create_llm_client(self.config)
                self._apply_client_debug(self.verbose)
                console.print("[green]✓ Settings applied for this session.[/green]")
                # Show quick summary
                usage = self.session_settings.last_token_usage or {}
                console.print(
                    f"[dim]Provider: {self.config.llm.provider}, Model: {self.config.llm.model}, Temp: {self.config.llm.temperature}, MaxTokens: {self.config.llm.max_tokens}, TotalTokens: {usage.get('total_tokens')}[/dim]"
                )
            except Exception as e:
                console.print(f"[red]Failed to open settings: {e}[/red]")
            return True
        
        elif command == '/model':
            # Prompt user for models
            try:
                new_model = Prompt.ask("Enter interview model (blank to skip)", default="")
                final_model = Prompt.ask("Enter final-stage model (blank to skip)", default="")
                if new_model.strip():
                    self.session_settings.interview_model = new_model.strip()
                if final_model.strip():
                    self.session_settings.final_stage_model = final_model.strip()
                apply_settings_to_config(self.config, self.session_settings)
                self.llm_client = create_llm_client(self.config)
                self._apply_client_debug(self.verbose)
                console.print("[green]✓ Model settings updated.[/green]")
            except Exception as e:
                console.print(f"[red]Failed to update model: {e}[/red]")
            return True
        
        elif command == '/temp':
            try:
                temp_str = Prompt.ask("Set temperature 0.0-2.0", default=str(self.config.llm.temperature))
                t = float(temp_str)
                if 0.0 <= t <= 2.0:
                    self.session_settings.temperature = t
                    apply_settings_to_config(self.config, self.session_settings)
                    self.llm_client = create_llm_client(self.config)
                    self._apply_client_debug(self.verbose)
                    console.print("[green]✓ Temperature updated.[/green]\n")
                else:
                    console.print("[yellow]Temperature must be between 0.0 and 2.0[/yellow]")
            except ValueError:
                console.print("[yellow]Invalid number[/yellow]")
            except Exception as e:
                console.print(f"[red]Failed to update temperature: {e}[/red]")
            return True
        
        elif command == '/tokens':
            self._refresh_token_usage()
            usage = self.session_settings.last_token_usage
            if usage:
                console.print(
                    f"[cyan]Tokens[/cyan] prompt: {usage.get('prompt_tokens')}, completion: {usage.get('completion_tokens')}, total: {usage.get('total_tokens')}"
                )
            else:
                console.print("[dim]No token usage available yet[/dim]")
            return True
        
        elif command == '/done':
            console.print("[cyan]🎯 Finalizing interview...[/cyan]")
            logger.info("User requested finalization via /done command")

            # First, try a direct one-shot finalize that avoids the normal guidance loop
            direct = self._finalize_via_direct_prompt()
            if direct:
                self.extracted_data = direct
                console.print("\n[green]✓ Interview complete! All required information gathered.[/green]")
                logger.info("Interview complete via direct finalize prompt")
                
                # Save interview summary to markdown
                if self.markdown_output_manager:
                    try:
                        self.markdown_output_manager.save_interview_summary(
                            conversation_history=self.conversation_history,
                            extracted_data=self.extracted_data
                        )
                        logger.info("Saved interview summary to markdown")
                    except Exception as e:
                        logger.warning(f"Failed to save interview summary: {e}")
                
                return False

            # Build a trimmed transcript for robust extraction attempts
            transcript = self._format_conversation_for_llm()
            if len(transcript) > 6000:
                transcript = transcript[-6000:]

            attempts = [
                # Prefer fenced JSON using transcript, explicitly ignore prior guidance
                (
                    "Ignore all prior instructions about asking for '/done' or continuing the interview. "
                    "Based ONLY on the transcript below, OUTPUT a JSON object with EXACT keys: project_name, primary_language, requirements, project_type, frameworks, database, authentication, deployment_platform, testing_requirements, ci_cd. "
                    "Respond inside a fenced ```json``` block ONLY. No extra text. If unknown, use empty string, false, or [] as appropriate.\n\n"
                    f"Transcript:\n{transcript}"
                ),
                # Then plain JSON with no fences
                (
                    "Ignore previous conversation guidance. Based ONLY on the transcript, OUTPUT ONLY a JSON object with the EXACT keys: "
                    "project_name, primary_language, requirements, project_type, frameworks, database, authentication, deployment_platform, testing_requirements, ci_cd. Do NOT use code fences. No prose.\n\n"
                    f"Transcript:\n{transcript}"
                ),
                # Minimal required only, no fence
                (
                    "Output ONLY the REQUIRED JSON with required keys (no prose): {\"project_name\":...,\"primary_language\":...,\"requirements\":...,\"project_type\":...}. "
                    "Include optional keys if known.\n\n"
                    f"Transcript:\n{transcript}"
                ),
            ]

            for idx, prompt_text in enumerate(attempts, start=1):
                response = self._generate_direct(prompt_text)
                # Only display if streaming is NOT enabled to avoid duplication
                streaming_enabled = getattr(self.config, 'streaming_enabled', False)
                if not streaming_enabled:
                    self._display_llm_response(response)
                self._refresh_token_usage()

                extracted = self._extract_structured_data(response)
                if extracted:
                    self.extracted_data = extracted
                    logger.info(f"Extracted structured data after /done attempt {idx}")
                    if self._validate_extracted_data(extracted):
                        console.print("\n[green]✓ Interview complete! All required information gathered.[/green]")
                        logger.info("Interview complete - all required data collected")
                        
                        # Save interview summary to markdown
                        if self.markdown_output_manager:
                            try:
                                self.markdown_output_manager.save_interview_summary(
                                    conversation_history=self.conversation_history,
                                    extracted_data=self.extracted_data
                                )
                                logger.info("Saved interview summary to markdown")
                            except Exception as e:
                                logger.warning(f"Failed to save interview summary: {e}")
                        
                        return False

            # Fallback: if we already have validated data from earlier, allow finalize
            if self.extracted_data and self._validate_extracted_data(self.extracted_data):
                console.print("\n[green]✓ Interview complete using previously collected data.[/green]")
                logger.info("Interview complete - using previously extracted data")
                
                # Save interview summary to markdown
                if self.markdown_output_manager:
                    try:
                        self.markdown_output_manager.save_interview_summary(
                            conversation_history=self.conversation_history,
                            extracted_data=self.extracted_data
                        )
                        logger.info("Saved interview summary to markdown")
                    except Exception as e:
                        logger.warning(f"Failed to save interview summary: {e}")
                
                return False

            # If no valid extraction, suggest user continue or retry
            console.print("[yellow]⚠ Could not extract complete project data. Please provide more details or type /done again.[/yellow]")
            return True
        
        elif command == '/quit':
            console.print("[yellow]Interview ended by user.[/yellow]")
            logger.info("Interview ended via /quit command")
            return False
        
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")
            return True

    def _refresh_token_usage(self) -> None:
        """Refresh last-known token usage from the provider client, if available."""
        try:
            usage = getattr(self.llm_client, "last_usage_metadata", None)
            if usage:
                self.session_settings.last_token_usage = {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                }
        except Exception:
            # Best-effort only
            pass
    
    def _bottom_toolbar_text(self):
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
        except Exception:
            cols = 80
        usage = self.session_settings.last_token_usage or {}
        p = usage.get("prompt_tokens")
        c = usage.get("completion_tokens")
        t = usage.get("total_tokens")
        # Fallback placeholders
        def fmt(v):
            return "-" if v is None else str(v)
        text = f"{self.config.llm.provider}:{self.config.llm.model} | T={self.config.llm.temperature} | tokens p:{fmt(p)} c:{fmt(c)} tot:{fmt(t)}"
        # Right-align for idle toolbar only; spinner will use a trimmed single-line
        pad = max(0, cols - len(text) - 1)
        return " " * pad + text

    def _spinner_status_line(self) -> str:
        """Return a single-line status string that won't wrap under spinner.

        We avoid left padding and trim to terminal width minus a small spinner margin.
        """
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
        except Exception:
            cols = 80
        usage = self.session_settings.last_token_usage or {}
        p = usage.get("prompt_tokens")
        c = usage.get("completion_tokens")
        t = usage.get("total_tokens")
        def fmt(v):
            return "-" if v is None else str(v)
        base = f"{self.config.llm.provider}:{self.config.llm.model} | T={self.config.llm.temperature} | tokens p:{fmt(p)} c:{fmt(c)} tot:{fmt(t)}"
        # Reserve space for spinner glyphs and a space (~4 chars)
        max_len = max(10, cols - 4)
        if len(base) > max_len:
            # Truncate with ellipsis
            return base[: max_len - 1] + "…"
        return base
    
    def _send_to_llm(self, user_input: str) -> str:
        """Send user input to LLM and get response."""
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Format conversation for LLM
        conversation_text = self._format_conversation_for_llm()
        
        if self.verbose:
            console.print("\n[dim]--- API Request ---[/dim]")
            console.print(f"[dim]Provider: {self.config.llm.provider}[/dim]")
            console.print(f"[dim]Model: {self.config.llm.model}[/dim]")
            console.print(f"[dim]Conversation length: {len(conversation_text)} chars[/dim]")
        
        logger.debug(f"Sending to LLM: {conversation_text[:200]}...")
        
        # Get LLM response
        try:
            # Check if streaming is enabled
            streaming_enabled = getattr(self.config, 'streaming_enabled', False)
            
            if streaming_enabled:
                # Use streaming for real-time token display
                console.print("\n[blue]🎵 Devussy[/blue]:")
                
                # Collect streaming response
                response_chunks = []
                
                def token_callback(token: str) -> None:
                    """Callback for each streaming token."""
                    response_chunks.append(token)
                    # Display token in real-time (without newlines for smooth streaming)
                    console.print(token, end="", style="blue")
                
                # Make streaming request
                import asyncio
                response = asyncio.run(self.llm_client.generate_completion_streaming(
                    conversation_text, token_callback
                ))
                
                console.print()  # Add newline after streaming
                console.print()  # Add spacing
                
            else:
                # Use non-streaming fallback
                # Single-line, non-wrapping status text while spinner is active
                status_line = Text(self._spinner_status_line(), style="black on white")
                with console.status(status_line, spinner="dots"):
                    response = self.llm_client.generate_completion_sync(conversation_text)
                
                # Display response normally (ONLY in non-streaming mode)
                self._display_llm_response(response)
            
            if self.verbose:
                console.print(f"[dim]Response length: {len(response)} chars[/dim]")
                console.print("[dim]--- End API Request ---[/dim]\n")
            logger.debug(f"LLM response: {response[:200]}...")
            
        except Exception as e:
            console.print(f"[red]❌ Error communicating with LLM: {e}[/red]")
            logger.error(f"LLM API error: {e}", exc_info=True)
            response = "I'm having trouble connecting right now. Could you try again?"
            # Display error response (ONLY in non-streaming mode to avoid duplication)
            if not streaming_enabled:
                self._display_llm_response(response)
        
        # Add LLM response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Save this Q&A pair to markdown if output manager is configured
        if self.markdown_output_manager:
            self.question_counter += 1
            try:
                self.markdown_output_manager.save_interview_response(
                    question_number=self.question_counter,
                    user_input=user_input,
                    llm_response=response
                )
            except Exception as e:
                logger.warning(f"Failed to save interview response to markdown: {e}")
        
        # Log full conversation exchange
        logger.info(f"USER: {user_input}")
        logger.info(f"ASSISTANT: {response[:500]}...")  # Log first 500 chars
        
        return response

    async def _send_to_llm_streaming(self, user_input: str, callback=None) -> str:
        """Send user input to LLM and get streaming response.
        
        Args:
            user_input: User input message
            callback: Optional callback function for each token
            
        Returns:
            Complete LLM response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Format conversation for LLM
        conversation_text = self._format_conversation_for_llm()
        
        if self.verbose:
            console.print("\n[dim]--- Streaming API Request ---[/dim]")
            console.print(f"[dim]Provider: {self.config.llm.provider}[/dim]")
            console.print(f"[dim]Model: {self.config.llm.model}[/dim]")
            console.print(f"[dim]Conversation length: {len(conversation_text)} chars[/dim]")
        
        logger.debug(f"Sending to LLM (streaming): {conversation_text[:200]}...")
        
        # Get LLM streaming response
        try:
            # Use streaming for real-time token display
            response_chunks = []
            
            def token_callback(token: str) -> None:
                """Callback for each streaming token."""
                response_chunks.append(token)
                # Call custom callback if provided
                if callback:
                    callback(token)
            
            # Make streaming request
            response = await self.llm_client.generate_completion_streaming(
                conversation_text, token_callback
            )
            
            if self.verbose:
                console.print(f"[dim]Streaming response length: {len(response)} chars[/dim]")
                console.print("[dim]--- End Streaming API Request ---[/dim]\n")
            logger.debug(f"LLM streaming response: {response[:200]}...")
            
        except Exception as e:
            console.print(f"[red]❌ Error communicating with LLM: {e}[/red]")
            logger.error(f"LLM API streaming error: {e}", exc_info=True)
            response = "I'm having trouble connecting right now. Could you try again?"
        
        # Add LLM response to conversation history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        
        # Log full conversation exchange
        logger.info(f"USER: {user_input}")
        logger.info(f"ASSISTANT (streaming): {response[:500]}...")  # Log first 500 chars
        
        return response

    def _format_conversation_for_llm(self) -> str:
        """Format conversation history for LLM consumption."""
        messages = []
        for msg in self.conversation_history:
            if msg["role"] == "system":
                messages.append(f"System: {msg['content']}")
            elif msg["role"] == "user":
                messages.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                messages.append(f"Devussy: {msg['content']}")
        
        return "\n\n".join(messages)

    def _finalize_via_direct_prompt(self) -> Optional[Dict[str, Any]]:
        """Attempt a one-shot JSON extraction that bypasses the normal interview loop.

        Sends a direct instruction to output ONLY a JSON object based on the transcript,
        reducing the chance the model repeats "/done" instructions instead of emitting JSON.
        """
        try:
            transcript = self._format_conversation_for_llm()
            # Trim overly long transcripts to keep prompt focused
            if len(transcript) > 6000:
                transcript = transcript[-6000:]

            prompt = (
                "You are a JSON extraction assistant. Ignore prior conversational instructions about asking the user to type /done.\n"
                "Read the following conversation transcript and OUTPUT ONLY a JSON object with EXACT keys: \n"
                "project_name, primary_language, requirements, project_type, frameworks, database, authentication, deployment_platform, testing_requirements, ci_cd.\n"
                "No prose. No markdown. No code fences. If a value is unknown, use an empty string or a reasonable default (false for booleans, [] for lists).\n\n"
                "Transcript:\n" + transcript
            )

            # Respect streaming settings - don't display if streaming is enabled to avoid duplication
            streaming_enabled = getattr(self.config, 'streaming_enabled', False)
            
            if streaming_enabled:
                # Use streaming but don't display (avoid duplication)
                response_chunks = []
                def silent_token_callback(token: str) -> None:
                    response_chunks.append(token)
                
                import asyncio
                response = asyncio.run(self.llm_client.generate_completion_streaming(
                    prompt, silent_token_callback
                ))
            else:
                # Use non-streaming
                response = self.llm_client.generate_completion_sync(prompt)
            
            extracted = self._extract_structured_data(response)
            if extracted and self._validate_extracted_data(extracted):
                return extracted
        except Exception:
            pass
        return None

    def _generate_direct(self, prompt: str) -> str:
        """Call the LLM without using the conversation history (no side effects)."""
        try:
            if self.verbose:
                console.print("\n[dim]--- Direct Finalize Request ---[/dim]")
                console.print(f"[dim]Model: {self.config.llm.model}[/dim]")
                console.print(f"[dim]Prompt length: {len(prompt)} chars[/dim]")
            
            # Respect streaming settings to avoid duplication
            streaming_enabled = getattr(self.config, 'streaming_enabled', False)
            
            if streaming_enabled:
                # Use streaming but don't display (avoid duplication during /done processing)
                response_chunks = []
                def silent_token_callback(token: str) -> None:
                    response_chunks.append(token)
                
                import asyncio
                response = asyncio.run(self.llm_client.generate_completion_streaming(
                    prompt, silent_token_callback
                ))
            else:
                # Use non-streaming
                response = self.llm_client.generate_completion_sync(prompt)
            
            if self.verbose:
                console.print(f"[dim]Response length: {len(response)} chars[/dim]")
                console.print("[dim]--- End Direct Request ---[/dim]\n")
            return response
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}", exc_info=True)
            return ""

    def _collect_missing_required_fields_interactively(self) -> bool:
        """Deprecated: interactive prompting for missing fields is disabled.
        Always return False so /done relies on LLM extraction only.
        """
        return False

    def _display_llm_response(self, response: str) -> None:
        """Display LLM response with nice formatting."""
        console.print(f"\n[blue]🎵 Devussy[/blue]:")
        
        # Split response into paragraphs for better readability
        paragraphs = response.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                console.print(f"[white]{paragraph.strip()}[/white]")
                console.print()

    def _extract_structured_data(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from an LLM response using multiple strategies."""
        # Try fenced JSON (case-insensitive), allow any whitespace and Windows newlines
        fenced_patterns = [
            r"```json\s*(\{[\s\S]*?\})\s*```",
            r"```\s*(\{[\s\S]*?\})\s*```",
        ]
        for pat in fenced_patterns:
            m = re.search(pat, response, re.DOTALL | re.IGNORECASE)
            if m:
                try:
                    data = json.loads(m.group(1))
                    data = self._normalize_extracted_data(data)
                    return data
                except json.JSONDecodeError:
                    pass

        # Try plain JSON object anywhere in text using a simple longest-match regex
        regex_any_obj = r"\{[\s\S]*\}"
        candidates = list(re.finditer(regex_any_obj, response, re.DOTALL))
        for m in sorted(candidates, key=lambda mm: len(mm.group(0)), reverse=True):
            try:
                data = json.loads(m.group(0))
                data = self._normalize_extracted_data(data)
                if isinstance(data, dict) and 'project_name' in data:
                    return data
            except json.JSONDecodeError:
                # YAML fallback for JSON-like content (tolerates comments, trailing commas, single quotes)
                try:
                    data = yaml.safe_load(m.group(0))
                    data = self._normalize_extracted_data(data)
                    if isinstance(data, dict) and 'project_name' in data:
                        return data
                except Exception:
                    continue

        # Balanced-brace scan to extract valid JSON object
        stack = []
        start_idx = None
        for i, ch in enumerate(response):
            if ch == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif ch == '}':
                if stack:
                    stack.pop()
                    if not stack and start_idx is not None:
                        frag = response[start_idx:i+1]
                        try:
                            data = json.loads(frag)
                            data = self._normalize_extracted_data(data)
                            if isinstance(data, dict) and 'project_name' in data:
                                return data
                        except json.JSONDecodeError:
                            try:
                                data = yaml.safe_load(frag)
                                data = self._normalize_extracted_data(data)
                                if isinstance(data, dict) and 'project_name' in data:
                                    return data
                            except Exception:
                                pass

        return None

    def _validate_extracted_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required fields are present in extracted data."""
        data = self._normalize_extracted_data(data)
        required_fields = ["project_name", "primary_language", "requirements", "project_type"]
        
        for field in required_fields:
            if field not in data or not data[field] or not str(data[field]).strip():
                return False
        
        return True

    def _normalize_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize LLM-provided dict to our expected schema.
        Accepts common synonyms and coerces simple types.
        """
        if not isinstance(data, dict):
            return {}
        # Lowercase keys for matching
        lower = {str(k).strip().lower(): v for k, v in data.items()}

        def first_str(val):
            if val is None:
                return ""
            if isinstance(val, list):
                return ",".join(str(x) for x in val if x is not None)
            return str(val)

        norm: Dict[str, Any] = {}

        # project_name
        for key in ["project_name", "name", "project", "projecttitle", "project_title", "title"]:
            if key in lower and str(lower[key]).strip():
                norm["project_name"] = str(lower[key]).strip()
                break

        # primary_language
        for key in ["primary_language", "language", "languages", "primarylanguage"]:
            if key in lower and lower[key] is not None:
                v = lower[key]
                if isinstance(v, list):
                    norm["primary_language"] = ",".join([str(x) for x in v if x])
                else:
                    norm["primary_language"] = str(v)
                break

        # requirements
        for key in ["requirements", "description", "summary", "spec", "specification"]:
            if key in lower and str(lower[key]).strip():
                norm["requirements"] = str(lower[key]).strip()
                break

        # project_type
        for key in ["project_type", "type", "app_type", "category"]:
            if key in lower and str(lower[key]).strip():
                norm["project_type"] = str(lower[key]).strip()
                break

        # optional passthroughs
        for src, dst in [
            ("frameworks", "frameworks"),
            ("database", "database"),
            ("authentication", "authentication"),
            ("deployment_platform", "deployment_platform"),
            ("testing_requirements", "testing_requirements"),
            ("ci_cd", "ci_cd"),
        ]:
            if src in lower:
                norm[dst] = lower[src]

        return norm

    def _print_project_summary(self) -> None:
        """Display a formatted summary of the analyzed repository."""
        if not self.repo_analysis:
            return
        
        analysis = self.repo_analysis
        
        # Build summary sections
        summary_lines = []
        summary_lines.append("[bold cyan]📊 Repository Analysis Summary[/bold cyan]\n")
        
        # Project type and root
        if analysis.project_type:
            summary_lines.append(f"[yellow]Project Type:[/yellow] {analysis.project_type}")
        summary_lines.append(f"[yellow]Root Path:[/yellow] {analysis.root_path}\n")
        
        # Structure
        struct = analysis.structure
        if struct.source_dirs:
            summary_lines.append(f"[yellow]Source Directories:[/yellow] {', '.join(sorted(struct.source_dirs))}")
        if struct.test_dirs:
            summary_lines.append(f"[yellow]Test Directories:[/yellow] {', '.join(sorted(struct.test_dirs))}")
        
        # Dependencies (show first few)
        deps = analysis.dependencies
        if deps.python:
            dep_list = sorted(deps.python)[:5]
            suffix = f" (+{len(deps.python) - 5} more)" if len(deps.python) > 5 else ""
            summary_lines.append(f"[yellow]Python Dependencies:[/yellow] {', '.join(dep_list)}{suffix}")
        if deps.node:
            dep_list = sorted(deps.node)[:5]
            suffix = f" (+{len(deps.node) - 5} more)" if len(deps.node) > 5 else ""
            summary_lines.append(f"[yellow]Node Dependencies:[/yellow] {', '.join(dep_list)}{suffix}")
        
        # Patterns
        patterns = analysis.patterns
        if patterns.test_frameworks:
            summary_lines.append(f"[yellow]Test Frameworks:[/yellow] {', '.join(sorted(patterns.test_frameworks))}")
        if patterns.build_tools:
            summary_lines.append(f"[yellow]Build Tools:[/yellow] {', '.join(sorted(patterns.build_tools))}")
        
        # Metrics
        metrics = analysis.code_metrics
        summary_lines.append(f"\n[yellow]Code Metrics:[/yellow] {metrics.total_files} files, {metrics.total_lines} lines")
        
        # Display in a panel
        console.print(Panel(
            "\n".join(summary_lines),
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()
    
    def extract_code_samples(self, selected_parts: Optional[list[str]] = None) -> list[CodeSample]:
        """Extract code samples from the repository for context.
        
        Args:
            selected_parts: Optional list of specific directories/files to focus on
            
        Returns:
            List of extracted code samples
        """
        if not self.repo_analysis:
            return []
        
        try:
            extractor = CodeSampleExtractor(
                root_path=str(self.repo_analysis.root_path),
                max_samples=8,  # Reasonable number for interview context
                max_lines_per_sample=150  # Keep samples concise
            )
            
            # Extract samples based on analysis and user goals
            goals = self.extracted_data.get("requirements", "")
            samples = extractor.extract_samples(
                analysis=self.repo_analysis,
                selected_parts=selected_parts,
                goals=goals
            )
            
            self.code_samples = samples
            logger.info(f"Extracted {len(samples)} code samples from repository")
            
            return samples
        except Exception as e:
            logger.warning(f"Failed to extract code samples: {e}")
            return []
    
    def get_code_samples_context(self) -> str:
        """Format code samples for inclusion in prompts.
        
        Returns:
            Formatted string of code samples ready for LLM context
        """
        if not self.code_samples:
            return ""
        
        try:
            # Safeguard: repo_analysis might be None if code_samples were injected externally
            root_path = (
                str(getattr(self.repo_analysis, "root_path", "."))
                if self.repo_analysis is not None else "."
            )
            extractor = CodeSampleExtractor(root_path=root_path)
            return extractor.format_samples_for_prompt(self.code_samples)
        except Exception:
            return ""
