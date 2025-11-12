# Task Group Update Ritual and Anchors

This document defines the non‑negotiable update ritual and the stable anchors that all implementation agents (human or AI) must use when updating project artifacts.

## Summary

- Work in groups of N tasks (task_group_size). Default: 3 for devplan generation, 5 for handoff.
- After each group, pause and update:
  1. devplan.md – Progress log and next task group
  2. phase.md (active phase) – Outcomes and blockers
  3. handoff (handoff_prompt.md or the generated prompt) – Status snapshot and next steps
- Only then proceed to the next group.

If a file does not exist, create it and include the anchors below.

## Anchors (Do Not Remove)

Use these stable markers so any model can find and update the right sections deterministically.

- devplan.md
  - <!-- PROGRESS_LOG_START --> ... <!-- PROGRESS_LOG_END -->
  - <!-- NEXT_TASK_GROUP_START --> ... <!-- NEXT_TASK_GROUP_END -->

- phaseX.md (the current phase file)
  - <!-- PHASE_PROGRESS_START --> ... <!-- PHASE_PROGRESS_END -->

- handoff (handoff_prompt.md or the generated prompt)
  - <!-- HANDOFF_NOTES_START --> ... <!-- HANDOFF_NOTES_END -->

## Minimal content at each update

- devplan.md → Progress Log: bullet list of just‑completed steps with step numbers; Next Task Group: the next N steps to execute.
- phase.md → Phase Progress: 2–5 bullets summarizing outcomes, links to changed files, and blockers.
- handoff → Short status (completed, in progress, next N steps) and any decisions/tradeoffs.

### Example: devplan.md

```
<!-- PROGRESS_LOG_START -->
- Completed 2.1 Implement DB schema – added tables, indexes, migration file
- Completed 2.2 Connection manager – pooled connections, retry, logging
<!-- PROGRESS_LOG_END -->

<!-- NEXT_TASK_GROUP_START -->
- 2.3: Write unit tests for DB layer
- 2.4: Code quality checks (black/flake8/isort)
- 2.5: Commit changes (feat: db layer)
<!-- NEXT_TASK_GROUP_END -->
```

### Example: phase.md

```
<!-- PHASE_PROGRESS_START -->
- Built DB schema and connection manager
- Added tests skeletons; coverage at 62%
- Follow‑ups: improve error handling for connection retries
<!-- PHASE_PROGRESS_END -->
```

### Example: handoff_prompt.md

```
<!-- HANDOFF_NOTES_START -->
Status: Phase 2 at 2/8 steps complete (2.1, 2.2).
Next: 2.3 tests, 2.4 quality, 2.5 commit (group size = 3).
Decisions: chose pooled connections with exponential backoff.
<!-- HANDOFF_NOTES_END -->
```

## Configuring task group size

Programmatic API:
- Basic plan generation: BasicDevPlanGenerator.generate(..., task_group_size=3)
- Detailed plan generation: DetailedDevPlanGenerator.generate(..., task_group_size=3)
- Handoff prompt: HandoffPromptGenerator.generate(..., task_group_size=5)

CLI wrappers can pass these values into the pipeline; otherwise defaults apply.
