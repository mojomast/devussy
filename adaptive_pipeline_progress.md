# Adaptive Pipeline Backend Progress

## Status Overview

- Complexity analyzer and initial tests implemented.
- Remaining backend milestones will be added in mock-first fashion (no LLM calls) and tracked here.

## Milestone 1: Complexity Analysis System

- [x] `src/interview/complexity_analyzer.py` (pure-Python scoring + phase estimation)
- [x] `tests/unit/test_complexity_analyzer.py` (rubric + scenario tests)
- [x] `src/interview/interview_pipeline.py` (wire interview data into `ComplexityAnalyzer`)
- [x] Integration tests: interview → complexity profile (mocked interview data)

## Milestone 2: Design Validation System

- [x] `src/pipeline/design_validator.py` (rule-based checks, no LLM calls)
- [x] `src/pipeline/llm_sanity_reviewer.py` (interface + mock implementation)
- [x] `src/pipeline/design_correction_loop.py` (iterative correction orchestrator, mocked)
- [x] `tests/unit/test_design_validator.py`
- [x] `tests/unit/test_llm_sanity_reviewer.py`
- [x] `tests/unit/test_design_correction_loop.py`
- [x] Integration tests: validation → correction (all mocks)

## Milestone 3: Adaptive Generators

- [x] `src/pipeline/design_generator.py` implemented with complexity-aware branching (mock + template modes)
- [x] `src/pipeline/devplan_generator.py` implemented with dynamic phase count (mock + template modes)
- [x] Template variants wired in (minimal / standard / detailed)
  - `templates/devplan/phase_minimal.jinja2`
  - `templates/devplan/phase_standard.jinja2`
  - `templates/devplan/phase_detailed.jinja2`
  - `templates/design/adaptive_design.jinja2`
  - `templates/interview/follow_up_questions.jinja2`
- [x] Unit tests for branching logic using stubbed data (`tests/unit/test_adaptive_design_generator.py`, `tests/unit/test_adaptive_devplan_generator.py`)
- [x] Follow-up mode added to `src/llm_interview.py` (FOLLOW_UP_SYSTEM_PROMPT, switch_mode, set_follow_up_context, request_clarifications)

## Milestone 4: Pipeline Integration

- [x] `src/pipeline/mock_adaptive_pipeline.py` implements end-to-end mock adaptive pipeline
- [x] `tests/integration/test_mock_adaptive_pipeline.py` (full adaptive pipeline with mocks only)
- [x] `tests/harness/pipeline_test_harness.py` and `tests/harness/test_pipeline_test_harness.py` (mock adaptive pipeline scenarios)
- [ ] Main pipeline refactored to integrate new stages:
  - Integrate `InterviewPipeline` → `ComplexityAnalyzer` flow
  - Integrate `DesignCorrectionLoop` after design generation
  - Use `AdaptiveDesignGenerator` and `AdaptiveDevPlanGenerator`
- [ ] Checkpointing extended to new stages:
  - Add `complexity_profile` checkpoint
  - Add `validation_report` checkpoint
  - Add `correction_history` checkpoint
- [ ] Streaming hooks added for new stages:
  - Add `[complexity]` prefix for complexity analysis
  - Add `[validation]` prefix for design validation
  - Add `[correction]` prefix for correction loop iterations
- [ ] JSON schemas created in `schemas/` directory:
  - `schemas/complexity_profile.json`
  - `schemas/validation_report.json`
  - `schemas/review_result.json`
  - `schemas/final_design.json`
- [ ] Unit tests for follow-up mode, template selection, streaming prefixes

## Phase 2 (Frontend) – Placeholder

Frontend work will be tracked separately once backend adaptive pipeline is stable.

---

## Next Steps (Priority Order)

1. **Refactor main pipeline** - Create a new orchestrator that integrates all adaptive stages
2. **Extend checkpoint system** - Add checkpoint support for new artifacts
3. **Add streaming prefixes** - Update streaming.py with new stage prefixes
4. **Create JSON schemas** - Define Pydantic models and export JSON schemas
5. **Add comprehensive unit tests** - Test follow-up mode, template selection, and streaming
