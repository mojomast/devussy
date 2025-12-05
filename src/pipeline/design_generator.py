from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.interview.complexity_analyzer import ComplexityProfile


def _get_templates_dir() -> Path:
    """Get the templates directory path."""
    return Path(__file__).resolve().parents[2] / "templates"


class AdaptiveDesignGenerator:
    """Adaptive design generator with complexity-aware output.

    This implementation can operate in two modes:
    1. Mock mode (default): Produces deterministic markdown without LLM calls
    2. Template mode: Uses Jinja templates for structured output

    The size and level of detail vary based on the provided ``ComplexityProfile``.
    """

    def __init__(self, use_templates: bool = False):
        """Initialize the generator.

        Args:
            use_templates: If True, use Jinja templates for output generation.
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
    ) -> str:
        """Generate a design document for the given complexity profile.

        Args:
            profile: Complexity profile computed from interview data.
            project_label: Human-readable label for the project.
            **context: Additional context variables for template rendering.

        Returns:
            Markdown string describing the system design.
        """
        if self.use_templates:
            return self._generate_from_template(profile, project_label, **context)
        return self._generate_mock(profile, project_label)

    def _generate_from_template(
        self,
        profile: ComplexityProfile,
        project_label: str,
        **context: Any,
    ) -> str:
        """Generate design using Jinja templates."""
        template = self._env.get_template("design/adaptive_design.jinja2")

        template_context = {
            "complexity_profile": {
                "complexity_score": profile.score,
                "estimated_phases": profile.estimated_phase_count,
                "depth_level": profile.depth_level,
                "project_scale": self._get_project_scale(profile.score),
                "risk_factors": getattr(profile, "risk_factors", []),
                "confidence": profile.confidence,
            },
            "project_name": project_label,
            **context,
        }

        return template.render(**template_context)

    def _get_project_scale(self, score: float) -> str:
        """Map complexity score to project scale label."""
        if score <= 3:
            return "trivial"
        elif score <= 7:
            return "simple"
        elif score <= 12:
            return "medium"
        elif score <= 16:
            return "complex"
        else:
            return "enterprise"

    def _generate_mock(self, profile: ComplexityProfile, project_label: str) -> str:
        """Generate a mock design document (original implementation).

        Args:
            profile: Complexity profile computed from interview data.
            project_label: Human-readable label for the project.

        Returns:
            Markdown string describing a mock system design.
        """
        header = f"# Adaptive Design for {project_label}\n\n"

        base_sections: list[str] = [
            "## Architecture\n\n"
            "High-level architecture for the project, focused on core components.",
            "## Data Model\n\n"
            "Overview of key entities and relationships.",
            "## Testing\n\n"
            "Strategy for unit and integration tests.",
        ]

        if profile.depth_level == "minimal":
            body = "\n\n".join(base_sections)
        elif profile.depth_level == "standard":
            standard_sections: list[str] = base_sections + [
                "## Deployment\n\n"
                "Basic deployment approach and environments.",
                "## Dependencies\n\n"
                "Important libraries, services, and integration points.",
            ]
            body = "\n\n".join(standard_sections)
        else:
            detailed_sections: list[str] = base_sections + [
                "## Deployment\n\n"
                "Detailed deployment topology, environments, and rollout strategy.",
                "## Security\n\n"
                "Authentication, authorization, and data protection measures.",
                "## Scalability & Reliability\n\n"
                "Approach to horizontal scaling, resilience, and observability.",
                "## CI/CD & Tooling\n\n"
                "Pipelines, checks, and automation supporting the project.",
            ]
            body = "\n\n".join(detailed_sections)

        footer = (
            "\n\n---\n"
            f"Complexity score: {profile.score:.1f} "
            f"| Estimated phases: {profile.estimated_phase_count} "
            f"| Depth: {profile.depth_level} "
            f"| Confidence: {profile.confidence:.2f}\n"
        )

        return header + body + footer
