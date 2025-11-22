# Jinja Context Schema

This document defines the expected context structure for each template.

## Core Pipeline Templates

### `project_design.jinja`

```python
{
    "project_name": str,
    "languages": list[str],
    "frameworks": list[str],       # Optional, can be []
    "apis": list[str],              # Optional, can be []
    "requirements": str
}
```

**Source**: `src/pipeline/project_design.py` (line 52-58)

---

### `basic_devplan.jinja`

```python
{
    "project_design": {
        "project_name": str,
        "objectives": list[str],
        "tech_stack": list[str],
        "architecture_overview": str,
        "dependencies": list[str],
        "challenges": list[str],
        "mitigations": list[str],         # NEW: Now rendered
        "complexity": str | None,
        "estimated_phases": int | None
    },
    "detail_level": str,                  # NEW: "short" | "normal" | "verbose"
    "repo_context": {                     # Optional
        "project_type": str,
        "structure": {
            "source_dirs": list[str],
            "test_dirs": list[str],
            "config_dirs": list[str],
            "has_ci": bool
        },
        "dependencies": dict[str, list[str]],  # e.g., {"python": ["fastapi", ...]}
        "metrics": {
            "total_files": int,
            "total_lines": int
        },
        "patterns": {
            "test_frameworks": list[str],
            "build_tools": list[str]
        },
        # NEW: from project_metadata
        "project_name": str | None,
        "description": str | None,
        "version": str | None,
        "author": str | None
    },
    "code_samples": str | None,           # Optional formatted code samples
    "interactive_session": {              # Optional
        "question_count": int | None
    }
}
```

**Source**: `src/pipeline/basic_devplan.py` (line 53-64)  
**Repo Context Source**: `src/interview/repository_analyzer.py::RepoAnalysis.to_prompt_context()` (line 76-124)

---

### `detailed_devplan.jinja`

```python
{
    "detail_level": str,                  # NEW: "short" | "normal" | "verbose"
    "repo_context": { ... },              # Same as basic_devplan
    "code_samples": str | None,
    "interactive_context": bool | None,   # Presence flag
    "phase_number": int,
    "phase_title": str,
    "phase_description": str | None,
    "project_name": str,
    "tech_stack": list[str]
}
```

**Source**: `src/pipeline/detailed_devplan.py`

---

### `design_review.jinja`

```python
{
    "project_design": {
        "project_name": str,
        "objectives": list[str],
        "tech_stack": list[str],
        "dependencies": list[str],
        "challenges": list[str]
    }
}
```

**Output**: JSON with `status`, `summary`, `issues[]`, `project_design`

---

### `handoff_prompt.jinja`

```python
{
    "project_name": str,
    "detail_level": str,                  # NEW: "short" | "normal" | "verbose"
    "repo_context": { ... },              # Same as basic_devplan (optional)
    "code_samples": bool | str | None,    # Presence flag or content
    "current_phase_number": int,
    "current_phase_name": str,
    "next_task_id": str,
    "next_task_description": str,
    "blockers": str | None                # Optional, defaults to "None known"
}
```

**Source**: `src/pipeline/handoff_prompt.py`

---

### `hivemind_arbiter.jinja`

```python
{
    "original_prompt": str,
    "drones": list[{
        "id": str,
        "content": str
    }]
}
```

**Source**: `src/pipeline/hivemind.py`

---

### `interactive_session_report.jinja`

```python
{
    "session": {
        "project_name": str,
        "session_id": str,
        "created_at": str,                # ISO format or human-readable
        "last_updated": str,
        "answers": dict[str, any]         # User responses to questions
    }
}
```

**Source**: `src/pipeline/interactive_session.py` (assumed)

---

## Documentation Templates

### `docs/devplan_report.jinja`

```python
{
    "timestamp": str,
    "devplan": {
        "project_name": str,
        "estimated_duration": str | None,
        "project_summary": str,
        "phases": list[{
            "number": int,
            "name": str,
            "completed": bool,
            "estimated_duration": str | None,
            "prerequisites": list[str],
            "description": str,
            "steps": list[{
                "number": str,              # e.g., "1.1"
                "title": str,
                "completed": bool,
                "description": str,
                "deliverables": list[str] | None,
                "commit_message": str | None
            }],
            "completed_steps": int
        }],
        "current_phase": {
            "number": int,
            "name": str
        } | None,
        "next_task": str | None,
        "milestones": list[any],
        "external_dependencies": list[any],
        "internal_dependencies": list[any],
        "success_criteria": list[str]
    }
}
```

---

### `docs/project_design_report.jinja`

**Note**: This template expects a different structure than core pipeline's `ProjectDesign` model.

```python
{
    "timestamp": str,
    "project_design": {
        "project_name": str,
        "status": str | None,
        "summary": str,
        "objectives": str,                # NOTE: String, not list
        "technologies": list[{
            "name": str,
            "purpose": str
        }],
        "dependencies": list[{
            "name": str,
            "version": str,
            "reason": str
        }],
        "architecture": str,
        "components": list[{
            "name": str,
            "purpose": str,
            "implementation": str
        }],
        "development_approach": str,
        "risks": list[{
            "category": str,
            "description": str,
            "mitigation": str
        }],
        "success_criteria": list[str],
        "next_steps": str
    }
}
```

**Action Required**: Align this with core `ProjectDesign` model or create adapter.

---

### `docs/handoff_report.jinja`

Complex schema with many optional fields. See template for full structure.

---

## Common Patterns

### Optional Fields

Use `| default(...)` for safe rendering:
```jinja
{{ field | default("Not specified") }}
```

### List Handling

Check if list exists and is not empty:
```jinja
{% if items %}
{% for item in items %}
...
{% endfor %}
{% endif %}
```

### Detail Level

Check detail level for conditional rendering:
```jinja
{% if detail_level == 'verbose' %}
...verbose content...
{% endif %}
```

### Safe Defaults

Python context builders should provide safe defaults:
- Empty lists instead of `None`
- Empty strings instead of `None` (where appropriate)
- Use `| default(...)` in templates as fallback
