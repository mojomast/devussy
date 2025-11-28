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
You are the Complexity Analysis Model. You will holistically analyze the interview data to determine how complex this project is and how it should be structured for development planning.

YOUR ROLE:
You are an expert software architect who has shipped hundreds of projects. You understand what makes projects simple vs complex based on REAL engineering experience, not arbitrary formulas.

YOU MUST NOT:
- invent features not in the requirements
- contradict the provided data
- use arbitrary numerical scales without justification
- output any text outside JSON

---

## HOLISTIC COMPLEXITY ASSESSMENT

Rather than mapping to predefined buckets, YOU determine the complexity by reasoning about these dimensions:

### 1. SCOPE DIMENSIONS (consider all that apply)
- **Core functionality**: How many distinct features/capabilities?
- **Data model**: Simple CRUD? Complex relationships? Event sourcing?
- **User types**: Single user? Multi-tenant? Role hierarchies?
- **Integration surface**: Standalone? Few APIs? Many external systems?

### 2. TECHNICAL CHALLENGE DIMENSIONS
- **Architecture needs**: Monolith? Services? Distributed?
- **Performance requirements**: Standard? High-throughput? Real-time?
- **Security/Compliance**: Basic auth? Enterprise SSO? HIPAA/PCI/SOC2?
- **Data handling**: Simple storage? ETL? ML pipelines? Analytics?

### 3. EXECUTION RISK DIMENSIONS
- **Team capability**: Solo dev? Small team? Cross-functional?
- **Timeline pressure**: Relaxed? Standard? Aggressive?
- **Unknowns**: Well-defined? Ambiguous requirements? R&D elements?
- **Dependencies**: Self-contained? Waiting on external teams/APIs?

---

## PHASE COUNT REASONING

Determine the number of phases (3-15) based on your holistic assessment:

**Minimal projects (3-4 phases):** Single-purpose tools, simple CRUD apps, CLI utilities, basic scripts with no external dependencies.

**Standard projects (5-7 phases):** Typical web apps, APIs with auth/db, moderate integrations, well-understood domains.

**Complex projects (8-10 phases):** Multi-service architectures, compliance requirements, real-time features, significant integrations, team coordination needs.

**Enterprise projects (11-15 phases):** Large-scale platforms, multiple subsystems, extensive compliance, distributed teams, long-term maintenance considerations.

YOU DECIDE the phase count by reasoning about the project, not by plugging numbers into a formula.

---

## DEPTH LEVEL

Choose depth based on how much detail each phase needs:

- **"minimal"**: Brief task lists, obvious implementation paths, experienced team can fill gaps
- **"standard"**: Clear specifications, acceptance criteria, reasonable detail for mid-level devs  
- **"detailed"**: Extensive specs, edge cases documented, junior-friendly, compliance audit trails

---

## CONFIDENCE SCORING

Your confidence (0.0-1.0) reflects how well you understand the project:

- **0.9-1.0**: Crystal clear requirements, well-defined scope, no ambiguity
- **0.7-0.9**: Good understanding, minor clarifications might help
- **0.5-0.7**: Significant gaps in requirements, need follow-up questions
- **< 0.5**: Requirements too vague to assess accurately

If confidence < 0.7, provide meaningful follow_up_questions.

---

EXPECTED JSON SCHEMA (MUST MATCH EXACTLY):

{{
  "complexity_score": <number 0-20>,
  "estimated_phase_count": <integer 3-15>,
  "depth_level": "<minimal|standard|detailed>",
  "confidence": <number 0-1>,
  "scoring_rationale": {{
    "score_justification": "<why you chose this specific score - what factors drove it up or down>",
    "phase_count_justification": "<why this many phases - what work needs to be separated>",
    "depth_justification": "<why this depth level - what about the project/team demands it>",
    "key_complexity_drivers": ["<list the 2-4 main things making this project complex or simple>"],
    "comparison_anchor": "<compare to a well-known project type: 'Similar in complexity to building X because Y'>"
  }},
  "complexity_factors": {{
    "integrations": "<none/low/medium/high + brief explanation>",
    "security_compliance": "<none/low/medium/high + brief explanation>",
    "data_complexity": "<none/low/medium/high + brief explanation>",
    "realtime_requirements": "<none/low/medium/high + brief explanation>",
    "scale_requirements": "<none/low/medium/high + brief explanation>",
    "architecture_complexity": "<none/low/medium/high + brief explanation>",
    "team_and_timeline_risk": "<none/low/medium/high + brief explanation>",
    "domain_complexity": "<none/low/medium/high + brief explanation>"
  }},
  "follow_up_questions": [
    "<meaningful questions to reduce uncertainty - omit if confidence > 0.85>"
  ],
  "hidden_risks": [
    "<domain-specific risks the user may not have considered>"
  ]
}}

YOUR TASK:
Analyze the provided interview data holistically. Reason through the dimensions above. Produce a complexity assessment where every number is justified by your reasoning, not by formulas.

INTERVIEW DATA:
{interview_json}

BEGIN NOW."""


@dataclass
class ScoringRationale:
    """Structured reasoning for why a complexity score was chosen."""
    score_justification: str = ""
    phase_count_justification: str = ""
    depth_justification: str = ""
    key_complexity_drivers: List[str] = field(default_factory=list)
    comparison_anchor: str = ""


@dataclass
class LLMComplexityResult:
    """Result from LLM-powered complexity analysis."""
    complexity_score: float
    estimated_phase_count: int
    depth_level: DepthLevel
    confidence: float
    scoring_rationale: ScoringRationale = field(default_factory=ScoringRationale)
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
                scoring_rationale=ScoringRationale(
                    score_justification="Fallback to static analysis due to LLM error",
                    phase_count_justification="Using static formula fallback",
                    depth_justification="Derived from static complexity score",
                ),
            )

    def _parse_llm_response(self, response: str) -> LLMComplexityResult:
        """Parse LLM JSON response into structured result.
        
        The LLM now holistically determines the phase count based on its
        reasoning. We trust the LLM's judgment since it provides explicit
        justification in scoring_rationale.
        """
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

        # Get complexity score from LLM
        complexity_score = float(data.get("complexity_score", 5.0))
        
        # Trust the LLM's phase count - it now provides explicit justification
        # Clamp to valid range [3, 15]
        llm_phase_count = int(data.get("estimated_phase_count", 5))
        estimated_phase_count = max(3, min(15, llm_phase_count))
        
        # Parse the structured scoring rationale
        rationale_data = data.get("scoring_rationale", {})
        scoring_rationale = ScoringRationale(
            score_justification=str(rationale_data.get("score_justification", "")),
            phase_count_justification=str(rationale_data.get("phase_count_justification", "")),
            depth_justification=str(rationale_data.get("depth_justification", "")),
            key_complexity_drivers=rationale_data.get("key_complexity_drivers", []),
            comparison_anchor=str(rationale_data.get("comparison_anchor", "")),
        )

        return LLMComplexityResult(
            complexity_score=complexity_score,
            estimated_phase_count=estimated_phase_count,
            depth_level=depth_level,
            confidence=float(data.get("confidence", 0.8)),
            scoring_rationale=scoring_rationale,
            complexity_factors=data.get("complexity_factors", {}),
            follow_up_questions=data.get("follow_up_questions", []),
            hidden_risks=data.get("hidden_risks", []),
        )
