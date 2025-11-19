# Phase Card Content Fix

**Date**: 2025-11-18  
**Issue**: Phase cards only show titles, not the full content from the devplan

---

## Problem

When viewing the Development Plan in "Cards" mode, the phase cards only display:
- Phase number and title
- "No description" text

But the "Raw Text" view shows the full devplan with:
- Summary for each phase
- Major components list
- Detailed bullet points

The cards need to show all this content for editing.

---

## Root Cause

The `parsePhasesFromPlan` function only extracted basic fields from the plan data object:
```typescript
{
  number: phase.number,
  title: phase.title,
  description: phase.description  // This was empty!
}
```

The actual content was in the `planContent` string (raw text), not in the structured plan object.

---

## Solution

Created a new `parsePhasesFromText` function that:
1. Parses the raw text content line by line
2. Identifies phase headers: `1. **Phase 1: Title**`
3. Collects all content between phase headers
4. Extracts:
   - Summary text (after `- Summary:`)
   - Component lists (after `- Major components:`)
   - All bullet points and indented content
5. Combines everything into the `description` field

---

## Changes Made

### devussy-web/src/components/pipeline/PlanView.tsx

1. **Added `parsePhasesFromText` function**:
   - Parses raw markdown text
   - Collects all content for each phase
   - Preserves formatting and structure

2. **Updated plan completion handler**:
   - Calls `parsePhasesFromText(planContent)` instead of `parsePhasesFromPlan`
   - Falls back to plan data if text parsing fails
   - Logs parsing results for debugging

3. **Added console logging**:
   - Logs number of phases parsed
   - Logs each phase with content length
   - Helps debug parsing issues

---

## How It Works

### Input (Raw Text):
```
1. **Phase 1: Project Initialization & Foundations**
   - Summary: Establish the repositories, developer workflows...
   - Major components:
     - Create repository, branching strategy
     - Decide & document stack choice
     - Add required development-artifact templates
```

### Output (PhaseData):
```typescript
{
  number: 1,
  title: "Project Initialization & Foundations",
  description: "Establish the repositories, developer workflows...\n\nComponents:\n- Create repository, branching strategy\n- Decide & document stack choice\n- Add required development-artifact templates"
}
```

---

## Testing

1. **Generate a new plan** or regenerate existing one
2. **Check browser console** for parsing logs:
   ```
   [PlanView] Plan received, parsing phases from text...
   [PlanView] Plan content length: 12345
   [PlanView] Parsed 10 phases from text
     Phase 1: Project Initialization & Foundations (450 chars)
     Phase 2: Local & CI Infrastructure (380 chars)
     ...
   ```
3. **Switch to Cards view** - should now show full content
4. **Expand/collapse phases** - content should be visible
5. **Edit phases** - should be able to modify full content

---

## Expected Result

Phase cards now display:
- ✅ Phase title
- ✅ Summary text
- ✅ Component lists
- ✅ All bullet points
- ✅ Proper formatting with line breaks

Users can:
- ✅ View full phase content in cards
- ✅ Edit all content in textarea
- ✅ Add/remove/reorder phases
- ✅ Toggle between Cards and Raw Text views

---

## Files Modified

- `devussy-web/src/components/pipeline/PlanView.tsx` - Added text parser and logging

---

## Next Steps

If content still doesn't appear:
1. Check browser console for parsing logs
2. Verify `planContent` has the full text
3. Check if phase headers match the regex pattern
4. Adjust parser logic if LLM format changes
