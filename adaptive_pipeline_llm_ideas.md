# Adaptive Pipeline LLM Integration Ideas

This document captures the intended **LLM-backed behavior** for each mocked component in the adaptive pipeline. Once the mock-only backend is stable and tested, this will be the source of truth for designing prompts, schemas, and API integration.

---

## 1. Complexity Analyzer (`src/interview/complexity_analyzer.py`)

### Current Mock Behavior

- Pure-Python heuristics infer:
  - `project_type_bucket` from `project_type` string (CLI, API, Web App, SaaS, etc.).
  - `technical_complexity_bucket` from keywords in `requirements` / `frameworks`.
  - `integration_bucket` from simple counts of `apis`.
  - `team_size_bucket` from `team_size` string or number.
- Computes `score`, `estimated_phase_count`, `depth_level`, and a simple `confidence`.

### Future LLM-Powered Behavior (Ideas)

- Use an LLM to:
  - Read the full **interview transcript + extracted data** and produce a structured `ComplexityProfile` JSON object.
  - Justify each bucket choice with a short natural-language rationale (for transparency UI later).
  - Infer hidden complexity signals (compliance, data sensitivity, latency/throughput goals) that may adjust score or add flags.
- LLM prompt shape:
  - Input: summary of project + key fields (`project_type`, `requirements`, `frameworks`, `apis`, `team_size`, repo metrics).
  - Output JSON keys must match the rubric in `handoff.md`:
    - `project_type_bucket`, `technical_complexity_bucket`, `integration_bucket`, `team_size_bucket`.
    - `complexity_score`, `estimated_phase_count`, `depth_level`, `confidence`.
    - Optional: `rationale` (short markdown string).
- Validation strategy:
  - Compare LLM-produced `complexity_score` against rubric-computed fallback; if they diverge by >1 point, prefer rubric and mark low confidence.
  - Clamp all values into valid ranges and enum sets.

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

## 6. How to Use This Doc Later

- When the mock-only backend is green:
  - For each module, derive:
    - Prompt templates.
    - JSON schemas.
    - Error-handling and validation rules.
  - Generate a focused **devplan phase** for LLM integration using these sections as inputs.
