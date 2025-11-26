from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .design_validator import DesignValidationReport


@dataclass
class LLMSanityReviewResult:
    confidence: float
    notes: str
    risks: List[str]


class LLMSanityReviewer:
    """Mock implementation of an LLM-based semantic reviewer.

    This version does not call any external APIs. It derives a simple
    confidence score and risk list from the validation report only, so it
    can be exercised in unit and integration tests.
    """

    def review(self, design_text: str, validation_report: DesignValidationReport) -> LLMSanityReviewResult:
        if validation_report.is_valid:
            confidence = 0.9
            notes = "Design passes all rule-based checks."
            risks: List[str] = []
        else:
            # Lower confidence if we have non-auto-correctable issues
            non_auto = [i for i in validation_report.issues if not i.auto_correctable]
            if non_auto:
                confidence = 0.5
            else:
                confidence = 0.7
            notes = "Design has validation issues; manual review recommended."
            risks = [issue.code for issue in validation_report.issues]

        return LLMSanityReviewResult(confidence=confidence, notes=notes, risks=risks)
