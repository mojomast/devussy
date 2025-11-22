# JINJA_CONTEXT_MAP

This document maps Jinja templates to their context variables.

## Templates

### project_design.jinja
- **Rendered by**: `src/pipeline/project_design.py`
- **Context Keys**:
    - `project_name`
    - `languages`
    - `frameworks`
    - `apis`
    - `requirements`

### basic_devplan.jinja
- **Rendered by**: `src/pipeline/basic_devplan.py`
- **Context Keys**:
    - `repo_context` (optional)
        - `project_type`
        - `structure`
            - `source_dirs`
            - `test_dirs`
            - `config_dirs`
            - `has_ci`
        - `dependencies`
        - `metrics`
            - `total_files`
            - `total_lines`
        - `patterns`
            - `test_frameworks`
            - `build_tools`
    - `code_samples` (optional)
    - `interactive_session` (optional)
        - `question_count`
    - `project_design`
        - `project_name`
        - `objectives`
        - `tech_stack`
        - `architecture_overview`
        - `dependencies`
        - `challenges`
        - `complexity`
        - `estimated_phases`

### detailed_devplan.jinja
- **Rendered by**: `src/pipeline/detailed_devplan.py`
- **Context Keys**:
    - `repo_context` (optional)
        - `project_type`
        - `structure`
        - `patterns`
        - `dependencies`
    - `code_samples` (optional)
    - `interactive_context` (optional)
    - `phase_number`
    - `phase_title`
    - `phase_description` (optional)
    - `project_name`
    - `tech_stack`

### design_review.jinja
- **Rendered by**: `src/pipeline/design_review.py`
- **Context Keys**:
    - `project_design`
        - `project_name`
        - `objectives`
        - `tech_stack`
        - `dependencies`
        - `challenges`

### interactive_session_report.jinja
- **Rendered by**: `src/pipeline/interactive_session.py`
- **Context Keys**:
    - `session`
        - `project_name`
        - `session_id`
        - `created_at`
        - `last_updated`
        - `answers`

### docs/devplan_report.jinja
- **Rendered by**: `src/pipeline/docs/devplan_report.py`
- **Context Keys**:
    - `timestamp`
    - `devplan`
        - `project_name`
        - `phases`
        - `estimated_duration`
        - `project_summary`
        - `current_phase`
        - `next_task`
        - `milestones`
        - `external_dependencies`
        - `internal_dependencies`
        - `success_criteria`
- **Rendered by**: `src/pipeline/handoff_prompt.py`
- **Context Keys**:
    - `project_name`
    - `repo_context` (optional)
        - `project_type`
        - `metrics`
        - `structure`
        - `patterns`
    - `code_samples` (optional)
    - `current_phase_number`
    - `current_phase_name`
    - `next_task_id`
    - `next_task_description`
    - `blockers` (optional)

### hivemind_arbiter.jinja
- **Rendered by**: `src/pipeline/hivemind.py`
- **Context Keys**:
    - `original_prompt`
    - `drones` (list)
        - `id`
        - `content`
