# Handoff Prompt: 
<!-- HANDOFF_VERSION: 2.0 -->

> **QuickStart:** Read QUICK_STATUS → Read PHASE_TASKS → Execute → Update anchors → Handoff

### Repository Context
- **Type**: python
- **Files**: 42
- **Lines**: 1337
- **Description**: A test application
- **Version**: 1.0.0
- **Author**: Test Author





## Quick Status (Read This Always)
<!-- QUICK_STATUS_START -->
- Active Phase:  - 
- Next Immediate Task:  - 
- Blockers: None known
<!-- QUICK_STATUS_END -->

## How to Continue Development
<!-- DEV_INSTRUCTIONS_START -->
1. Read devplan.md between <!-- NEXT_TASK_GROUP_START --> and <!-- NEXT_TASK_GROUP_END --> only (~150 tokens).
2. Open phase.md and read only <!-- PHASE_TASKS_START --> to <!-- PHASE_TASKS_END --> (~100 tokens).
3. Execute the next group of steps in order (do not skip ahead).
4. After completing the group, update:
   - devplan.md: add one line to PROGRESS_LOG and refresh NEXT_TASK_GROUP.
   - phase.md: add one line to PHASE_OUTCOMES (or legacy PHASE_PROGRESS).
   - This file: update QUICK_STATUS only (3 lines, ~30 seconds).
5. Stop after this group. Handoff if more work is needed.
<!-- DEV_INSTRUCTIONS_END -->

## Token Budget
<!-- TOKEN_RULES_START -->
**Stay under 500 tokens per turn by reading ONLY anchored sections:**

| File | Section | Read? | Tokens |
|------|---------|-------|--------|
| devplan.md | NEXT_TASK_GROUP_START to END | ✅ | ~150 |
| devplan.md | PROGRESS_LOG_START to END | ✅ if needed | ~100 |
| phase.md | PHASE_TASKS_START to END | ✅ | ~100 |
| phase.md | PHASE_OUTCOMES_START to END | ✅ if needed | ~50 |
| handoff_prompt.md | QUICK_STATUS_START to END | ✅ | ~50 |
| Everything else | (full files, verbose sections) | ❌ NEVER | - |

**If you're reading more than 500 tokens, you're reading the wrong sections.**
<!-- TOKEN_RULES_END -->

## File References

**For static or rarely-changing information, read these once and reference thereafter:**
- project_design.md — Architecture, tech stack, core decisions.
- README.md — Setup instructions, development workflow, code quality standards.
- devplan.md — Main dashboard with all phases.

---

## Active Anchors
<!-- HANDOFF_NOTES_START -->
<!-- HANDOFF_NOTES_END -->