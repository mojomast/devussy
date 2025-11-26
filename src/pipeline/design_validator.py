from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from src.interview.complexity_analyzer import ComplexityProfile


@dataclass
class DesignValidationIssue:
    code: str
    message: str
    auto_correctable: bool = True


@dataclass
class DesignValidationReport:
    is_valid: bool
    auto_correctable: bool
    issues: List[DesignValidationIssue]
    checks: Dict[str, bool]


class DesignValidator:
    """Deterministic rule-based validation of a design document.

    This mock-first implementation relies purely on string heuristics and
    simple checks so it can be tested without any LLM calls.
    """

    def validate(
        self,
        design_text: str,
        requirements_text: Optional[str] = None,
        complexity_profile: Optional[ComplexityProfile] = None,
    ) -> DesignValidationReport:
        issues: List[DesignValidationIssue] = []
        checks: Dict[str, bool] = {}

        text = design_text.strip().lower()

        # 1) Consistency check: ensure we do not see obvious contradictory phrases
        inconsistent = "must be monolith" in text and "microservices" in text
        checks["consistency"] = not inconsistent
        if inconsistent:
            issues.append(
                DesignValidationIssue(
                    code="consistency.conflict_monolith_microservices",
                    message="Design mentions both strict monolith and microservices.",
                    auto_correctable=False,
                )
            )

        # 2) Completeness check: require at least minimal sections
        has_arch = "architecture" in text or "architecture overview" in text
        has_data = "data model" in text or "database" in text
        has_testing = "testing" in text
        checks["completeness"] = has_arch and has_data and has_testing
        if not checks["completeness"]:
            issues.append(
                DesignValidationIssue(
                    code="completeness.missing_sections",
                    message="Design is missing architecture, data model, or testing details.",
                    auto_correctable=True,
                )
            )

        # 3) Scope alignment check: very rough heuristic with complexity_profile
        if complexity_profile is not None:
            # For high complexity scores, require mention of scalability or reliability
            requires_scaling = complexity_profile.score >= 7
            mentions_scaling = "scalab" in text or "high availability" in text
            scope_ok = not requires_scaling or mentions_scaling
            checks["scope_alignment"] = scope_ok
            if not scope_ok:
                issues.append(
                    DesignValidationIssue(
                        code="scope_alignment.missing_scalability",
                        message="Complex project without scalability or reliability discussion.",
                        auto_correctable=True,
                    )
                )
        else:
            checks["scope_alignment"] = True

        # 4) Hallucination detection (very simple): flag TODO:API_NAME style markers
        hallucinated = "FAKE_API" in design_text or "<fictional-api>" in design_text
        checks["hallucination"] = not hallucinated
        if hallucinated:
            issues.append(
                DesignValidationIssue(
                    code="hallucination.suspect_api",
                    message="Design appears to reference placeholder or fictional APIs.",
                    auto_correctable=True,
                )
            )

        # 5) Over-engineering detection: small projects using heavy patterns
        over_engineered = False
        if complexity_profile is not None:
            if complexity_profile.score <= 3:
                if "event sourcing" in text or "cqrs" in text or "microservices" in text:
                    over_engineered = True
        checks["over_engineering"] = not over_engineered
        if over_engineered:
            issues.append(
                DesignValidationIssue(
                    code="over_engineering.complex_patterns_for_simple_project",
                    message="Trivial project uses heavy patterns like microservices/CQRS/event sourcing.",
                    auto_correctable=True,
                )
            )

        is_valid = all(checks.values())
        auto_correctable = is_valid or all(issue.auto_correctable for issue in issues)

        return DesignValidationReport(
            is_valid=is_valid,
            auto_correctable=auto_correctable,
            issues=issues,
            checks=checks,
        )
