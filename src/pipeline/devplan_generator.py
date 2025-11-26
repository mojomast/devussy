from __future__ import annotations

from typing import List

from src.interview.complexity_analyzer import ComplexityProfile
from src.models import DevPlan, DevPlanPhase


class AdaptiveDevPlanGenerator:
    """Mock adaptive devplan generator.

    This generator creates a deterministic ``DevPlan`` from a
    ``ComplexityProfile`` without calling any LLMs. It is intended for
    exercising the adaptive pipeline control flow and for unit tests.
    """

    def generate(self, profile: ComplexityProfile, project_label: str = "project") -> DevPlan:
        """Generate a mock devplan based on the given profile.

        Args:
            profile: Complexity profile with phase count and depth.
            project_label: Human-readable label for the project.

        Returns:
            ``DevPlan`` instance with phases but no detailed steps.
        """
        phase_count = max(1, int(profile.estimated_phase_count or 1))
        names = self._phase_names_for_count(phase_count)

        phases: list[DevPlanPhase] = []
        for idx, name in enumerate(names, start=1):
            phases.append(
                DevPlanPhase(
                    number=idx,
                    title=f"Phase {idx}: {name}",
                    description=None,
                    steps=[],
                )
            )

        summary = (
            f"Adaptive devplan for {project_label} with {phase_count} phases "
            f"(depth={profile.depth_level})."
        )
        return DevPlan(phases=phases, summary=summary)

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
