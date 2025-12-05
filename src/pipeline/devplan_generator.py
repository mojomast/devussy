from __future__ import annotations

from pathlib import Path
from typing import Any, List

from jinja2 import Environment, FileSystemLoader

from src.interview.complexity_analyzer import ComplexityProfile
from src.models import DevPlan, DevPlanPhase


def _get_templates_dir() -> Path:
    """Get the templates directory path."""
    return Path(__file__).resolve().parents[2] / "templates"


class AdaptiveDevPlanGenerator:
    """Adaptive devplan generator with complexity-aware phase generation.

    This generator creates a ``DevPlan`` from a ``ComplexityProfile``.
    It supports both mock mode (deterministic output) and template mode
    (Jinja templates for phase rendering).
    """

    def __init__(self, use_templates: bool = False):
        """Initialize the generator.

        Args:
            use_templates: If True, use Jinja templates for phase rendering.
        """
        self.use_templates = use_templates
        if use_templates:
            templates_dir = _get_templates_dir()
            self._env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def generate(
        self,
        profile: ComplexityProfile,
        project_label: str = "project",
        **context: Any,
    ) -> DevPlan:
        """Generate a devplan based on the given profile.

        Args:
            profile: Complexity profile with phase count and depth.
            project_label: Human-readable label for the project.
            **context: Additional context variables for template rendering.

        Returns:
            ``DevPlan`` instance with phases.
        """
        phase_count = max(1, int(profile.estimated_phase_count or 1))
        names = self._phase_names_for_count(phase_count)

        phases: list[DevPlanPhase] = []
        for idx, name in enumerate(names, start=1):
            description = self._generate_phase_description(
                phase_number=idx,
                phase_name=name,
                depth_level=profile.depth_level,
                **context,
            )
            phases.append(
                DevPlanPhase(
                    number=idx,
                    title=f"Phase {idx}: {name}",
                    description=description,
                    steps=[],
                )
            )

        summary = (
            f"Adaptive devplan for {project_label} with {phase_count} phases "
            f"(depth={profile.depth_level})."
        )
        return DevPlan(phases=phases, summary=summary)

    def _generate_phase_description(
        self,
        phase_number: int,
        phase_name: str,
        depth_level: str,
        **context: Any,
    ) -> str | None:
        """Generate phase description based on depth level.

        Args:
            phase_number: The phase number (1-indexed).
            phase_name: The name of the phase.
            depth_level: "minimal", "standard", or "detailed".
            **context: Additional context for template rendering.

        Returns:
            Phase description string, or None for minimal mock mode.
        """
        if not self.use_templates:
            # Mock mode: minimal descriptions
            if depth_level == "minimal":
                return None
            elif depth_level == "standard":
                return f"Implement {phase_name.lower()} functionality."
            else:
                return (
                    f"Comprehensive implementation of {phase_name.lower()} "
                    f"with full testing, documentation, and quality checks."
                )

        # Template mode: use appropriate template
        template_name = f"devplan/phase_{depth_level}.jinja2"
        try:
            template = self._env.get_template(template_name)
        except Exception:
            # Fall back to standard template
            template = self._env.get_template("devplan/phase_standard.jinja2")

        template_context = {
            "phase_number": phase_number,
            "phase_name": phase_name,
            "phase_description": f"Implement {phase_name.lower()} functionality.",
            "phase_goal": f"Complete all {phase_name.lower()} work items.",
            "tasks": self._generate_tasks_for_phase(phase_name, depth_level),
            "test_strategy": self._generate_test_strategy(depth_level),
            "acceptance_criteria": self._generate_acceptance_criteria(phase_name),
            **context,
        }

        return template.render(**template_context)

    def _generate_tasks_for_phase(self, phase_name: str, depth_level: str) -> list[Any]:
        """Generate task list for a phase based on depth level."""
        base_tasks = [
            f"Set up {phase_name.lower()} environment",
            f"Implement core {phase_name.lower()} functionality",
            f"Write tests for {phase_name.lower()}",
        ]

        if depth_level == "minimal":
            return base_tasks[:2]
        elif depth_level == "standard":
            return base_tasks + [f"Document {phase_name.lower()} implementation"]
        else:
            return [
                {
                    "title": task,
                    "description": f"Complete task: {task}",
                    "subtasks": [
                        f"Research best practices for {task.split()[-1]}",
                        "Implement solution",
                        "Write unit tests",
                        "Update documentation",
                    ],
                }
                for task in base_tasks
            ] + [
                {
                    "title": f"Quality checks for {phase_name}",
                    "description": "Run all quality checks and fix issues",
                    "subtasks": [
                        "Run linters (black, flake8)",
                        "Run type checker (mypy)",
                        "Verify test coverage >= 80%",
                        "Review and address code review feedback",
                    ],
                }
            ]

    def _generate_test_strategy(self, depth_level: str) -> str:
        """Generate testing strategy based on depth level."""
        if depth_level == "minimal":
            return "Verify functionality works as expected"
        elif depth_level == "standard":
            return (
                "Write unit tests for core functionality. "
                "Run integration tests for component interactions."
            )
        else:
            return (
                "Implement comprehensive testing:\n"
                "- Unit tests for all functions and methods\n"
                "- Integration tests for component interactions\n"
                "- End-to-end tests for critical user flows\n"
                "- Performance benchmarks for key operations\n"
                "- Security testing for sensitive operations"
            )

    def _generate_acceptance_criteria(self, phase_name: str) -> list[str]:
        """Generate acceptance criteria for a phase."""
        return [
            f"All {phase_name.lower()} tasks completed",
            "Tests pass with acceptable coverage",
            "Code reviewed and approved",
            "Documentation updated",
        ]

    def _phase_names_for_count(self, phase_count: int) -> List[str]:
        """Return human-friendly phase names for the requested count.

        The mapping loosely follows the naming conventions in the devplan
        but falls back to generic labels when the requested count does not
        exactly match the canonical sets.
        """
        # Canonical sequences for common counts
        if phase_count == 3:
            base = ["Foundation", "Implementation", "Polish"]
        elif phase_count == 5:
            base = [
                "Foundation",
                "Core",
                "Integration",
                "Testing",
                "Deployment",
            ]
        elif phase_count == 7:
            base = [
                "Planning",
                "Foundation",
                "Core",
                "Features",
                "Integration",
                "Testing",
                "Deployment",
            ]
        else:
            base = [
                "Planning",
                "Foundation",
                "Core",
                "Auth & Security",
                "Data Layer",
                "API / Services",
                "Frontend / UX",
                "Integration & Hardening",
                "Testing",
                "Deployment",
                "Monitoring",
                "Polish",
                "Post-Launch",
                "Continuous Improvement",
                "Operational Readiness",
            ]

        if phase_count <= len(base):
            return base[:phase_count]

        names = list(base)
        generic_idx = 1
        while len(names) < phase_count:
            names.append(f"Additional Work {generic_idx}")
            generic_idx += 1
        return names

    def render_phase_markdown(
        self,
        phase: DevPlanPhase,
        depth_level: str = "standard",
        **context: Any,
    ) -> str:
        """Render a single phase to markdown using templates.

        Args:
            phase: The phase to render.
            depth_level: "minimal", "standard", or "detailed".
            **context: Additional context for template rendering.

        Returns:
            Markdown string for the phase.
        """
        if not self.use_templates:
            # Simple markdown fallback
            lines = [f"## {phase.title}"]
            if phase.description:
                lines.append(f"\n{phase.description}")
            return "\n".join(lines)

        template_name = f"devplan/phase_{depth_level}.jinja2"
        try:
            template = self._env.get_template(template_name)
        except Exception:
            template = self._env.get_template("devplan/phase_standard.jinja2")

        template_context = {
            "phase_number": phase.number,
            "phase_name": phase.title.replace(f"Phase {phase.number}: ", ""),
            "phase_description": phase.description,
            "tasks": [step.title if hasattr(step, "title") else str(step) for step in phase.steps],
            **context,
        }

        return template.render(**template_context)
