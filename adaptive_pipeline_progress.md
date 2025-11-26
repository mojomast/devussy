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

- [x] `src/pipeline/design_generator.py` implemented with complexity-aware branching (mock, LLM-free)
- [x] `src/pipeline/devplan_generator.py` implemented with dynamic phase count (mock, LLM-free)
- [ ] Template variants wired in (minimal / standard / detailed)
- [x] Unit tests for branching logic using stubbed data (`tests/unit/test_adaptive_design_generator.py`, `tests/unit/test_adaptive_devplan_generator.py`)

## Milestone 4: Pipeline Integration

- [x] `src/pipeline/mock_adaptive_pipeline.py` implements end-to-end mock adaptive pipeline
- [x] `tests/integration/test_mock_adaptive_pipeline.py` (full adaptive pipeline with mocks only)
- [x] `tests/harness/pipeline_test_harness.py` and `tests/harness/test_pipeline_test_harness.py` (mock adaptive pipeline scenarios)
- [ ] `src/pipeline/main_pipeline.py` refactored to include new stages (mock-only)
- [ ] Checkpointing extended to new stages
- [ ] Streaming hooks stubbed for new stages

## Phase 2 (Frontend) – Placeholder

Frontend work will be tracked separately once backend adaptive pipeline is stable.
