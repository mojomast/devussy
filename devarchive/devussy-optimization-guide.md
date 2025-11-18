# Devussy Optimization Guide

**Token-Efficient Circular Development Through Anchor-Based Context Management**

---

## Executive Summary

This guide provides comprehensive recommendations for optimizing your devussy AI development pipeline to address three critical issues:

1. **Phase documents with excessive information** → Streamline to task-oriented minimal format
2. **Handoff prompt growth** → Convert from progress log to navigation document
3. **Inefficient anchor usage** → Explicit instructions for targeted context reading

**Expected Results:**
- **94% reduction** in context tokens per agent invocation (7800 → 450 tokens)
- Handoff stays **<500 tokens forever** (vs. growing to 3000+)
- **$1-2 cost savings per devplan execution**
- Clearer agent instructions reducing confusion

---

## Problem Analysis

### Issue 1: Bloated Phase Documents (~600 tokens each)

**Current State:**
- Verbose task descriptions with paragraphs of text
- Redundant prerequisites and overview sections
- Technical context mixed with task lists
- Hard for agents to extract actionable items quickly

**Impact:**
- Agents waste tokens reading unnecessary content
- Slower comprehension → more LLM calls
- Difficult to track completion status

### Issue 2: Growing Handoff File (3000+ tokens)

**Current State:**
- Every agent appends multi-paragraph progress reports
- File grows continuously throughout development
- Agents must read entire handoff each time
- Contains duplicated information from other docs

**Impact:**
- Exponentially increasing token costs
- Slower agent startup time
- Harder to find current status in noise

### Issue 3: Anchors Exist But Aren't Used

**Current State:**
- Anchors like PROGRESS_LOG_START/END are in templates
- No explicit instructions for agents to use them
- Agents default to reading entire files
- Token optimization potential is wasted

**Impact:**
- 10x more tokens consumed than necessary
- Missing opportunity for 90%+ savings
- Slow circular development loops

---

## Solution Overview

### 1. Streamlined Phase Documents (83% token reduction)

**Transform from verbose to minimal:**

```markdown
# Phase 2: Database Layer

## Tasks
<!-- PHASE_TASKS_START -->
- [ ] 2.1: Create SQLAlchemy models (User, Post, Comment) → Files: `models/`
- [ ] 2.2: Implement repository classes with CRUD → Files: `repositories/`
- [ ] 2.3: Write pytest unit tests (80% coverage) → Files: `tests/`
<!-- PHASE_TASKS_END -->

## Context (Read Only When Blocked)
<!-- PHASE_CONTEXT_START -->
SQLAlchemy ORM with Repository pattern. Session management in repositories.
<!-- PHASE_CONTEXT_END -->

## Outcomes
<!-- PHASE_OUTCOMES_START -->
<!-- Updates added as tasks complete -->
<!-- PHASE_OUTCOMES_END -->
```

**Key Changes:**
- Checkbox-style task list (like GitHub issues)
- One-line task descriptions with file paths
- Context available but not forced
- Outcomes section for learnings

### 2. Navigation-Focused Handoff (stays <500 tokens)

**Transform from progress log to navigation:**

```markdown
# Handoff Prompt
<!-- HANDOFF_VERSION: 2.0 -->

## Quick Status (Read This First)
<!-- QUICK_STATUS_START -->
- Active Phase: 2 - Database Layer
- Next Immediate Task: 2.2 - Implement repository classes
- Blockers: None
<!-- QUICK_STATUS_END -->

## How to Continue Development
<!-- DEV_INSTRUCTIONS_START -->
1. Read docs/devplan.md NEXT_TASK_GROUP section only
2. Read docs/phase2.md PHASE_TASKS section
3. Complete task and update phase2.md PHASE_OUTCOMES
4. **Do NOT append progress to this handoff file**
<!-- DEV_INSTRUCTIONS_END -->

## Token Optimization Rules
<!-- TOKEN_RULES_START -->
**CRITICAL: Use anchors to minimize token usage**

- devplan.md: Read NEXT_TASK_GROUP_START → END only
- phaseX.md: Read PHASE_TASKS_START → END only
- handoff_prompt.md: Read QUICK_STATUS_START → END only

**Never read entire files - this wastes tokens.**
<!-- TOKEN_RULES_END -->
```

**Key Changes:**
- Handoff is a **map**, not a journal
- Progress goes to phase docs (localized)
- Explicit instructions to NOT append here
- Token rules embedded in handoff itself

### 3. Explicit Anchor Instructions

**Add to every generated handoff:**

```markdown
## Anchor Reference Guide

**devplan.md:**
- NEXT_TASK_GROUP → Next 3-5 tasks (150 tokens)
- PROGRESS_LOG → Recent completions (100 tokens)

**phaseX.md:**
- PHASE_TASKS → All tasks (100 tokens)
- BLOCKERS → Current issues (20 tokens)

**handoff_prompt.md:**
- QUICK_STATUS → Current state (50 tokens)

**Token Budget: <500 tokens per turn**
```

---

## Implementation Plan

### Phase 1: Template Updates

**Files to modify:**
1. `templates/phase_doc.md.j2` → Minimal task format
2. `templates/handoff_prompt.md.j2` → Navigation structure
3. `templates/devplan.md.j2` → Emphasize anchor usage

**New structure:**
- Checkbox tasks with file paths
- Compressed context (2-3 sentences max)
- Separate outcomes section
- Embedded token optimization rules

### Phase 2: Generator Logic

**Files to modify:**
1. `src/generators/detailed_devplan_generator.py`
   - Extract action verbs from verbose descriptions
   - Compress context to essentials
   - Validate anchors in output

2. `src/generators/handoff_prompt_generator.py`
   - Generate navigation-focused structure
   - Include token optimization rules
   - Add phase status links

**Add anchor utilities:**
```python
# src/utils/anchor_utils.py
- extract_between_anchors()
- replace_anchor_content()
- ensure_anchors_exist()
- get_anchor_token_estimate()
```

### Phase 3: Update Ritual Refinement

**New ritual (every N tasks):**

1. **phaseX.md PHASE_OUTCOMES** - Add one line:
   ```
   - [timestamp] Completed X.Y: [one-line summary] - [Result]
   ```

2. **devplan.md PROGRESS_LOG** - Add one line:
   ```
   - ✓ X.Y [brief outcome] (Phase X)
   ```

3. **devplan.md NEXT_TASK_GROUP** - Update if group complete

4. **handoff_prompt.md QUICK_STATUS** - Update 3 fields only

**What NOT to do:**
- ❌ No multi-paragraph reports
- ❌ No copying full task descriptions
- ❌ No duplicate information
- ❌ No writing to handoff ARCHITECTURE section

### Phase 4: Validation & Testing

**Add validation script:**
```bash
python -m src.utils.validate_anchors docs/
```

**Checks:**
- All required anchors present
- Token estimates per section
- Handoff size stays <500 tokens
- Phase docs stay <150 tokens

**Test with actual agents:**
- Monitor whether they follow anchor instructions
- Track token usage per session
- Measure time to complete tasks

---

## Expected Token Savings

### Before Optimization
| File | Section | Tokens |
|------|---------|--------|
| phase2.md | Full file | 600 |
| devplan.md | Full file | 1500 |
| handoff_prompt.md | Full file | 3000 |
| **Total** | | **5100** |

### After Optimization
| File | Section | Tokens |
|------|---------|--------|
| phase2.md | PHASE_TASKS only | 100 |
| devplan.md | NEXT_TASK_GROUP only | 150 |
| handoff_prompt.md | QUICK_STATUS only | 50 |
| **Total** | | **300** |

### Savings
- **Per agent invocation: 94% reduction** (5100 → 300 tokens)
- **Over 100 calls: 480,000 tokens saved**
- **Cost savings: $1-2 per devplan** (at typical API rates)
- **Time savings: Faster agent comprehension**

---

## Code Examples

### Anchor Utility Functions

```python
# src/utils/anchor_utils.py

import re
from typing import Optional, Tuple

def extract_between_anchors(
    content: str, 
    anchor_name: str,
    raise_on_missing: bool = False
) -> Optional[str]:
    """Extract content between START and END anchors."""
    start = f"<!-- {anchor_name}_START -->"
    end = f"<!-- {anchor_name}_END -->"
    
    pattern = f"{re.escape(start)}(.*?){re.escape(end)}"
    match = re.search(pattern, content, re.DOTALL)
    
    return match.group(1).strip() if match else None

def replace_anchor_content(
    content: str,
    anchor_name: str,
    new_content: str
) -> str:
    """Replace content between anchors."""
    start = f"<!-- {anchor_name}_START -->"
    end = f"<!-- {anchor_name}_END -->"
    new_section = f"{start}\n{new_content}\n{end}"
    
    pattern = f"{re.escape(start)}.*?{re.escape(end)}"
    return re.sub(pattern, new_section, content, flags=re.DOTALL)
```

### Generator Updates

```python
# src/generators/detailed_devplan_generator.py

class DetailedDevPlanGenerator:
    def _extract_action(self, description: str) -> str:
        """Extract one-line action from verbose description."""
        first_sentence = description.split('.')[0]
        return first_sentence[:100] if len(first_sentence) <= 100 \
               else description[:97] + '...'
    
    def _compress_context(self, context: str) -> str:
        """Compress to 2-3 sentences max."""
        if not context:
            return None
        sentences = context.split('.')[:3]
        compressed = '. '.join(sentences).strip()
        return compressed[:297] + '...' if len(compressed) > 300 \
               else compressed
```

### Validation Script

```python
# src/utils/validate_anchors.py

REQUIRED_ANCHORS = {
    'devplan.md': ['PROGRESS_LOG', 'NEXT_TASK_GROUP'],
    'handoff_prompt.md': ['QUICK_STATUS', 'DEV_INSTRUCTIONS', 'TOKEN_RULES'],
    'phase*.md': ['PHASE_TASKS', 'PHASE_OUTCOMES', 'BLOCKERS']
}

def validate_file(file_path: Path) -> bool:
    """Validate anchors exist in file."""
    with open(file_path) as f:
        content = f.read()
    
    required = REQUIRED_ANCHORS.get(file_path.name)
    if not required:
        return True
    
    missing = [a for a in required 
               if f"<!-- {a}_START -->" not in content]
    
    if missing:
        print(f"❌ {file_path.name}: Missing {missing}")
        return False
    
    print(f"✅ {file_path.name}: Valid")
    return True
```

---

## Agent Instructions

### How to Read Files Efficiently

**Step 1: Identify what you need**
- Current task? → Read QUICK_STATUS
- Next tasks? → Read NEXT_TASK_GROUP
- Blockers? → Read BLOCKERS

**Step 2: Request only that section**

✅ **CORRECT:**
```
Read docs/devplan.md from NEXT_TASK_GROUP_START to NEXT_TASK_GROUP_END
```

❌ **WRONG:**
```
Read docs/devplan.md
```

**Step 3: Never read full files**
- Full files waste 90%+ of tokens
- You only need 1-2 sections at a time
- Budget: <500 tokens per turn

### Anchor Quick Reference

| File | Anchor | Purpose | Tokens |
|------|--------|---------|--------|
| devplan.md | NEXT_TASK_GROUP | Next 3-5 tasks | ~150 |
| devplan.md | PROGRESS_LOG | Recent completions | ~100 |
| phaseX.md | PHASE_TASKS | All tasks | ~100 |
| phaseX.md | BLOCKERS | Current issues | ~20 |
| handoff_prompt.md | QUICK_STATUS | Current state | ~50 |

**If you're reading more than 500 tokens, you're doing it wrong!**

---

## Additional Optimizations

### 1. Context Budget Enforcement

Add to handoff instructions:
```markdown
## Token Budget Guidelines
- Each agent turn: <500 tokens for context
- If you need more, you're reading too much
- Question: "Do I really need this entire section?"
```

### 2. Progress Compression

For completed phases:
```python
def compress_completed_phase(phase_doc):
    """Replace detailed outcomes with summary."""
    outcomes = extract_between_anchors(phase_doc, "PHASE_OUTCOMES")
    summary = f"Phase completed: {count_tasks(outcomes)} tasks. "
    summary += extract_key_result(outcomes)
    return replace_anchor_content(phase_doc, "PHASE_OUTCOMES", summary)
```

### 3. Handoff Versioning

Track format changes:
```markdown
<!-- HANDOFF_VERSION: 2.0 -->
```
Helps agents understand which structure they're reading.

### 4. Token Usage Tracking

Monitor actual savings:
```python
tracker = TokenTracker()
tracker.record_read('devplan.md', 'NEXT_TASK_GROUP', section, full_content)
print(tracker.report())  # Shows savings per file
```

---

## Migration Strategy

### For Existing Projects

**Step 1: Backup current docs**
```bash
cp -r docs docs.backup
```

**Step 2: Run migration script**
```bash
python -m src.cli migrate-to-v2 docs/
```

**Step 3: Validate new structure**
```bash
python -m src.utils.validate_anchors docs/
```

**Step 4: Test with agent**
- Verify agent follows new instructions
- Check handoff stays small
- Monitor token usage

### Backward Compatibility

- Keep old anchor names working
- Add new anchors without breaking old ones
- Gradual rollout across projects

---

## Success Metrics

Track these to verify improvements:

1. **Handoff size over time**
   - Target: <500 tokens forever
   - Currently: Grows to 3000+ tokens

2. **Average tokens per agent turn**
   - Target: <500 tokens
   - Currently: 3500-7800 tokens

3. **Phase doc readability**
   - Target: <150 tokens per doc
   - Currently: 500-800 tokens

4. **Agent task completion time**
   - Expect: 20-30% faster with clearer context
   - Less confusion = fewer clarification calls

5. **Cost per devplan execution**
   - Target: $1-2 savings per run
   - Over 100 runs: $100-200 saved

---

## Troubleshooting

### Agents still reading full files?

**Solution:** Make anchor instructions MORE explicit:
```markdown
**NEVER do this:** Read docs/devplan.md
**ALWAYS do this:** Read docs/devplan.md from NEXT_TASK_GROUP_START to END
```

### Handoff still growing?

**Check:**
1. Are agents ignoring DEV_INSTRUCTIONS?
2. Is UPDATE_RITUAL section clear enough?
3. Add more explicit "What NOT to do" examples

### Phase docs still verbose?

**Solution:** Update `_extract_action()` to be more aggressive:
```python
def _extract_action(self, description: str) -> str:
    # Just use verb + object (first 50 chars)
    return description[:47] + '...'
```

### Anchors missing?

**Run validator:**
```bash
python -m src.utils.validate_anchors docs/
```

---

## Conclusion

These optimizations will:

✅ **Reduce token costs by 90%+**
✅ **Keep handoff small forever**
✅ **Make phase docs scannable**
✅ **Speed up circular development**
✅ **Improve agent comprehension**

The key insight: **Agents should be navigators, not archaeologists.** They need maps (handoffs), checklists (phase docs), and compasses (anchors) — not history books.

**Next Steps:**
1. Update templates with new structure
2. Add anchor utility functions
3. Modify generators to validate anchors
4. Test with real agents
5. Monitor token savings

Good luck optimizing devussy! 🚀
