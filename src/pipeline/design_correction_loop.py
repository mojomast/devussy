from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from src.interview.complexity_analyzer import ComplexityProfile
from .design_validator import DesignValidator, DesignValidationReport
from .llm_sanity_reviewer import LLMSanityReviewer, LLMSanityReviewResult


MAX_ITERATIONS = 3
CONFIDENCE_THRESHOLD = 0.8


@dataclass
class DesignCorrectionResult:
    design_text: str
    validation: DesignValidationReport
    review: LLMSanityReviewResult
    requires_human_review: bool = False
    max_iterations_reached: bool = False


class DesignCorrectionLoop:
    """Pure-Python implementation of the correction loop.

    This mirrors the control flow from the handoff spec but uses a simple
    deterministic "apply_corrections" step so that we can test convergence
    behavior without hitting an LLM.
    """

    def __init__(self) -> None:
        self._validator = DesignValidator()
        self._reviewer = LLMSanityReviewer()

    def run(
        self,
        design_text: str,
        complexity_profile: ComplexityProfile | None = None,
    ) -> DesignCorrectionResult:
        current_design = design_text

        for _ in range(MAX_ITERATIONS):
            validation = self._validator.validate(
                current_design,
                complexity_profile=complexity_profile,
            )
            review = self._reviewer.review(current_design, validation)

            if validation.is_valid and review.confidence > CONFIDENCE_THRESHOLD:
                return DesignCorrectionResult(
                    design_text=current_design,
                    validation=validation,
                    review=review,
                )

            if not validation.auto_correctable:
                return DesignCorrectionResult(
                    design_text=current_design,
                    validation=validation,
                    review=review,
                    requires_human_review=True,
                )

            current_design = self._apply_corrections(current_design, validation, review)

        # Max iterations reached
        final_validation = self._validator.validate(
            current_design,
            complexity_profile=complexity_profile,
        )
        final_review = self._reviewer.review(current_design, final_validation)
        return DesignCorrectionResult(
            design_text=current_design,
            validation=final_validation,
            review=final_review,
            max_iterations_reached=True,
        )

    def _apply_corrections(
        self,
        design_text: str,
        validation: DesignValidationReport,
        review: LLMSanityReviewResult,
    ) -> str:
        """Deterministic placeholder for design corrections.

        For now, this simply appends a small "Corrections applied" footer so
        we can observe that the loop made progress. Real implementations will
        rewrite sections based on validation/report details.
        """

        footer_lines = ["\n\n---", "Corrections applied based on validation checks."]
        for issue in validation.issues:
            if issue.auto_correctable:
                footer_lines.append(f"- Resolved: {issue.code}")

        if review.risks:
            footer_lines.append("- Remaining risks: " + ", ".join(review.risks))

        return design_text + "\n" + "\n".join(footer_lines)
