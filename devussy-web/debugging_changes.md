# Debugging Changes - Phase Parsing & Execution

**Date**: 2025-11-18  
**Status**: Debugging in progress

---

## Issues Identified

1. **Phase titles contain `**`** - Parser not cleaning markdown properly
2. **"No description" on all phases** - Description extraction not working
3. **Execution phases stuck on "Waiting to start..."** - Phases not executing

---

## Root Causes Found

### 1. Phase Parsing Issue
The LLM response uses this format:
```
1. **Phase 1: Project Initialization & Development Workflow**
   - Summary: Create the repo...
   - Major components:
     - Item 1
     - Item 2
```

The regex patterns weren't matching `1. **Phase 1: Title**` format.

### 2. Description Extraction Issue
Descriptions are in `- Summary: ...` format, not plain text after the header.

### 3. Execution Loop Bug
The `startExecution` function had a bug in Promise.race logic - it wasn't properly removing completed promises from the running array.

---

## Changes Made

### src/pipeline/basic_devplan.py

1. **Updated regex patterns** to match `1. **Phase 1: Title**` format:
   ```python
   # Added pattern for numbered with bold phase
   re.compile(
       r"^\d+\.\s*\*\*\s*Phase\s+0*(\d+)\s*[:\-–—]\s*(.+?)\s*\*\*\s*$",
       re.IGNORECASE,
   )
   ```

2. **Fixed description extraction** to look for `- Summary:` lines:
   ```python
   if stripped.startswith("- Summary:") or stripped.startswith("- summary:"):
       summary_text = stripped.split(":", 1)[1].strip()
       if summary_text:
           current_description = summary_text
   ```

3. **Added comprehensive debugging**:
   - Saves full LLM response to `.devussy_state/last_devplan_response.txt`
   - Logs first 15 non-empty lines
   - Prints detailed warning if no phases parsed

### devussy-web/src/components/pipeline/ExecutionView.tsx

1. **Fixed Promise.race loop**:
   - Changed from array to Map to track running promises
   - Properly removes completed promises
   - Added proper error handling

2. **Added console logging**:
   - Logs when execution starts
   - Logs each phase start/complete
   - Logs queue and running counts
   - Logs errors

### devussy-web/api/plan/detail.py

1. **Added debugging output**:
   - Logs received phase number and project name
   - Logs number of phases in plan
   - Logs errors clearly

2. **Fixed PhaseDetailResult access** (from previous session):
   - Changed `detailed_phase.steps` to `detailed_phase.phase.steps`

---

## Testing Instructions

1. **Restart backend server**:
   ```bash
   python -m devussy-web.api_server
   ```

2. **Restart frontend** (if needed):
   ```bash
   cd devussy-web
   npm run dev
   ```

3. **Generate a new plan**:
   - Go through Interview → Design → Plan
   - Watch the backend console for debug output

4. **Check phase parsing**:
   - Look for: `[detail.py] Plan has X phases`
   - Check if phases show proper titles (without `**`)
   - Check if descriptions are populated

5. **Check execution**:
   - Click "Approve & Start Execution"
   - Watch browser console for `[ExecutionView]` logs
   - Watch backend console for `[detail.py]` logs
   - Verify phases start executing

---

## Expected Debug Output

### Backend Console
```
[detail.py] Received request for phase 1, project: gnarley fartley
[detail.py] Plan has 10 phases
Parsing response with 150 lines
First 15 non-empty lines: ['1. **Phase 1: ...', ...]
Matched phase header: '1. **Phase 1: ...' -> Phase 1: Project Initialization
DEBUG: Parsed 10 phases
  Phase 1: Project Initialization & Development Workflow
    Description: Create the repo, choose the primary stack...
  Phase 2: Local & CI Infrastructure
    Description: Provide reproducible local and CI environments...
```

### Browser Console
```
[ExecutionView] Starting execution with 10 phases, concurrency: 3
[ExecutionView] Starting phase 1 - Queue remaining: 9 Running: 0
[executePhase] Starting phase 1 Project Initialization & Development Workflow
[executePhase] Fetching from http://localhost:8000/api/plan/detail for phase 1
[ExecutionView] Starting phase 2 - Queue remaining: 8 Running: 1
[ExecutionView] Starting phase 3 - Queue remaining: 7 Running: 2
[ExecutionView] Phase 1 completed
[ExecutionView] Starting phase 4 - Queue remaining: 6 Running: 2
```

---

## Files Modified

1. `src/pipeline/basic_devplan.py` - Phase parsing and description extraction
2. `devussy-web/src/components/pipeline/ExecutionView.tsx` - Execution loop and debugging
3. `devussy-web/api/plan/detail.py` - Backend debugging

---

## Next Steps

After testing:
1. If phases parse correctly, remove debug logging
2. If execution works, clean up console.log statements
3. If issues persist, check the saved response file and adjust regex patterns
