# Holistic Scoring Upgrade

**Date:** 2025-11-27  
**Status:** Implemented  
**File:** `src/interview/complexity_analyzer.py`

---

## Problem: Static/Bogus Scoring

The previous implementation had several bogus aspects:

### 1. Arbitrary Static Score Mappings
```python
PROJECT_TYPE_SCORE = {"cli_tool": 1, "library": 2, "api": 3, "web_app": 4, "saas": 5}
TECHNICAL_COMPLEXITY_SCORE = {"simple_crud": 1, "auth_db": 2, "realtime": 3, ...}
```
These numbers were completely made up with no basis in reality.

### 2. Formula-Based Phase Counting
```python
def estimate_phase_count(complexity_score: float) -> int:
    if complexity_score <= 3: return 3
    if complexity_score <= 7: return 5
    if complexity_score <= 12: return 7
    return int(min(9 + (complexity_score - 12) // 2, 15))
```
This overrode the LLM's judgment with an arbitrary formula.

### 3. Keyword Bucketing
The static analyzer classified projects by searching for keywords like "cli", "api", "saas" - completely missing nuance.

---

## Solution: Holistic LLM-Driven Assessment

### New Prompt Structure

The new `COMPLEXITY_ANALYSIS_PROMPT` asks the LLM to:

1. **Define its own reasoning** across three dimensions:
   - Scope Dimensions (features, data model, user types, integrations)
   - Technical Challenge Dimensions (architecture, performance, security, data handling)
   - Execution Risk Dimensions (team, timeline, unknowns, dependencies)

2. **Justify every number** with structured rationale:
   ```json
   "scoring_rationale": {
     "score_justification": "why this specific score",
     "phase_count_justification": "why this many phases",
     "depth_justification": "why this depth level",
     "key_complexity_drivers": ["main complexity factors"],
     "comparison_anchor": "Similar to building X because Y"
   }
   ```

3. **Provide semantic complexity factors** instead of buckets:
   ```json
   "complexity_factors": {
     "integrations": "medium - 2 external APIs (Stripe, SendGrid)",
     "security_compliance": "high - HIPAA requirements add audit trails",
     ...
   }
   ```

### Phase Count Guidance (Not Rules)

The LLM is given guidance on phase ranges:
- **Minimal (3-4)**: Single-purpose tools, simple CRUD, CLI utilities
- **Standard (5-7)**: Typical web apps, APIs with auth/db, moderate integrations
- **Complex (8-10)**: Multi-service, compliance, real-time, significant integrations
- **Enterprise (11-15)**: Large-scale platforms, multiple subsystems, distributed teams

But the LLM decides based on holistic reasoning, not score → phase mapping.

### Trust the LLM

The static `estimate_phase_count()` override is **removed**. The LLM's phase count is now used directly (clamped to [3, 15] for safety).

---

## New Data Structures

### ScoringRationale
```python
@dataclass
class ScoringRationale:
    score_justification: str = ""
    phase_count_justification: str = ""
    depth_justification: str = ""
    key_complexity_drivers: List[str] = field(default_factory=list)
    comparison_anchor: str = ""
```

### Updated LLMComplexityResult
```python
@dataclass
class LLMComplexityResult:
    complexity_score: float
    estimated_phase_count: int
    depth_level: DepthLevel
    confidence: float
    scoring_rationale: ScoringRationale  # NEW - structured justifications
    complexity_factors: Mapping[str, str]
    follow_up_questions: List[str]
    hidden_risks: List[str]
```

---

## Other Bogus Parts Identified (TODO)

### 1. `design_validator.py` - Static Keyword Validation

Currently uses hardcoded keyword lists:
```python
REQUIRED_SECTIONS = ["architecture", "database", "testing"]
OVER_ENGINEERING_KEYWORDS = ["microservice", "kubernetes", "distributed", ...]
```

**Fix needed**: The `LLMSanityReviewerWithLLM` class already exists - should be used instead of keyword matching for semantic validation.

### 2. Static `ComplexityAnalyzer` Class

The static analyzer (lines 77-147) still exists as fallback. Consider:
- Removing it entirely once LLM path is stable
- Or making it clearly labeled as "emergency fallback only"

### 3. `_check_scope_alignment()` in DesignValidator

Uses arbitrary keyword counting:
```python
complexity_keywords = ["microservice", "distributed", "kubernetes", ...]
found_keywords = sum(1 for kw in complexity_keywords if kw in design_lower)
if complexity_profile.depth_level == "minimal" and found_keywords > 2:
    # Flag as over-scoped
```

This should be LLM-driven semantic analysis.

---

## Testing

After this change, test with varied project descriptions to verify:
1. The LLM provides meaningful justifications
2. Phase counts vary appropriately with project complexity
3. No static formulas are overriding LLM decisions
4. Fallback to static only triggers on actual LLM errors

```python
# Example test cases
simple_project = {"project_name": "hello-cli", "requirements": "Print hello world"}
# Expected: score ~2, phases 3, depth minimal

complex_project = {
    "project_name": "healthcare-platform",
    "requirements": "HIPAA-compliant multi-tenant SaaS with real-time messaging",
    "apis": ["Stripe", "Twilio", "SendGrid", "AWS S3"],
    "team_size": "6"
}
# Expected: score ~14, phases 10-12, depth detailed
```

---

## Related: Task Decomposition Step (NEW)

To ensure phase generation is grounded in explicit task analysis, a new **Task Decomposition** step was added before devplan generation.

### New Module: `src/pipeline/task_decomposer.py`

This module runs BEFORE phase generation and:

1. **Extracts all discrete tasks** from the project design
2. **Validates coverage** - every requirement has tasks
3. **Plans phases** with dependency awareness
4. **Provides explicit rationale** for phase structure

### Pipeline Flow (Updated)

```
Interview → Design → Complexity Analysis → Task Decomposition → DevPlan Generation
                                              ↑
                                     NEW STEP: Grounds phase 
                                     generation in explicit tasks
```

### Task Extraction Prompt

The LLM is asked to extract tasks with:
- Clear ID, title, description
- Category (setup, core, data, integration, ui, testing, docs, deployment, security)
- Complexity level
- Dependencies on other tasks
- Requirements traceability

### Phase Planning Prompt

The LLM then organizes tasks into phases with:
- Dependency validation (no task before its dependencies)
- Entry/exit criteria for each phase
- Risk awareness
- Explicit rationale for structure

### Template Integration

The `basic_devplan.jinja` template now checks for `task_decomposition` and if present, instructs the LLM to follow the pre-planned phase structure exactly, rather than inventing phases ad-hoc.

This ensures:
- No phases with inaccurate/useless/wrong steps
- Every task is explicitly assigned
- Dependencies are respected
- Phase structure is justified, not arbitrary
