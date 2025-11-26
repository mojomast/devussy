from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Any, Mapping, Optional

from .design_validator import DesignValidationReport


@dataclass
class LLMSanityReviewResult:
    confidence: float
    notes: str
    risks: List[str]


@dataclass
class HallucinationIssue:
    type: str
    text: str
    note: str


@dataclass
class ScopeAlignment:
    score: float
    missing_requirements: List[str] = field(default_factory=list)
    over_engineered: List[str] = field(default_factory=list)
    under_engineered: List[str] = field(default_factory=list)


@dataclass
class Risk:
    severity: str
    category: str
    description: str
    mitigation: str


@dataclass
class LLMSanityReviewResultDetailed:
    """Detailed result from LLM-powered sanity review."""
    confidence: float
    overall_assessment: str  # "sound", "sound_with_concerns", "problematic"
    coherence_score: float
    coherence_notes: str
    hallucination_passed: bool
    hallucination_issues: List[HallucinationIssue] = field(default_factory=list)
    scope_alignment: Optional[ScopeAlignment] = None
    risks: List[Risk] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    summary: str = ""


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


# =============================================================================
# LLM-Powered Sanity Review
# =============================================================================

SANITY_REVIEW_PROMPT = """IMPORTANT OUTPUT RULES (STRICT):
1. Output ONLY valid JSON.
2. Do NOT wrap the JSON in code fences.
3. Do NOT include any prose before or after the JSON.
4. Do NOT add/remove/rename any fields.
5. Do NOT include comments inside the JSON.
6. Use ONLY double-quoted strings.
7. All booleans must be lowercase true/false.
8. No trailing commas.
9. Follow the schema EXACTLY.
10. Do NOT rewrite or modify the provided design text.

ABOUT THIS TASK:
You are the Sanity Review Model. You must evaluate a design document for coherence, hallucinations, scope alignment, and risks.

You MUST NOT:
- rewrite or correct the design text
- include unrelated risks
- add features not based on provided content
- generate more than allowed items

LIMITS:
hallucination_check.issues → max 10 items  
risks → max 8 items  
suggestions → max 10 items  

overall_assessment MUST be one of:
- "sound"
- "sound_with_concerns"
- "problematic"

hallucination_check.passed MUST be boolean.

EXPECTED JSON SCHEMA (MUST MATCH EXACTLY):

{{
  "confidence": <number>,
  "overall_assessment": "<sound|sound_with_concerns|problematic>",
  "coherence": {{
    "score": <number>,
    "notes": "<string>"
  }},
  "hallucination_check": {{
    "passed": <boolean>,
    "issues": [
      {{
        "type": "<string>",
        "text": "<string>",
        "note": "<string>"
      }}
    ]
  }},
  "scope_alignment": {{
    "score": <number>,
    "missing_requirements": [
      "<string>"
    ],
    "over_engineered": [
      "<string>"
    ],
    "under_engineered": [
      "<string>"
    ]
  }},
  "risks": [
    {{
      "severity": "<string>",
      "category": "<string>",
      "description": "<string>",
      "mitigation": "<string>"
    }}
  ],
  "suggestions": [
    "<string>"
  ],
  "summary": "<string>"
}}

YOUR TASK:
Review the provided design text and validation report. Produce JSON in the exact structure above.

DESIGN DOCUMENT:
{design_text}

VALIDATION REPORT:
{validation_json}

BEGIN NOW."""


class LLMSanityReviewerWithLLM:
    """LLM-powered sanity reviewer using hardened prompts."""

    def __init__(self, llm_client: Any) -> None:
        self._llm_client = llm_client
        self._fallback_reviewer = LLMSanityReviewer()

    async def review_with_llm(
        self,
        design_text: str,
        validation_report: DesignValidationReport,
    ) -> LLMSanityReviewResultDetailed:
        """Review design using LLM with hardened prompt.
        
        Falls back to simple review if LLM fails.
        """
        # Build validation JSON for prompt
        validation_data = {
            "is_valid": validation_report.is_valid,
            "auto_correctable": validation_report.auto_correctable,
            "checks": validation_report.checks,
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "auto_correctable": issue.auto_correctable,
                }
                for issue in validation_report.issues
            ],
        }
        validation_json = json.dumps(validation_data, indent=2)

        prompt = SANITY_REVIEW_PROMPT.format(
            design_text=design_text,
            validation_json=validation_json,
        )

        try:
            response = await self._llm_client.generate_completion(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            # Fallback to simple review
            print(f"LLM sanity review failed, using fallback: {e}")
            simple_result = self._fallback_reviewer.review(design_text, validation_report)
            return LLMSanityReviewResultDetailed(
                confidence=simple_result.confidence,
                overall_assessment="sound" if simple_result.confidence > 0.8 else "sound_with_concerns",
                coherence_score=0.8 if validation_report.is_valid else 0.5,
                coherence_notes=simple_result.notes,
                hallucination_passed=True,
                summary=f"Fallback review: {simple_result.notes}",
            )

    def _parse_llm_response(self, response: str) -> LLMSanityReviewResultDetailed:
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

        # Parse coherence
        coherence = data.get("coherence", {})
        
        # Parse hallucination check
        hallucination = data.get("hallucination_check", {})
        hallucination_issues = [
            HallucinationIssue(
                type=issue.get("type", ""),
                text=issue.get("text", ""),
                note=issue.get("note", ""),
            )
            for issue in hallucination.get("issues", [])[:10]  # Max 10
        ]

        # Parse scope alignment
        scope_data = data.get("scope_alignment", {})
        scope_alignment = ScopeAlignment(
            score=float(scope_data.get("score", 0.8)),
            missing_requirements=scope_data.get("missing_requirements", []),
            over_engineered=scope_data.get("over_engineered", []),
            under_engineered=scope_data.get("under_engineered", []),
        )

        # Parse risks
        risks = [
            Risk(
                severity=risk.get("severity", "medium"),
                category=risk.get("category", "unknown"),
                description=risk.get("description", ""),
                mitigation=risk.get("mitigation", ""),
            )
            for risk in data.get("risks", [])[:8]  # Max 8
        ]

        # Validate overall_assessment
        overall = data.get("overall_assessment", "sound_with_concerns")
        if overall not in ("sound", "sound_with_concerns", "problematic"):
            overall = "sound_with_concerns"

        return LLMSanityReviewResultDetailed(
            confidence=float(data.get("confidence", 0.8)),
            overall_assessment=overall,
            coherence_score=float(coherence.get("score", 0.8)),
            coherence_notes=str(coherence.get("notes", "")),
            hallucination_passed=bool(hallucination.get("passed", True)),
            hallucination_issues=hallucination_issues,
            scope_alignment=scope_alignment,
            risks=risks,
            suggestions=data.get("suggestions", [])[:10],  # Max 10
            summary=str(data.get("summary", "")),
        )
