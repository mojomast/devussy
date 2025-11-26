from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal, Mapping, Any, List, Optional

ProjectTypeBucket = Literal["cli_tool", "library", "api", "web_app", "saas"]
TechnicalComplexityBucket = Literal[
    "simple_crud",
    "auth_db",
    "realtime",
    "ml_ai",
    "multi_region",
]
IntegrationBucket = Literal[
    "standalone",
    "1_2_services",
    "3_5_services",
    "6_plus_services",
]
TeamSizeBucket = Literal["solo", "2_3", "4_6", "7_plus"]
DepthLevel = Literal["minimal", "standard", "detailed"]


PROJECT_TYPE_SCORE: Mapping[ProjectTypeBucket, int] = {
    "cli_tool": 1,
    "library": 2,
    "api": 3,
    "web_app": 4,
    "saas": 5,
}

TECHNICAL_COMPLEXITY_SCORE: Mapping[TechnicalComplexityBucket, int] = {
    "simple_crud": 1,
    "auth_db": 2,
    "realtime": 3,
    "ml_ai": 4,
    "multi_region": 5,
}

INTEGRATION_SCORE: Mapping[IntegrationBucket, int] = {
    "standalone": 0,
    "1_2_services": 1,
    "3_5_services": 2,
    "6_plus_services": 3,
}

TEAM_SIZE_MULTIPLIER: Mapping[TeamSizeBucket, float] = {
    "solo": 0.5,
    "2_3": 1.0,
    "4_6": 1.2,
    "7_plus": 1.5,
}


@dataclass
class ComplexityProfile:
    project_type_bucket: ProjectTypeBucket
    technical_complexity_bucket: TechnicalComplexityBucket
    integration_bucket: IntegrationBucket
    team_size_bucket: TeamSizeBucket

    score: float
    estimated_phase_count: int
    depth_level: DepthLevel
    confidence: float


def estimate_phase_count(complexity_score: float) -> int:
    if complexity_score <= 3:
        return 3
    if complexity_score <= 7:
        return 5
    if complexity_score <= 12:
        return 7
    return int(min(9 + (complexity_score - 12) // 2, 15))


class ComplexityAnalyzer:
    def analyze(self, interview_data: Mapping[str, Any]) -> ComplexityProfile:
        project_type_bucket = self._infer_project_type_bucket(interview_data)
        technical_complexity_bucket = self._infer_technical_complexity_bucket(
            interview_data
        )
        integration_bucket = self._infer_integration_bucket(interview_data)
        team_size_bucket = self._infer_team_size_bucket(interview_data)

        base = (
            PROJECT_TYPE_SCORE[project_type_bucket]
            + TECHNICAL_COMPLEXITY_SCORE[technical_complexity_bucket]
            + INTEGRATION_SCORE[integration_bucket]
        )
        multiplier = TEAM_SIZE_MULTIPLIER[team_size_bucket]
        score = base * multiplier

        estimated_phase_count = estimate_phase_count(score)
        depth_level = self._derive_depth_level(score)
        confidence = self._estimate_confidence(
            project_type_bucket,
            technical_complexity_bucket,
            integration_bucket,
            team_size_bucket,
        )

        return ComplexityProfile(
            project_type_bucket=project_type_bucket,
            technical_complexity_bucket=technical_complexity_bucket,
            integration_bucket=integration_bucket,
            team_size_bucket=team_size_bucket,
            score=score,
            estimated_phase_count=estimated_phase_count,
            depth_level=depth_level,
            confidence=confidence,
        )

    def _infer_project_type_bucket(self, interview_data: Mapping[str, Any]) -> ProjectTypeBucket:
        project_type_raw = str(interview_data.get("project_type", "")).lower()
        if "cli" in project_type_raw:
            return "cli_tool"
        if any(word in project_type_raw for word in ("library", "sdk")):
            return "library"
        if "api" in project_type_raw:
            return "api"
        if any(word in project_type_raw for word in ("web", "frontend", "spa")):
            return "web_app"
        if any(word in project_type_raw for word in ("saas", "platform", "multi-tenant")):
            return "saas"
        return "web_app"

    def _infer_technical_complexity_bucket(
        self, interview_data: Mapping[str, Any]
    ) -> TechnicalComplexityBucket:
        requirements = str(interview_data.get("requirements", "")).lower()
        frameworks = str(interview_data.get("frameworks", "")).lower()

        if any(keyword in requirements for keyword in ("machine learning", "ml", "ai")):
            return "ml_ai"
        if any(keyword in requirements for keyword in ("realtime", "real-time", "websocket", "streaming")):
            return "realtime"
        if any(keyword in requirements for keyword in ("multi region", "multi-region", "global")):
            return "multi_region"
        if any(keyword in requirements for keyword in ("auth", "authentication", "login")):
            return "auth_db"

        if any(keyword in frameworks for keyword in ("django", "rails", "laravel")):
            return "auth_db"

        return "simple_crud"

    def _infer_integration_bucket(self, interview_data: Mapping[str, Any]) -> IntegrationBucket:
        apis_raw = interview_data.get("apis")
        if isinstance(apis_raw, str):
            apis = [a for a in (p.strip() for p in apis_raw.split(",")) if a]
        elif isinstance(apis_raw, list):
            apis = [str(a).strip() for a in apis_raw if str(a).strip()]
        else:
            apis = []

        count = len(apis)
        if count == 0:
            return "standalone"
        if count <= 2:
            return "1_2_services"
        if count <= 5:
            return "3_5_services"
        return "6_plus_services"

    def _infer_team_size_bucket(self, interview_data: Mapping[str, Any]) -> TeamSizeBucket:
        raw = str(interview_data.get("team_size", "")).strip().lower()
        if not raw:
            return "solo"

        if raw.isdigit():
            size = int(raw)
        else:
            digits = [int(s) for s in raw.split("-") if s.isdigit()]
            size = digits[-1] if digits else 1

        if size <= 1:
            return "solo"
        if size <= 3:
            return "2_3"
        if size <= 6:
            return "4_6"
        return "7_plus"

    def _derive_depth_level(self, score: float) -> DepthLevel:
        if score <= 3:
            return "minimal"
        if score <= 7:
            return "standard"
        return "detailed"

    def _estimate_confidence(
        self,
        project_type_bucket: ProjectTypeBucket,
        technical_complexity_bucket: TechnicalComplexityBucket,
        integration_bucket: IntegrationBucket,
        team_size_bucket: TeamSizeBucket,
    ) -> float:
        buckets = [
            project_type_bucket,
            technical_complexity_bucket,
            integration_bucket,
            team_size_bucket,
        ]
        inferred_count = sum(1 for b in buckets if b is not None)
        return max(0.5, min(1.0, 0.5 + 0.125 * inferred_count))


# =============================================================================
# LLM-Powered Complexity Analysis
# =============================================================================

COMPLEXITY_ANALYSIS_PROMPT = """IMPORTANT OUTPUT RULES (STRICT):
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
You are the Complexity Analysis Model. You will review the full interview data to produce a structured complexity profile describing the difficulty, scope, and risks of the project.

YOU MUST NOT:
- invent features not in the requirements
- contradict the provided data
- hallucinate unknown metrics
- produce non-deterministic field names
- output any text outside JSON

ALLOWED VALUES:
depth_level MUST be one of:
  - "minimal"
  - "standard"
  - "detailed"

complexity_score MUST be a number between 0 and 20.
confidence MUST be a float between 0 and 1.

follow_up_questions MUST be questions seeking missing or ambiguous project info.
hidden_risks MUST identify domain-specific risks not explicitly stated.

EXPECTED JSON SCHEMA (MUST MATCH EXACTLY):

{{
  "complexity_score": <number>,
  "estimated_phase_count": <integer>,
  "depth_level": "<minimal|standard|detailed>",
  "confidence": <number>,
  "rationale": "<string>",
  "complexity_factors": {{
    "integrations": "<string>",
    "security_compliance": "<string>",
    "data_privacy": "<string>",
    "realtime_communication": "<string>",
    "multi_tenancy": "<string>",
    "scale": "<string>",
    "architecture": "<string>",
    "team_and_timeline": "<string>",
    "domain_complexity": "<string>",
    "operational_overhead": "<string>"
  }},
  "follow_up_questions": [
    "<string>"
  ],
  "hidden_risks": [
    "<string>"
  ]
}}

YOUR TASK:
Analyze the provided interview data and return JSON in the exact schema above, with no extra fields.

INTERVIEW DATA:
{interview_json}

BEGIN NOW."""


@dataclass
class LLMComplexityResult:
    """Result from LLM-powered complexity analysis."""
    complexity_score: float
    estimated_phase_count: int
    depth_level: DepthLevel
    confidence: float
    rationale: str = ""
    complexity_factors: Mapping[str, str] = field(default_factory=dict)
    follow_up_questions: List[str] = field(default_factory=list)
    hidden_risks: List[str] = field(default_factory=list)


class LLMComplexityAnalyzer:
    """LLM-powered complexity analyzer using hardened prompts."""

    def __init__(self, llm_client: Any) -> None:
        self._llm_client = llm_client
        self._fallback_analyzer = ComplexityAnalyzer()

    async def analyze_with_llm(
        self, interview_data: Mapping[str, Any]
    ) -> LLMComplexityResult:
        """Analyze complexity using LLM with hardened prompt.
        
        Falls back to static analysis if LLM fails.
        """
        interview_json = json.dumps(interview_data, indent=2)
        prompt = COMPLEXITY_ANALYSIS_PROMPT.format(interview_json=interview_json)

        try:
            response = await self._llm_client.generate_completion(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            # Fallback to static analysis
            print(f"LLM analysis failed, using fallback: {e}")
            static_profile = self._fallback_analyzer.analyze(interview_data)
            return LLMComplexityResult(
                complexity_score=static_profile.score,
                estimated_phase_count=static_profile.estimated_phase_count,
                depth_level=static_profile.depth_level,
                confidence=static_profile.confidence,
                rationale="Fallback to static analysis due to LLM error",
            )

    def _parse_llm_response(self, response: str) -> LLMComplexityResult:
        """Parse LLM JSON response into structured result."""
        # Clean up response - remove potential code fences
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remove markdown code fences
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

        # Validate and extract fields
        depth_level = data.get("depth_level", "standard")
        if depth_level not in ("minimal", "standard", "detailed"):
            depth_level = "standard"

        return LLMComplexityResult(
            complexity_score=float(data.get("complexity_score", 5.0)),
            estimated_phase_count=int(data.get("estimated_phase_count", 5)),
            depth_level=depth_level,
            confidence=float(data.get("confidence", 0.8)),
            rationale=str(data.get("rationale", "")),
            complexity_factors=data.get("complexity_factors", {}),
            follow_up_questions=data.get("follow_up_questions", []),
            hidden_risks=data.get("hidden_risks", []),
        )
