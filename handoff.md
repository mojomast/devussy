 """# Devussy Adaptive Pipeline - Circular Development Handoff

**Date:** 2025-11-25  
**From:** Design & Planning Agent  
**To:** Implementation Agent  
**Project:** Devussy Adaptive Complexity Overhaul v2.0  

---

## 🎯 Mission Statement

Transform Devussy into an adaptive, complexity-aware development planning pipeline that dynamically scales output based on project complexity, validates designs through multi-stage checks, and prevents over-engineering through intelligent iteration.

**Core Improvement:** Replace static pipeline with adaptive complexity assessment → validation loops → scaled output generation.

---

## 📋 What You're Receiving

### Primary Artifacts
1. **devplan.md** - Complete 2-phase implementation plan
2. **handoff.md** - This document (circular development guide)

### Context Already Established
- Current Devussy architecture (see GitHub repo)
- Problem analysis (static complexity, no validation, no reasoning)
- Solution approach (multi-stage interview, validation, adaptive scaling)
- Success metrics and testing requirements

---

## 🎯 Your Primary Objectives

### Phase 1: Backend Workflow Overhaul (PRIORITY)

**Goal:** Build the adaptive complexity engine and validation system.

**What to build:**

1. **Complexity Analyzer Module** (`src/interview/complexity_analyzer.py`)
   - Analyze interview JSON → complexity score (0-20)
   - Estimate phase count (3-15 phases)
   - Determine depth level (minimal/standard/detailed)
   - Calculate confidence score
   - Generate follow-up questions if needed

2. **Interview Enhancement** (`src/interview/llm_interview_manager.py` modifications)
   - Add `follow_up` mode to existing interview manager
   - Implement clarification request flow
   - Integrate with complexity analyzer

3. **Design Validation System** (new modules)
   - `src/pipeline/design_validator.py` - Rule-based validation checks
   - `src/pipeline/llm_sanity_reviewer.py` - LLM semantic review
   - `src/pipeline/design_correction_loop.py` - Iterative correction orchestrator

4. **Adaptive Generators** (modify existing)
   - `src/pipeline/design_generator.py` - Scale output by complexity
   - `src/pipeline/devplan_generator.py` - Dynamic phase count and granularity

5. **Pipeline Orchestration** (`src/pipeline/main_pipeline.py` refactor)
   - Integrate all new stages
   - Implement checkpoint system for new stages
   - Add streaming support for validation/correction

**Testing Requirements:**
- 85%+ code coverage for all new modules
- Unit tests for each validation check
- Integration tests for full pipeline flows
- E2E tests with real LLM at 3 complexity levels

---

### Phase 2: Frontend/UI Updates (AFTER Phase 1 Complete)

**Goal:** Expose adaptive pipeline features through web UI.

**What to build:**

1. **New Screens/Components** (in `devussy-web/app/components/`)
   - `ComplexityAssessment.tsx` - Visual complexity profile
   - `DesignSanityCheck.tsx` - Validation results dashboard
   - `IterativeApproval.tsx` - Approval gates UI
   - `CorrectionTimeline.tsx` - Iteration history visualization

2. **State Management Updates** (`devussy-web/app/state/`)
   - Extend pipeline stages enum
   - Add new data models (ComplexityProfile, ValidationReport, etc.)
   - Implement state transitions with conditions

3. **API Integration** (`devussy-web/app/api/`)
   - New SSE endpoints for validation/correction
   - Real-time streaming for correction loop
   - Checkpoint loading for new stages

4. **Enhanced Downloads**
   - Include complexity profile, validation reports in ZIP
   - Add iteration history
   - Include prompts used

**Testing Requirements:**
- 80%+ component test coverage
- E2E tests for all new user flows
- Visual regression tests
- Accessibility compliance (WCAG 2.1 AA)

---

## 🔑 Critical Implementation Details

### Complexity Scoring Rubric (MUST IMPLEMENT EXACTLY)

```python
# Complexity score calculation
project_type_score = {
    'cli_tool': 1,
    'library': 2,
    'api': 3,
    'web_app': 4,
    'saas': 5
}

technical_complexity_score = {
    'simple_crud': 1,
    'auth_db': 2,
    'realtime': 3,
    'ml_ai': 4,
    'multi_region': 5
}

integration_score = {
    'standalone': 0,
    '1_2_services': 1,
    '3_5_services': 2,
    '6_plus_services': 3
}

team_size_multiplier = {
    'solo': 0.5,
    '2_3': 1.0,
    '4_6': 1.2,
    '7_plus': 1.5
}

total_complexity = (project_type + technical + integration) * team_multiplier
```

### Phase Count Mapping (MUST USE)

```python
def estimate_phase_count(complexity_score: float) -> int:
    if complexity_score <= 3:
        return 3  # minimal
    elif complexity_score <= 7:
        return 5  # standard
    elif complexity_score <= 12:
        return 7  # complex
    else:
        return min(9 + (complexity_score - 12) // 2, 15)  # enterprise (cap at 15)
```

### Validation Checks (ALL REQUIRED)

1. **Consistency Check:** No contradictions in design
2. **Completeness Check:** All requirements addressed
3. **Scope Alignment Check:** Complexity matches profile
4. **Hallucination Detection:** No fictional APIs/libraries
5. **Over-Engineering Detection:** Appropriate abstractions for scale

### Correction Loop Logic (MAX 3 ITERATIONS)

```python
MAX_ITERATIONS = 3
CONFIDENCE_THRESHOLD = 0.8

for iteration in range(MAX_ITERATIONS):
    validation = validate_design(design)
    review = llm_review_design(design)
    
    if validation.is_valid and review.confidence > CONFIDENCE_THRESHOLD:
        return design  # SUCCESS
    
    if not validation.auto_correctable:
        return design, requires_human_review=True
    
    design = apply_corrections(design, validation, review)

return design, max_iterations_reached=True
```

---

## 📁 File Structure Reference

### New Files to Create

```
src/
├── interview/
│   ├── complexity_analyzer.py (NEW)
│   └── interview_pipeline.py (NEW)
├── pipeline/
│   ├── design_validator.py (NEW)
│   ├── llm_sanity_reviewer.py (NEW)
│   ├── design_correction_loop.py (NEW)
│   └── output_formatter.py (NEW)

schemas/
├── complexity_profile.json (NEW)
├── validation_report.json (NEW)
├── review_result.json (NEW)
└── final_design.json (NEW)

templates/
├── interview/
│   └── follow_up_questions.jinja2 (NEW)
├── design/
│   └── adaptive_design.jinja2 (NEW)
├── devplan/
│   ├── adaptive_phases.jinja2 (NEW)
│   ├── phase_minimal.jinja2 (NEW)
│   ├── phase_standard.jinja2 (NEW)
│   └── phase_detailed.jinja2 (NEW)
└── validation/
    └── sanity_review_prompt.jinja2 (NEW)

tests/
├── unit/
│   ├── test_complexity_analyzer.py (NEW)
│   ├── test_design_validator.py (NEW)
│   ├── test_llm_sanity_reviewer.py (NEW)
│   └── test_design_correction_loop.py (NEW)
├── integration/
│   ├── test_interview_to_complexity_flow.py (NEW)
│   ├── test_adaptive_design_generation.py (NEW)
│   ├── test_validation_and_correction.py (NEW)
│   └── test_end_to_end_adaptive_pipeline.py (NEW)
└── harness/
    └── pipeline_test_harness.py (NEW)

devussy-web/
└── app/
    ├── components/
    │   ├── ComplexityAssessment.tsx (NEW)
    │   ├── DesignSanityCheck.tsx (NEW)
    │   ├── IterativeApproval.tsx (NEW)
    │   ├── ComplexityGauge.tsx (NEW)
    │   ├── PhaseCountEstimate.tsx (NEW)
    │   ├── ValidationResults.tsx (NEW)
    │   ├── CorrectionTimeline.tsx (NEW)
    │   ├── ReasoningPanel.tsx (NEW)
    │   ├── PromptInspector.tsx (NEW)
    │   └── RefineButton.tsx (NEW)
    ├── state/
    │   └── pipelineState.ts (MODIFY)
    └── api/
        └── (new endpoints) (NEW)
```

### Files to Modify

```
src/
├── interview/
│   └── llm_interview_manager.py (ADD follow_up mode)
├── pipeline/
│   ├── design_generator.py (ADD complexity awareness)
│   ├── devplan_generator.py (ADD adaptive phase count)
│   ├── main_pipeline.py (REFACTOR for new flow)
│   └── streaming.py (ADD new stage prefixes)

devussy-web/
└── app/
    ├── components/
    │   └── WindowManager.tsx (ADD new window types)
    └── utils/
        └── zipGenerator.ts (INCLUDE new artifacts)
```

---

## 🚨 Critical Rules for Circular Development

### 1. Context Management (KEEP IT SMALL)

**DO:**
- ✅ Read ONLY the files relevant to current task
- ✅ Use anchors to reference prior context (see devplan.md sections)
- ✅ Keep active context under 50k tokens
- ✅ Rely on this handoff for high-level flow

**DON'T:**
- ❌ Re-read entire repository
- ❌ Re-explain problem statement
- ❌ Duplicate context already in devplan.md
- ❌ Load all files "just in case"

### 2. Iteration Protocol

**When starting work:**
1. Read this handoff.md
2. Read relevant section of devplan.md
3. Read ONLY files you'll modify
4. Implement task
5. Write tests
6. Update handoff with progress

**When passing baton:**
1. Update handoff.md with:
   - What you completed
   - What's next
   - Any blockers or decisions needed
   - Files modified (list)
2. Commit changes
3. Next agent reads handoff, continues

### 3. Testing Before Proceeding

**After each milestone:**
- Run unit tests → must pass
- Run integration tests → must pass
- Update test coverage report
- Don't proceed if tests failing

**After each phase:**
- Run full test suite
- Run E2E tests
- Validate against success criteria
- Generate test report

### 4. Hallucination Prevention

**When generating code that references external packages:**
1. Cross-reference against known registries (npm, PyPI)
2. Check import paths match real packages
3. Validate API methods exist in documentation
4. Flag uncertain references for human review

**When generating designs:**
1. Use only tech stacks mentioned in interview
2. Don't invent framework names
3. Keep dependencies minimal and verified
4. Flag experimental or uncommon choices

### 5. Deterministic Output

**Always:**
- Use consistent formatting (black, prettier)
- Generate same output for same input
- Preserve existing file structure
- Follow existing code style
- Use templates consistently

**Never:**
- Randomize output
- Change unrelated code
- Reformat entire files
- Introduce style inconsistencies

---
## 📊 Progress Tracking

### Phase 1 Checklist

**Milestone 1: Complexity Analysis System**
 - [x] `complexity_analyzer.py` implemented
 - [x] `interview_pipeline.py` implemented
 - [ ] Follow-up mode added to `llm_interview_manager.py`
 - [ ] Unit tests passing (30+ tests)
 - [x] Integration test: interview → complexity flow

**Milestone 2: Design Validation System**
 - [x] `design_validator.py` implemented
 - [x] `llm_sanity_reviewer.py` implemented
 - [x] `design_correction_loop.py` implemented
 - [x] All 5 validation checks working (rule-based, mock-first)
 - [ ] Unit tests passing (60+ tests)
 - [x] Integration test: validation → correction flow

**Milestone 3: Adaptive Generators**
- [x] `design_generator.py` implemented with complexity awareness (mock, LLM-free)
- [x] `devplan_generator.py` implemented with dynamic phases (mock, LLM-free)
- [ ] Template variants created (minimal/standard/detailed)
- [x] Unit tests passing for adaptive generators
- [x] Output scales correctly at 3 complexity levels (minimal/standard/detailed)

**Milestone 4: Pipeline Integration**
 - [x] Mock adaptive backend pipeline implemented (`mock_adaptive_pipeline.py`)
 - [x] Integration tests: end-to-end mock adaptive pipeline
 - [x] Pipeline test harness implemented for mock adaptive pipeline (`tests/harness/pipeline_test_harness.py`)
 - [ ] `main_pipeline.py` refactored
 - [ ] Checkpoint system extended
 - [ ] Streaming support added
 - [ ] E2E tests passing (3 complexity levels with real LLM)
 - [ ] Test coverage ≥ 85%

### Phase 2 Checklist

**Milestone 5: Core UI Components**
- [ ] `ComplexityAssessment.tsx` implemented

---

## 📝 Progress Log

### 2025-11-25 - Initial Planning Agent
**Completed:**
- Full devplan.md creation (Phase 1 + Phase 2)
- This handoff.md for circular development
- Problem analysis and solution design
- Success criteria definition
- Testing strategy

**Next Steps:**
- Implementation Agent: Start Phase 1, Milestone 1 (Complexity Analysis System)
- Begin with `src/interview/complexity_analyzer.py`

**Blockers/Decisions Needed:**
- None - ready for implementation

---

### 2025-11-25 - Backend Mock Implementation Agent
**Completed:**
- Implemented `src/interview/complexity_analyzer.py` and unit tests
- Implemented `src/interview/interview_pipeline.py` and integration test
- Implemented `src/pipeline/design_validator.py`, `llm_sanity_reviewer.py`, `design_correction_loop.py`
- Added unit tests for validation and correction loop
- Implemented `src/pipeline/mock_adaptive_pipeline.py` and integration test for full mock adaptive flow
- Created tracking docs: `adaptive_pipeline_progress.md`, `adaptive_pipeline_llm_ideas.md`

**Files Modified:**
- `src/interview/complexity_analyzer.py`
- `src/interview/interview_pipeline.py`
- `src/pipeline/design_validator.py`
- `src/pipeline/llm_sanity_reviewer.py`
- `src/pipeline/design_correction_loop.py`
- `src/pipeline/mock_adaptive_pipeline.py`
- `tests/unit/test_complexity_analyzer.py`
- `tests/unit/test_design_validator.py`
- `tests/unit/test_llm_sanity_reviewer.py`
- `tests/unit/test_design_correction_loop.py`
- `tests/integration/test_interview_to_complexity_flow.py`
- `tests/integration/test_validation_and_correction.py`
- `tests/integration/test_mock_adaptive_pipeline.py`
- `adaptive_pipeline_progress.md`
- `adaptive_pipeline_llm_ideas.md`

**Tests:**
 - Unit tests: complexity analyzer, validation, sanity reviewer, correction loop
 - Integration tests: interview → complexity, validation → correction, mock adaptive pipeline
 - Coverage: not yet measured for this slice

**How to run tests for this phase:**

- Run unit tests for new backend modules:
  - `pytest tests/unit/test_complexity_analyzer.py -v`
  - `pytest tests/unit/test_design_validator.py -v`
  - `pytest tests/unit/test_llm_sanity_reviewer.py -v`
  - `pytest tests/unit/test_design_correction_loop.py -v`
- Run integration tests for adaptive backend flow:
  - `pytest tests/integration/test_interview_to_complexity_flow.py -v`
  - `pytest tests/integration/test_validation_and_correction.py -v`
  - `pytest tests/integration/test_mock_adaptive_pipeline.py -v`
- Optional: run full coverage for this repo slice:
  - `pytest --cov=src --cov-report=html`

**Next backend phases after this slice:**

- Implement `follow_up` mode and clarification flow in `llm_interview_manager.py`.
- Add complexity-aware behavior to `design_generator` / `devplan_generator` (mock-first, no real LLM calls).
- Use `adaptive_pipeline_llm_ideas.md` to design prompts, schemas, and validation for real LLM integration.

### 2025-11-25 - Adaptive Generators & Harness Agent
**Completed:**
- Implemented `src/pipeline/design_generator.py` (AdaptiveDesignGenerator, mock complexity-aware design).
- Implemented `src/pipeline/devplan_generator.py` (AdaptiveDevPlanGenerator, dynamic phase structure).
- Wired adaptive generators into `src/pipeline/mock_adaptive_pipeline.py`.
- Updated `src/pipeline/design_correction_loop.py` to accept optional `ComplexityProfile` for validation.
- Added unit tests `tests/unit/test_adaptive_design_generator.py` and `tests/unit/test_adaptive_devplan_generator.py`.
- Implemented `tests/harness/pipeline_test_harness.py` and `tests/harness/test_pipeline_test_harness.py` for mock adaptive scenarios.

**Files Modified/Added:**
- `src/pipeline/design_generator.py`
- `src/pipeline/devplan_generator.py`
- `src/pipeline/mock_adaptive_pipeline.py`
- `src/pipeline/design_correction_loop.py`
- `tests/unit/test_adaptive_design_generator.py`
- `tests/unit/test_adaptive_devplan_generator.py`
- `tests/harness/pipeline_test_harness.py`
- `tests/harness/test_pipeline_test_harness.py`

**Recommended Tests:**
- `pytest tests/unit/test_adaptive_design_generator.py -v`
- `pytest tests/unit/test_adaptive_devplan_generator.py -v`
- `pytest tests/harness/test_pipeline_test_harness.py -v`
- `pytest tests/integration/test_mock_adaptive_pipeline.py -v`

### For Frontend Work

**Reuse existing:**
- Tailwind config and design tokens
- Shadcn UI components
- Window management patterns
- Streaming handlers

**State management:**
- Use Zustand for global state
- Add new pipeline stages to enum
- Implement conditional transitions
- Persist state in checkpoints

**Testing approach:**
- React Testing Library for component tests
- Mock API responses with MSW
- Playwright for E2E tests
- Percy/Chromatic for visual regression

---

## 🚀 Quick Start Commands

### Backend Development

```bash
# Setup
cd devussy
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -e .

# Run tests
pytest tests/unit/test_complexity_analyzer.py -v
pytest tests/integration/ -v
pytest tests/ --cov=src --cov-report=html

# Run pipeline
python -m src.cli interactive
```

### Frontend Development

```bash
# Setup
cd devussy-web
npm install

# Run dev server (backend must be running)
npm run dev

# Run tests
npm test
npm run test:e2e
npm run test:visual
```

---

## 📚 Reference Materials

### Key Documentation
- **Current Devussy README:** https://github.com/mojomast/devussy
- **JSON Schema Spec:** https://json-schema.org/
- **Pydantic Docs:** https://docs.pydantic.dev/
- **Jinja2 Templates:** https://jinja.palletsprojects.com/
- **React Testing Library:** https://testing-library.com/react
- **Playwright:** https://playwright.dev/

### Devussy-Specific
- Current prompts: `src/prompts/`
- Current templates: `templates/`
- Existing tests: `tests/`
- Web UI: `devussy-web/`

---

## 🎉 Final Notes

**You have everything you need:**
- Complete devplan with detailed tasks
- This handoff with implementation guidance
- Clear success criteria
- Testing strategy
- File structure

**Remember:**
- Keep context small (use anchors)
- Test before proceeding
- Update progress log
- Pass clean baton to next agent

**Questions?**
- Refer to devplan.md for detailed specs
- Check existing code for patterns
- Flag uncertainties in progress log

**Let's build something great! 🚀**

---

*End of Handoff Document*
"""