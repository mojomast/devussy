# Jinja Gap Analysis

This document tracks valuable data produced by the pipeline but not currently used in Jinja templates.

## 1. Project Design
- **Unused Field**: `mitigations`
    - **Source**: `ProjectDesign.mitigations` (List[str])
    - **Description**: Strategies to mitigate identified challenges.
    - **Proposal**: Add a "Mitigation Strategies" subsection under "Challenges" in `project_design.jinja` and `basic_devplan.jinja`.
- **Unused Field**: `raw_llm_response`
    - **Source**: `ProjectDesign.raw_llm_response` (str)
    - **Description**: Full markdown response from the LLM.
    - **Proposal**: Add to a "Debug/Verbose" section if `detail_level == 'verbose'`.

## 2. Development Plan
- **Unused Field**: `details` (Sub-bullets)
    - **Source**: `DevPlanStep.details` (List[str])
    - **Description**: Concrete sub-steps or details for a plan step.
    - **Proposal**: Render these as nested bullets in `docs/devplan_report.jinja` and `detailed_devplan.jinja`.

## 3. Repository Context
- **Unused Field**: `description`, `version`, `author`
    - **Source**: `RepoAnalysis.project_metadata`
    - **Description**: Metadata extracted from manifest files (package.json, pyproject.toml, etc.).
    - **Proposal**: Display in `basic_devplan.jinja` and `handoff_prompt.jinja` header if available.
- **Unused Field**: `errors`
    - **Source**: `RepoAnalysis.errors`
    - **Description**: Errors encountered during repository analysis.
    - **Proposal**: Show a warning block in templates if errors exist.

## 4. General
- **Missing**: `detail_level` control
    - **Description**: No standard way to toggle between summary and verbose views.
    - **Proposal**: Implement `detail_level` context variable ("short", "normal", "verbose") across all templates.
