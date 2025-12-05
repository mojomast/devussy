from __future__ import annotations

"""
Complexity Analyzer - Testing Scaffold Implementation

This module provides DETERMINISTIC, RULE-BASED complexity analysis for testing
and development purposes. The static scoring rubric enables:
- Predictable unit test outcomes
- Fast iteration without API calls
- Baseline comparison for LLM integration

PRODUCTION BEHAVIOR (future):
When integrated with LLM, the analyzer should dynamically assess complexity
based on full project context rather than keyword matching. See:
- adaptive_pipeline_llm_ideas.md (Section 1)
- handoff.md (Complexity Assessment section)

The LLM should:
1. Analyze interview transcript holistically
2. Consider how complexity factors interact
3. Detect hidden complexity (compliance, security, scaling)
4. Generate targeted follow-up questions
5. Provide transparent reasoning for its assessment

The rule-based implementation here serves as a FALLBACK when:
- LLM is unavailable
- Validating LLM output against heuristics
- Running CI/CD tests deterministically
"""

from dataclasses import dataclass
from typing import Literal, Mapping, Any


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
