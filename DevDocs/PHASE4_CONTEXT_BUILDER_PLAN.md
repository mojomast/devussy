# Phase 4: Context Builder Updates - Implementation Plan

## Goal
Ensure all Python context builders populate the fields that the upgraded templates expect, including:
1. `detail_level` control for all templates
2. All existing model fields are being utilized
3. Safe defaults for optional fields

## Current State Analysis

### ✅ Already Working
- **`ProjectDesign.mitigations`**: Model field exists, templates use it via `section_challenges()` macro
- **`RepoAnalysis.project_metadata`**: Already surfaced in `to_prompt_context()` method
- **`DevPlanStep.details`**: Model field exists, ready for template rendering

### ❌ Missing
- **`detail_level`**: Not passed in any context builder
- **Templates not using `DevPlanStep.details`**: Need to verify templates render this field

## Tasks

### Task 1: Add `detail_level` to Configuration Model
**File**: `src/config.py`

Add a new configuration field to control template verbosity:
```python
class AppConfig:
    # ... existing fields ...
    detail_level: str = "normal"  # Options: "short", "normal", "verbose"
```

### Task 2: Update `basic_devplan.py` Context Builder
**File**: `src/pipeline/basic_devplan.py`

Update the `generate()` method to include `detail_level` in context:

**Current**:
```python
context = {
    "project_design": project_design,
    "task_group_size": task_group_size,
}
```

**Updated**:
```python
context = {
    "project_design": project_design,
    "task_group_size": task_group_size,
    "detail_level": llm_kwargs.get("detail_level", "normal"),
}
```

### Task 3: Update `detailed_devplan.py` Context Builder
**File**: `src/pipeline/detailed_devplan.py`

Add `detail_level` to the context passed to the template.

### Task 4: Update `handoff_prompt.py` Context Builder  
**File**: `src/pipeline/handoff_prompt.py`

Add `detail_level` to the handoff context.

### Task 5: Update `project_design.py` Context Builder
**File**: `src/pipeline/project_design.py`

Add `detail_level` if the template uses it.

### Task 6: Verify Template Usage of `DevPlanStep.details`
**Files**: `templates/detailed_devplan.jinja`, `templates/docs/devplan_report.jinja`

Ensure these templates render the `details` sub-bullets for each step.

### Task 7: Add Debug Logging for Unused Context Keys
**File**: `src/templates.py`

Add optional debug logging to track which context keys are not used by templates:

```python
def render_template(template_name: str, context: dict) -> str:
    # ... existing code ...
    
    # Debug: Log unused context keys (dev mode only)
    if os.getenv("DEV_MODE") or os.getenv("DEBUG_TEMPLATES"):
        # Track which keys were accessed during rendering
        # This requires wrapping the context in a tracking dict
        pass
```

## Schema Summary

### `basic_devplan.jinja` Context Schema
```python
{
    "project_design": ProjectDesign,  # Pydantic model
    "task_group_size": int,
    "detail_level": str,              # NEW: "short" | "normal" | "verbose"
    "repo_context": dict | None,      # From RepoAnalysis.to_prompt_context()
    "code_samples": str | None,
}
```

### `detailed_devplan.jinja` Context Schema
```python
{
    "repo_context": dict | None,
    "code_samples": str | None,
    "detail_level": str,              # NEW
    "phase_number": int,
    "phase_title": str,
    "phase_description": str | None,
    "project_name": str,
    "tech_stack": list[str],
}
```

### `handoff_prompt.jinja` Context Schema
```python
{
    "project_name": str,
    "repo_context": dict | None,
    "detail_level": str,              # NEW
    "code_samples": bool | str | None,
    "current_phase_number": int,
    "current_phase_name": str,
    "next_task_id": str,
    "next_task_description": str,
    "blockers": str | None,
}
```

## Verification Steps

1. **Run the pipeline** on a test project
2. **Check generated context samples** in `DevDocs/JINJA_DATA_SAMPLES/`
3. **Verify `detail_level` appears** in all context JSON files
4. **Manually test** with different `detail_level` values
5. **Ensure backward compatibility** - templates should work without `detail_level` via safe defaults

## Success Criteria

- [ ] All templates can access `detail_level` via `{{ detail_level | default("normal") }}`
- [ ] Context builders provide safe defaults for all optional fields
- [ ] No breaking changes to existing templates
- [ ] Documentation updated with new schema
