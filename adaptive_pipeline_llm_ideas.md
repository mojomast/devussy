# Adaptive Pipeline LLM Integration Ideas

This document captures the intended **LLM-backed behavior** for each mocked component in the adaptive pipeline. Once the mock-only backend is stable and tested, this will be the source of truth for designing prompts, schemas, and API integration.

> **IMPORTANT:** The current implementation uses static heuristics as a **testing scaffold**. The production system should use **LLM-driven dynamic assessment** that analyzes actual project requirements holistically rather than mapping to fixed buckets.

---

## Design Philosophy: Mock → LLM Transition

### Why Start with Mocks?
1. **Deterministic Testing:** Unit tests need predictable outputs
2. **Fast Iteration:** No API latency during development
3. **Cost Control:** Avoid token costs while iterating on logic
4. **Schema Validation:** Prove the data structures work before LLM integration

### Production LLM Behavior Goals
1. **Holistic Analysis:** LLM considers full project context, not just keyword matching
2. **Nuanced Scoring:** Complexity factors interact (e.g., "simple CRUD with ML" is more complex than either alone)
3. **Hidden Complexity Detection:** LLM can identify compliance, security, or scaling requirements not explicitly stated
4. **Adaptive Follow-Ups:** LLM generates targeted clarification questions based on gaps
5. **Transparent Reasoning:** LLM explains its complexity assessment for user validation

---

## 1. Complexity Analyzer (`src/interview/complexity_analyzer.py`)

### Current Mock Behavior

- Pure-Python heuristics infer:
  - `project_type_bucket` from `project_type` string (CLI, API, Web App, SaaS, etc.).
  - `technical_complexity_bucket` from keywords in `requirements` / `frameworks`.
  - `integration_bucket` from simple counts of `apis`.
  - `team_size_bucket` from `team_size` string or number.
- Computes `score`, `estimated_phase_count`, `depth_level`, and a simple `confidence`.

### Future LLM-Powered Behavior (Production)

The LLM should analyze projects **dynamically** rather than fitting into predefined buckets:

#### Prompt Template (Complexity Assessment)
```
You are a senior software architect analyzing a project to determine appropriate development complexity and planning depth.

## Project Information
- **Project Name:** {project_name}
- **Description:** {description}
- **Project Type:** {project_type}
- **Technical Requirements:** {requirements}
- **Target Frameworks/Tech Stack:** {frameworks}
- **External Integrations:** {apis}
- **Team Size:** {team_size}
- **Timeline Constraints:** {timeline}

## Additional Context (if available)
{repository_analysis_summary}

## Your Task
Analyze this project holistically and provide a complexity assessment. Consider:
1. How the various complexity factors INTERACT (a simple CRUD + ML integration is more complex than either alone)
2. Hidden complexity signals like compliance requirements, data sensitivity, or scaling needs
3. Team experience implications (larger teams need more coordination overhead)
4. Any unstated assumptions that add complexity

Respond with ONLY valid JSON matching this schema:
```json
{
  "complexity_score": <float 0-20>,
  "estimated_phase_count": <int 3-15>,
  "depth_level": "minimal" | "standard" | "detailed",
  "confidence": <float 0-1>,
  "rationale": "<markdown string explaining your reasoning>",
  "complexity_factors": {
    "project_scope": <1-5>,
    "technical_depth": <1-5>,
    "integration_complexity": <0-5>,
    "team_coordination": <1-3>,
    "hidden_complexity": <0-3>
  },
  "hidden_complexity_flags": ["<list of detected hidden factors>"],
  "risk_factors": ["<list of identified risks>"],
  "follow_up_questions": ["<questions to ask if confidence < 0.7>"]
}
```

#### Validation Strategy
```python
def validate_llm_complexity(llm_result: dict, interview_data: dict) -> ComplexityProfile:
    # Compute rule-based fallback
    fallback = rule_based_complexity(interview_data)
    
    # Parse LLM result
    llm_profile = parse_llm_response(llm_result)
    
    # Validate score is within reasonable bounds
    if abs(llm_profile.score - fallback.score) > 3:
        # Large divergence - flag for review but trust LLM with reduced confidence
        llm_profile.confidence *= 0.7
        llm_profile.rationale += "\n\n⚠️ Score differs significantly from heuristic estimate."
    
    # Clamp values to valid ranges
    llm_profile.score = clamp(llm_profile.score, 0, 20)
    llm_profile.estimated_phase_count = clamp(llm_profile.estimated_phase_count, 3, 15)
    llm_profile.confidence = clamp(llm_profile.confidence, 0, 1)
    
    return llm_profile
```

---

## 2. Interview Pipeline (`src/interview/interview_pipeline.py`)

### Planned Mock Behavior

- Orchestrator that:
  - Accepts `LLMInterviewManager` outputs (either `extracted_data` or `to_generate_design_inputs()` result).
  - Calls `ComplexityAnalyzer.analyze(...)`.
  - Emits a consolidated object: `{ "inputs": ..., "complexity_profile": ... }`.
- All data provided directly by tests; **no live LLM calls**.

### Future LLM-Powered Behavior (Ideas)

- Allow an LLM to:
  - Post-process interview transcripts into a richer, normalized "project brief" before complexity analysis.
  - Suggest **follow-up questions** when confidence is low or key fields are missing.
- Prompt concepts:
  - Given transcript + current `ComplexityProfile`, ask LLM to propose 3–5 targeted clarifying questions and a short explanation of why each matters.
- Integration:
  - Expose a `follow_up` mode on `LLMInterviewManager` that uses these questions to drive another micro-interview loop.

---

## 3. Design Validation System

### 3.1 `src/pipeline/design_validator.py` (Rule-Based)

#### Mock Behavior (Planned)

- Deterministic checks only:
  - Consistency, completeness, scope alignment, hallucination guard (basic string checks), over-engineering heuristics.
- Returns a `ValidationReport` object with:
  - `is_valid`, `auto_correctable`, per-check results, and a list of issues.

#### Future LLM Ideas

- Use LLM to:
  - Classify each issue’s severity and suggest candidate fixes.
  - Detect more subtle contradictions and missing requirements.
- Prompt concepts:
  - Provide design markdown + current issues; ask for a structured refinement plan.

### 3.2 `src/pipeline/llm_sanity_reviewer.py`

#### Mock Behavior (Planned)

- Simple stub that:
  - Returns a fixed `review_result` with configurable `confidence` and generic comments.

#### Future LLM Ideas

- Dedicated LLM reviewer prompt that:
  - Scores design on axes (feasibility, consistency, scalability, risk) 0–1.
  - Produces short bullet lists of **risks**, **assumptions**, and **questions**.
- Output schema:
  - `confidence`, `risk_flags`, `suggested_changes`, `notes`.

### 3.3 `src/pipeline/design_correction_loop.py`

#### Mock Behavior (Planned)

- Pure loop that:
  - Applies deterministic transformations (e.g., tweak text, inject placeholders) to simulate corrections.
  - Stops after `MAX_ITERATIONS` or when validation + mock review meet thresholds.

#### Future LLM Ideas

- Use LLM to:
  - Rewrite design sections in-place to resolve specific validation issues.
  - Preserve structure while adjusting content (headings, phases, bullet lists).
- Prompt concepts:
  - "Here is the current design + structured issues; rewrite only the marked sections to address them." with strict JSON or markdown segment outputs.

---

## 4. Adaptive Generators

### 4.1 `src/pipeline/design_generator.py`

#### Mock Behavior (Planned)

- Switches between template variants (minimal/standard/detailed) using stubbed data.
- No real LLM; uses static fixtures or simple string composition.

#### Future LLM Ideas

- Prompt templates that:
  - Include `ComplexityProfile`, validation feedback, and interview summary.
  - Enforce word-count / detail targets per depth level.

### 4.2 `src/pipeline/devplan_generator.py`

#### Mock Behavior (Planned)

- Uses `estimated_phase_count` and depth level to:
  - Select phase templates.
  - Generate deterministic placeholder devplans.

#### Future LLM Ideas

- LLM prompts tuned for:
  - Phase count, per-phase granularity, and explicit assumptions.
  - Output as structured markdown with anchors required by Devussy.

---

## 5. Main Pipeline Integration (`src/pipeline/main_pipeline.py`)

### Mock Behavior (Planned)

- Compose all pieces:
  - Interview → Complexity → Design → Validation → Correction → Devplan.
- All LLM steps replaced with:
  - Stubs, fixtures, or deterministic generators.

### Future LLM Ideas

- Central configuration for:
  - Per-stage models (design, devplan, validation/review).
  - Temperature / max tokens tuned by complexity score.
- Observability:
  - Track token usage and latency per stage.
  - Save raw prompts/responses for debugging (behind a flag).

---

## 6. Migration Strategy: Mock → LLM

### Phase 1: Stabilize Mock Pipeline (CURRENT)
- [x] All mock components implemented
- [x] Unit tests passing for deterministic behavior
- [x] Integration tests for full mock pipeline
- [ ] Coverage > 85% for adaptive modules

### Phase 2: LLM-Ready Interfaces
- [ ] Add `LLMProvider` protocol to complexity analyzer
- [ ] Create `use_llm: bool` flag in pipeline config
- [ ] Implement fallback chain: LLM → Rule-Based → Error
- [ ] Add structured logging for LLM responses

### Phase 3: Complexity Analyzer LLM Integration
- [ ] Create `templates/complexity/assessment_prompt.jinja2`
- [ ] Implement `LLMComplexityAnalyzer` class
- [ ] Add response schema validation with Pydantic
- [ ] Wire to existing `ComplexityAnalyzer` as strategy pattern
- [ ] A/B test: compare LLM vs heuristic scores on sample projects

### Phase 4: Validation & Correction LLM Integration
- [ ] Create `templates/validation/sanity_review_prompt.jinja2`
- [ ] Implement `LLMSanityReviewer.review_with_llm()`
- [ ] Create `templates/correction/fix_issues_prompt.jinja2`
- [ ] Test correction loop convergence with real LLM

### Phase 5: Generators LLM Integration
- [ ] Enhance design generator prompts with complexity awareness
- [ ] Enhance devplan generator prompts with dynamic phase targets
- [ ] Add streaming support for real-time generation

---

## 7. LLM Configuration Recommendations

### Model Selection by Stage
```yaml
# config/config.yaml additions
adaptive_pipeline:
  complexity_analysis:
    model: "claude-sonnet-4-20250514"  # Fast, good at structured output
    temperature: 0.3
    max_tokens: 2000
  
  design_validation:
    model: "claude-sonnet-4-20250514"  # Analytical tasks
    temperature: 0.2
    max_tokens: 3000
  
  design_correction:
    model: "claude-sonnet-4-20250514"  # Creative rewriting
    temperature: 0.5
    max_tokens: 4000
  
  design_generation:
    model: "claude-sonnet-4-20250514"  # Complex generation
    temperature: 0.7
    max_tokens: 8000
```

### Token Budget by Complexity
```python
def get_token_budget(complexity_score: float, stage: str) -> int:
    """Scale token limits based on project complexity."""
    base_budgets = {
        "complexity_analysis": 1500,
        "design_validation": 2000,
        "design_generation": 4000,
        "devplan_generation": 6000,
    }
    
    # Scale up for complex projects
    multiplier = 1.0 + (complexity_score / 20) * 0.5  # 1.0x - 1.5x
    return int(base_budgets[stage] * multiplier)
```

---

## 8. Testing Strategy for LLM Integration

### Unit Tests (Mock LLM)
```python
@pytest.fixture
def mock_llm_response():
    return {
        "complexity_score": 7.5,
        "estimated_phase_count": 5,
        "depth_level": "standard",
        "confidence": 0.85,
        "rationale": "Medium-complexity web app with auth..."
    }

def test_llm_complexity_parsing(mock_llm_response):
    analyzer = LLMComplexityAnalyzer(llm_client=MockClient())
    profile = analyzer.analyze(sample_interview_data)
    assert profile.score == 7.5
    assert profile.depth_level == "standard"
```

### Integration Tests (Real LLM, Limited)
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_real_llm_complexity_analysis():
    """Run with real LLM to validate prompt quality."""
    analyzer = LLMComplexityAnalyzer(llm_client=RealClient())
    profile = analyzer.analyze(SAMPLE_COMPLEX_PROJECT)
    
    # Validate structure, not exact values
    assert 0 <= profile.score <= 20
    assert 3 <= profile.estimated_phase_count <= 15
    assert profile.confidence > 0.5
    assert len(profile.rationale) > 100
```

### Golden Master Tests
```python
def test_llm_output_stability():
    """Ensure LLM outputs don't regress in quality."""
    profile = analyzer.analyze(GOLDEN_PROJECT_DATA)
    
    # Compare against saved golden output
    with open("tests/golden/complex_project_profile.json") as f:
        golden = json.load(f)
    
    # Allow some variance but flag large changes
    assert abs(profile.score - golden["score"]) <= 2
    assert profile.depth_level == golden["depth_level"]
```

---

## 9. Error Handling & Fallbacks

```python
class AdaptiveComplexityAnalyzer:
    """Combines LLM and rule-based analysis with fallback."""
    
    def __init__(self, llm_client, use_llm: bool = True):
        self.llm_analyzer = LLMComplexityAnalyzer(llm_client)
        self.rule_analyzer = ComplexityAnalyzer()  # Current implementation
        self.use_llm = use_llm
    
    def analyze(self, interview_data: dict) -> ComplexityProfile:
        if not self.use_llm:
            return self.rule_analyzer.analyze(interview_data)
        
        try:
            llm_profile = self.llm_analyzer.analyze(interview_data)
            rule_profile = self.rule_analyzer.analyze(interview_data)
            
            # Validate LLM output against rules
            return self._reconcile(llm_profile, rule_profile)
        
        except LLMError as e:
            logger.warning(f"LLM analysis failed, using rule-based: {e}")
            return self.rule_analyzer.analyze(interview_data)
    
    def _reconcile(self, llm: ComplexityProfile, rule: ComplexityProfile) -> ComplexityProfile:
        """Reconcile LLM and rule-based results."""
        score_diff = abs(llm.score - rule.score)
        
        if score_diff > 5:
            # Major divergence - log and reduce confidence
            logger.warning(f"LLM/rule score divergence: {score_diff}")
            llm.confidence *= 0.5
            llm.rationale += f"\n\n⚠️ Heuristic estimate: {rule.score:.1f}"
        
        return llm
```

---

## 10. Observability & Debugging

### Prompt Logging
```python
class ObservableLLMClient:
    """Wrapper that logs all LLM interactions."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        request_id = uuid4()
        
        # Log request
        self._log_request(request_id, prompt, kwargs)
        
        start = time.time()
        response = self.inner_client.generate(prompt, **kwargs)
        latency = time.time() - start
        
        # Log response
        self._log_response(request_id, response, latency)
        
        return response
```

### Metrics to Track
- Token usage per stage
- LLM latency per stage
- Rule vs LLM score divergence
- Validation failure rates
- Correction loop iteration counts
- Confidence score distributions

---

## 11. How to Use This Doc

When ready to integrate LLM:

1. **Pick a module** (start with Complexity Analyzer)
2. **Create prompt template** from the examples above
3. **Implement LLM variant** alongside mock
4. **Add feature flag** to toggle between them
5. **Write tests** covering both paths
6. **Run A/B comparison** on sample projects
7. **Iterate on prompt** based on quality metrics
8. **Repeat** for next module
  - Generate a focused **devplan phase** for LLM integration using these sections as inputs.
