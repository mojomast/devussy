from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Tuple, List, Any, Optional

from src.interview.complexity_analyzer import ComplexityProfile
from .design_validator import DesignValidator, DesignValidationReport
from .llm_sanity_reviewer import LLMSanityReviewer, LLMSanityReviewResult


MAX_ITERATIONS = 3
CONFIDENCE_THRESHOLD = 0.8


@dataclass
class CorrectionChange:
    """A single correction change made to the design."""
    issue_code: str
    action: str  # "added", "removed", "rewritten", "replaced"
    before: str
    after: str
    explanation: str
    location: str = ""


@dataclass
class DesignCorrectionResult:
    design_text: str
    validation: DesignValidationReport
    review: LLMSanityReviewResult
    requires_human_review: bool = False
    max_iterations_reached: bool = False
    changes_made: List[CorrectionChange] = field(default_factory=list)
    iterations_used: int = 0


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
        all_changes: List[CorrectionChange] = []

        for iteration in range(MAX_ITERATIONS):
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
                    changes_made=all_changes,
                    iterations_used=iteration + 1,
                )

            if not validation.auto_correctable:
                return DesignCorrectionResult(
                    design_text=current_design,
                    validation=validation,
                    review=review,
                    requires_human_review=True,
                    changes_made=all_changes,
                    iterations_used=iteration + 1,
                )

            current_design, changes = self._apply_corrections(current_design, validation, review)
            all_changes.extend(changes)

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
            changes_made=all_changes,
            iterations_used=MAX_ITERATIONS,
        )

    def _apply_corrections(
        self,
        design_text: str,
        validation: DesignValidationReport,
        review: LLMSanityReviewResult,
    ) -> Tuple[str, List[CorrectionChange]]:
        """Deterministic placeholder for design corrections.

        For now, this simply appends a small "Corrections applied" footer so
        we can observe that the loop made progress. Real implementations will
        rewrite sections based on validation/report details.
        """
        changes: List[CorrectionChange] = []
        footer_lines = ["\n\n---", "Corrections applied based on validation checks."]
        
        for issue in validation.issues:
            if issue.auto_correctable:
                footer_lines.append(f"- Resolved: {issue.code}")
                changes.append(CorrectionChange(
                    issue_code=issue.code,
                    action="added",
                    before="",
                    after=f"[Resolved: {issue.code}]",
                    explanation=f"Auto-corrected issue: {issue.message}",
                ))

        if review.risks:
            footer_lines.append("- Remaining risks: " + ", ".join(review.risks))

        return design_text + "\n" + "\n".join(footer_lines), changes


# =============================================================================
# LLM-Powered Design Correction
# =============================================================================

DESIGN_CORRECTION_PROMPT = """IMPORTANT OUTPUT RULES (STRICT):
1. Output ONLY valid JSON.
2. Do NOT wrap the JSON in code fences.
3. Do NOT include any prose before or after the JSON.
4. Do NOT add/remove/rename any fields.
5. Do NOT include comments inside the JSON.
6. Use ONLY double-quoted strings.
7. All booleans must be lowercase true/false.
8. No trailing commas.
9. Follow the schema EXACTLY.

ABOUT THIS TASK:
You are the Design Correction Model. You will repair the design by fixing ONLY the issues provided.

YOU MUST:
- preserve the original design structure
- make minimal corrections required to fix issues
- modify ONLY sections related to the issues list
- keep the corrected design valid Markdown

YOU MUST NOT:
- rewrite unrelated sections
- restructure the architecture
- add new technologies unless replacing hallucinations
- introduce new issues
- invent additional corrections outside the given issues

remaining_issues MUST only contain issues you were explicitly given which could not be auto-corrected.

changes_made MUST contain:
- issue_code
- action ("added", "removed", "rewritten", "replaced")
- before
- after
- explanation
- location (if applicable)

EXPECTED JSON SCHEMA:

{{
  "corrected_design": "<string>",
  "changes_made": [
    {{
      "issue_code": "<string>",
      "action": "<string>",
      "before": "<string>",
      "after": "<string>",
      "explanation": "<string>",
      "location": "<string>"
    }}
  ],
  "remaining_issues": [
    "<string>"
  ],
  "confidence": <number>,
  "notes": "<string>"
}}

YOUR TASK:
Apply corrections iteratively based on the provided issues. Return pure JSON conforming to the schema.

ORIGINAL DESIGN:
{design_text}

ISSUES TO FIX:
{issues_json}

BEGIN NOW."""


@dataclass
class LLMCorrectionResult:
    """Result from LLM-powered design correction."""
    corrected_design: str
    changes_made: List[CorrectionChange]
    remaining_issues: List[str]
    confidence: float
    notes: str


class LLMDesignCorrectionLoop:
    """LLM-powered design correction loop using hardened prompts."""

    def __init__(self, llm_client: Any) -> None:
        self._llm_client = llm_client
        self._validator = DesignValidator()
        self._fallback_loop = DesignCorrectionLoop()

    async def run_with_llm(
        self,
        design_text: str,
        complexity_profile: ComplexityProfile | None = None,
        max_iterations: int = MAX_ITERATIONS,
    ) -> DesignCorrectionResult:
        """Run correction loop using LLM for corrections.
        
        Falls back to simple corrections if LLM fails.
        """
        current_design = design_text
        all_changes: List[CorrectionChange] = []

        for iteration in range(max_iterations):
            validation = self._validator.validate(
                current_design,
                complexity_profile=complexity_profile,
            )
            
            # Use simple reviewer for now (could be upgraded to LLM too)
            from .llm_sanity_reviewer import LLMSanityReviewer
            reviewer = LLMSanityReviewer()
            review = reviewer.review(current_design, validation)

            if validation.is_valid and review.confidence > CONFIDENCE_THRESHOLD:
                return DesignCorrectionResult(
                    design_text=current_design,
                    validation=validation,
                    review=review,
                    changes_made=all_changes,
                    iterations_used=iteration + 1,
                )

            if not validation.auto_correctable:
                return DesignCorrectionResult(
                    design_text=current_design,
                    validation=validation,
                    review=review,
                    requires_human_review=True,
                    changes_made=all_changes,
                    iterations_used=iteration + 1,
                )

            # Use LLM to apply corrections
            try:
                correction_result = await self._correct_with_llm(current_design, validation)
                current_design = correction_result.corrected_design
                all_changes.extend(correction_result.changes_made)
            except Exception as e:
                print(f"LLM correction failed, using fallback: {e}")
                # Fallback to simple corrections
                current_design, changes = self._fallback_loop._apply_corrections(
                    current_design, validation, review
                )
                all_changes.extend(changes)

        # Max iterations reached
        final_validation = self._validator.validate(
            current_design,
            complexity_profile=complexity_profile,
        )
        final_review = reviewer.review(current_design, final_validation)
        return DesignCorrectionResult(
            design_text=current_design,
            validation=final_validation,
            review=final_review,
            max_iterations_reached=True,
            changes_made=all_changes,
            iterations_used=max_iterations,
        )

    async def _correct_with_llm(
        self,
        design_text: str,
        validation: DesignValidationReport,
    ) -> LLMCorrectionResult:
        """Use LLM to correct design issues."""
        # Build issues JSON
        issues_data = [
            {
                "code": issue.code,
                "message": issue.message,
                "auto_correctable": issue.auto_correctable,
            }
            for issue in validation.issues
            if issue.auto_correctable
        ]
        issues_json = json.dumps(issues_data, indent=2)

        prompt = DESIGN_CORRECTION_PROMPT.format(
            design_text=design_text,
            issues_json=issues_json,
        )

        response = await self._llm_client.generate_completion(prompt)
        return self._parse_llm_response(response)

    def _parse_llm_response(self, response: str) -> LLMCorrectionResult:
        """Parse LLM JSON response into structured result."""
        # Clean up response - remove potential code fences
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        # Parse changes
        changes = [
            CorrectionChange(
                issue_code=change.get("issue_code", ""),
                action=change.get("action", ""),
                before=change.get("before", ""),
                after=change.get("after", ""),
                explanation=change.get("explanation", ""),
                location=change.get("location", ""),
            )
            for change in data.get("changes_made", [])
        ]

        return LLMCorrectionResult(
            corrected_design=str(data.get("corrected_design", "")),
            changes_made=changes,
            remaining_issues=data.get("remaining_issues", []),
            confidence=float(data.get("confidence", 0.8)),
            notes=str(data.get("notes", "")),
        )
