# Template Design Notes

This document describes the current template architecture after the Jinja upgrade.

## Overview

Templates are located in `templates/` and use Jinja2 for rendering. All templates support optional `detail_level` control ("short", "normal", "verbose") to adjust output verbosity.

## Shared Macros

### `_shared_macros.jinja`

Reusable macros for common sections:

- **`project_header(project_name)`**: Renders project title
- **`section_objectives(objectives)`**: Renders objectives list
- **`section_tech_stack(tech_stack)`**: Renders technology stack
- **`section_architecture(architecture_overview)`**: Renders architecture overview
- **`section_challenges(challenges, mitigations)`**: Renders challenges with paired mitigations
- **`section_repo_context(repo_context, detail_level='normal')`**: Renders repository context including:
  - Project type, files, lines
  - Description, version, author (if available)
  - Dependencies (verbose mode only)

### `_circular_macros.jinja`

Workflow macros for the circular development pattern (handoff prompts, anchor management).

## Template Structure

### Core Pipeline Templates

#### `project_design.jinja`
**Purpose**: LLM prompt for generating project design  
**Sections**: Project information, task requirements, output format  
**Context Keys**: `project_name`, `languages`, `frameworks`, `apis`, `requirements`  
**Output**: LLM-readable prompt (not markdown)

#### `basic_devplan.jinja`
**Purpose**: LLM prompt for generating high-level development plan  
**Sections**:
- Repository context (uses `section_repo_context` macro)
- Code samples (if available)
- Interactive session context
- Project design (uses shared macros)
- Task requirements

**Context Keys**: `project_design`, `repo_context`, `code_samples`, `interactive_session`  
**Macros Used**: `section_repo_context`, `project_header`, `section_objectives`, `section_tech_stack`, `section_architecture`, `section_challenges`  
**Output**: LLM-readable prompt

**Notable**: Now includes mitigations alongside challenges via `section_challenges` macro.

#### `detailed_devplan.jinja`
**Purpose**: LLM prompt for generating detailed phase implementation steps  
**Sections**:
- Repository context (uses `section_repo_context`)
- Code samples
- Interactive context
- Phase information
- Project context (uses shared macros)

**Context Keys**: `repo_context`, `code_samples`, `interactive_context`, `phase_number`, `phase_title`, `phase_description`, `project_name`, `tech_stack`  
**Macros Used**: `section_repo_context`, `project_header`, `section_tech_stack`  
**Output**: LLM-readable prompt

#### `design_review.jinja`
**Purpose**: LLM prompt for reviewing and fixing project design  
**Context Keys**: `project_design`  
**Output**: JSON (strict schema)

#### `handoff_prompt.jinja`
**Purpose**: Markdown handoff document for next developer/agent  
**Sections**:
- Quick status
- Repository context (uses `section_repo_context`)
- Code samples note
- Development instructions
- Token budget rules
- Active anchors

**Context Keys**: `project_name`, `repo_context`, `code_samples`, `current_phase_number`, `current_phase_name`, `next_task_id`, `next_task_description`, `blockers`  
**Macros Used**: `section_repo_context`  
**Output**: Markdown document

#### `hivemind_arbiter.jinja`
**Purpose**: LLM prompt for synthesizing multiple devplan proposals  
**Context Keys**: `original_prompt`, `drones` (list of `{id, content}`)  
**Output**: LLM-readable prompt

#### `interactive_session_report.jinja`
**Purpose**: Markdown report of interactive session  
**Context Keys**: `session` (with `project_name`, `session_id`, `created_at`, `last_updated`, `answers`)  
**Output**: Markdown document

### Documentation Templates

#### `docs/project_design_report.jinja`
**Purpose**: Formal project design report  
**Context Keys**: `timestamp`, `project_design` (complex structure)  
**Output**: Markdown document

**Note**: This template expects a different `project_design` structure than the core pipeline (with `technologies`, `components`, `risks`, etc.). May need alignment.

#### `docs/devplan_report.jinja`
**Purpose**: Comprehensive development plan report  
**Context Keys**: `timestamp`, `devplan` (with `phases`, `milestones`, etc.)  
**Output**: Markdown document with automation anchors

#### `docs/handoff_report.jinja`
**Purpose**: Detailed handoff report  
**Context Keys**: `timestamp`, `handoff` (complex structure)  
**Output**: Markdown document with automation anchors

## Detail Level Behavior

The `detail_level` context variable controls output verbosity:

- **`"short"`**: Minimal output, core information only
- **`"normal"`** (default): Standard output
- **`"verbose"`**: Full output including all optional sections

### Current Support

- **`section_repo_context`**: Hides dependency details unless `detail_level == 'verbose'`
- **Future**: Other macros can check `{% if detail_level != "short" %}` to hide optional sections

## Design Principles

1. **DRY (Don't Repeat Yourself)**: Use shared macros for common sections
2. **Graceful Degradation**: All sections use `{% if ... %}` to handle missing data
3. **Token Awareness**: Support `detail_level` to control output size
4. **Consistency**: Use standard macro names across templates
5. **Documentation**: Include mitigations with challenges, metadata with repo context

## Future Enhancements

1. Thread `detail_level` through all templates
2. Add `detail_level` support to more macros
3. Consider macros for:
   - Dependencies rendering
   - Phase structure rendering
   - Step details (sub-bullets)
4. Align `docs/project_design_report.jinja` context with core pipeline `ProjectDesign` model
