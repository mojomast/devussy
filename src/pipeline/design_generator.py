from __future__ import annotations

from typing import Any

from src.interview.complexity_analyzer import ComplexityProfile


class AdaptiveDesignGenerator:
    """Mock adaptive design generator.

    This implementation is intentionally LLM-free. It produces a simple
    markdown design document whose size and level of detail vary based on
    the provided ``ComplexityProfile``. It is used by the mock adaptive
    pipeline to exercise control flow before real LLM integration.
    """

    def generate(self, profile: ComplexityProfile, project_label: str = "project") -> str:
        """Generate a mock design document for the given complexity profile.

        Args:
            profile: Complexity profile computed from interview data.
            project_label: Human-readable label for the project (e.g. project type).

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
