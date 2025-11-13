# Handoff Template Fix - Clean Version

## Problem Summary

Your current `handoff_prompt.md.j2` template is generating ~2900 tokens of which **~1900 tokens (65%) is noise** consisting of:

1. **Redundant repetition** - Same rules/rituals explained 4-5 times
2. **Boilerplate that belongs in README** - Dev workflow, code quality standards
3. **Static context that belongs in project_design.md** - Architecture diagrams, tech stack
4. **Meta-noise** - Instructions about when to generate a handoff (shouldn't be in the handoff!)

---

## New Clean Handoff Template

Replace your `templates/handoff_prompt.md.j2` with this:

```jinja2
# Handoff Prompt: {{ project_name }}
<!-- HANDOFF_VERSION: 2.0 -->

> **QuickStart:** Read QUICK_STATUS → Read PHASE_TASKS → Execute → Update anchors → Handoff

## Quick Status (Read This Always)
<!-- QUICK_STATUS_START -->
- Active Phase: {{ current_phase_number }} - {{ current_phase_name }}
- Next Immediate Task: {{ next_task_id }} - {{ next_task_description }}
- Blockers: {{ blockers | default('None known', true) }}
<!-- QUICK_STATUS_END -->

## How to Continue Development
<!-- DEV_INSTRUCTIONS_START -->
1. Read `devplan.md` between `NEXT_TASK_GROUP_START` and `END` only (~150 tokens)
2. Open `phase{{ current_phase_number }}.md` and read only `PHASE_TASKS_START` to `END` (~100 tokens)
3. Execute the next 5-step group in order
4. After completing all 5 steps, update:
   - `devplan.md`: Add 1 line to PROGRESS_LOG, update NEXT_TASK_GROUP
   - `phase{{ current_phase_number }}.md`: Add 1 line to PHASE_OUTCOMES
   - **This file**: Update QUICK_STATUS only (3 lines, 30 seconds)
5. Stop. Do not continue beyond the group. Handoff when done.

**CRITICAL:** Do NOT append progress reports or detailed logs to this file. That's what devplan.md and phaseN.md are for.
<!-- DEV_INSTRUCTIONS_END -->

## Token Budget
<!-- TOKEN_RULES_START -->
**Stay under 500 tokens per turn by reading ONLY anchored sections:**

| File | Section | Read? | Tokens |
|------|---------|-------|--------|
| devplan.md | NEXT_TASK_GROUP_START to END | ✅ | ~150 |
| devplan.md | PROGRESS_LOG_START to END | ✅ if needed | ~100 |
| phaseN.md | PHASE_TASKS_START to END | ✅ | ~100 |
| phaseN.md | PHASE_OUTCOMES_START to END | ✅ if needed | ~50 |
| handoff_prompt.md | QUICK_STATUS_START to END | ✅ | ~50 |
| Everything else | (full files, verbose sections) | ❌ NEVER | - |

**If you're reading more than 500 tokens, you're reading wrong sections.**
<!-- TOKEN_RULES_END -->

## File References

**For static/rarely-changing information, see these files (read once, reference thereafter):**
- `project_design.md` — Architecture, tech stack, core decisions
- `README.md` — Setup instructions, dev workflow, code quality standards
- `devplan.md` (main dashboard) — All 9 phases overview

---

## Active Anchors
<!-- HANDOFF_NOTES_START -->
<!-- HANDOFF_NOTES_END -->
```

---

## Template Variables Required

Make sure your handoff generator passes these variables to Jinja2:

```python
context = {
    'project_name': 'cookiepuss',
    'current_phase_number': 1,
    'current_phase_name': 'Project Initialization & Tooling',
    'next_task_id': '1.1',
    'next_task_description': 'Initialize repository structure and basic files',
    'blockers': 'None known',  # or specific blocker text
}
```

---

## What Gets Deleted

Remove these sections ENTIRELY from your template:

### ❌ DELETE "Next Steps (Priority Order)"
This is redundant with devplan.md NEXT_TASK_GROUP_START. Agents should read devplan, not the handoff.

### ❌ DELETE "Development Workflow Rules"  
This belongs in `README.md` or `CONTRIBUTING.md` and should be written ONCE, not in every handoff. Example:

**Move to README.md:**
```markdown
## Development Workflow

### Code Development
- Follow steps sequentially—do not skip ahead
- After each group, update the devplan
- Commit changes with conventional commits

### Git Workflow
- Commit style: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- Example: `git commit -m "feat: implement X"`

### Code Quality
- Run before committing: `black`, `isort`, `flake8`, `pytest`
- Target: >80% test coverage
```

### ❌ DELETE "Key Technical Context" with architecture diagram
This belongs in `project_design.md` and never changes. Point to it instead with a 1-line reference.

### ❌ DELETE "When to Generate a New Handoff Prompt"
Meta-instructions don't belong in the handoff. Put in your devussy README instead.

### ❌ DELETE "RESUME" Contract section
This is a duplicate of DEV_INSTRUCTIONS. Keep only one version.

### ❌ DELETE redundant "Context Budget" and "Update Ritual" sections
Keep only ONE copy of TOKEN_RULES and one copy of UPDATE_RITUAL instructions.

### ❌ DELETE "Anchor Reference Guide" if it repeats information
It's already in devplan.md and TOKEN_RULES. Don't repeat it.

---

## Result

**Old handoff:** ~2900 tokens  
**New handoff:** ~1000 tokens  
**Noise reduction:** 65%

Every section now answers ONE clear question:
- **QUICK_STATUS** → "Where are we right now?"
- **DEV_INSTRUCTIONS** → "What do I do next?"
- **TOKEN_RULES** → "How do I read efficiently?"
- **File References** → "Where do I find static info?"

---

## Handoff Generator Update

Update your `src/generators/handoff_prompt_generator.py` to use the clean template:

```python
class HandoffPromptGenerator:
    def generate(self, 
                 project_name: str,
                 current_phase: int,
                 phase_name: str,
                 next_task_id: str,
                 next_task_desc: str,
                 blockers: str = 'None known') -> str:
        """Generate minimal handoff prompt with NO boilerplate."""
        
        template_path = Path(__file__).parent.parent / \
                       'templates' / 'handoff_prompt_clean.md.j2'
        
        with open(template_path) as f:
            template = Template(f.read())
        
        context = {
            'project_name': project_name,
            'current_phase_number': current_phase,
            'current_phase_name': phase_name,
            'next_task_id': next_task_id,
            'next_task_description': next_task_desc,
            'blockers': blockers,
        }
        
        # Render and validate
        content = template.render(**context)
        
        # Ensure critical anchors exist
        from ..utils.anchor_utils import ensure_anchors_exist
        required = ['QUICK_STATUS', 'DEV_INSTRUCTIONS', 'TOKEN_RULES']
        all_found, missing = ensure_anchors_exist(content, required)
        
        if not all_found:
            raise ValueError(f"Generated handoff missing anchors: {missing}")
        
        return content
```

---

## Before/After Comparison

### BEFORE (Noisy)
```
# Handoff Prompt: cookiepuss

## Quick Status
- Active Phase: None
- Next Task: 1.1
- Blockers: None

## How to Continue Development
[Good instructions]

## Token Optimization Rules
[Good rules]

## Next Steps (Priority Order)  ← NOISE: Redundant
1. 1.1: Initialize repository...
2. 1.2: Add basic configuration...

## Development Workflow Rules  ← NOISE: Belongs in README
- Follow steps sequentially
- Commit with feat:/fix:/docs:
- Run black, flake8, pytest

## Key Technical Context  ← NOISE: Belongs in project_design.md
### Architecture
[Large diagram]

### Dependencies
Not specified

### Configuration
Not specified

## When to Generate a New Handoff  ← NOISE: Meta-instructions
Stop when phase finishes...

## Task Group Size and Update Ritual  ← NOISE: Duplicate
After each group of 5 steps...

## RESUME Contract  ← NOISE: Duplicate of How to Continue
1) Identify current phase...
2) Read next 5 steps...

## Context Budget (Read-Minimal Rules)  ← NOISE: Duplicate of Token Rules
Read only anchored sections...

## Update Ritual (Non-negotiable)  ← NOISE: Already explained above
After each group of 5 steps...
```

**Total: 47% noise, ~1900 tokens of repetition/boilerplate**

### AFTER (Clean)
```
# Handoff Prompt: cookiepuss

## Quick Status
- Active Phase: None
- Next Task: 1.1
- Blockers: None

## How to Continue Development
[Clear 5-point instructions]

## Token Budget
[Clear table showing what to read]

## File References
For static info, see: project_design.md, README.md

---

## Active Anchors
[Empty, ready for future updates]
```

**Total: <1000 tokens, zero noise, all signal**

---

## Implementation Checklist

- [ ] Delete "Next Steps (Priority Order)" section
- [ ] Delete "Development Workflow Rules" section  
- [ ] Move content to README.md if needed
- [ ] Delete "Key Technical Context" section
- [ ] Add 1-line reference to project_design.md instead
- [ ] Delete "When to Generate a New Handoff Prompt"
- [ ] Delete "RESUME" Contract (merge into DEV_INSTRUCTIONS)
- [ ] Delete redundant "Context Budget" section
- [ ] Delete redundant "Update Ritual" sections  
- [ ] Keep only ONE "TOKEN_RULES" section
- [ ] Validate final handoff is <1200 tokens
- [ ] Test that agents can navigate with QUICK_STATUS alone
- [ ] Commit new clean template

---

## Why This Works

1. **Agents don't need to read boilerplate** - GitHub workflow standards, code quality rules, architecture diagrams are static and should be in README/docs, not every handoff
2. **Repetition is toxic** - Seeing the same instruction 4x creates doubt and confusion. Say it once, clearly
3. **Handoff is a navigation document** - Not a reference manual. It should be ~1000 tokens: "Here's where you are, here's what to do next, here's how to read efficiently, and here are references for static info"
4. **Future handoffs can be regenerated fresh** - You don't need to keep the kitchen sink in every prompt

This approach follows the **principle of minimal viable context** — agents get exactly what they need for the current task, plus pointers to where static info lives.

