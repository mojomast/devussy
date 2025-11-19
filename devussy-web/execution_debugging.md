# Execution Phase Debugging

**Date**: 2025-11-18  
**Issue**: Execution starts 3 phases then hangs, backend shows 17 phases with weird descriptions

---

## Symptoms

1. **Backend logs show 17 phases** instead of expected 10
2. **Phase descriptions contain HTML comments** like `<!-- HANDOFF_NOTES_END -->`
3. **Only 3 phases start executing**, then no more requests
4. **Frontend shows correct number of phases** in cards

---

## Debugging Added

### Frontend Logging

1. **PlanView.tsx - handleApprove**:
   ```typescript
   console.log('[PlanView] Approving plan with X phases');
   // Logs each phase number and title
   ```

2. **page.tsx - handlePlanApproved**:
   ```typescript
   console.log('[page.tsx] Plan approved with X phases');
   // Logs first 5 phases
   ```

3. **ExecutionView.tsx - executePhase**:
   ```typescript
   console.log('[executePhase] Request body:', {
     phaseNumber, projectName, planPhasesCount, firstPhase
   });
   ```

### Backend Logging

1. **detail.py - Plan parsing**:
   ```python
   print(f"[detail.py] Parsing plan_data with X phases")
   print(f"[detail.py] DevPlan created with X phases")
   # Prints all phases with descriptions
   ```

---

## Expected Debug Flow

### When "Approve & Start Execution" is clicked:

1. **PlanView logs**:
   ```
   [PlanView] Approving plan with 10 phases
     Phase 1: Project Initialization & Foundations (desc: Establish the repositories...)
     Phase 2: Local & CI Infrastructure (desc: Provide reproducible...)
     ...
   ```

2. **page.tsx logs**:
   ```
   [page.tsx] Plan approved with 10 phases
     Phase 1: Project Initialization & Foundations
     Phase 2: Local & CI Infrastructure
     ...
   ```

3. **ExecutionView logs** (for each phase):
   ```
   [ExecutionView] Starting execution with 10 phases, concurrency: 3
   [ExecutionView] Starting phase 1 - Queue remaining: 9 Running: 0
   [executePhase] Starting phase 1 Project Initialization & Foundations
   [executePhase] Request body: {
     phaseNumber: 1,
     projectName: "bees",
     planPhasesCount: 10,
     firstPhase: { number: 1, title: "...", description: "..." }
   }
   ```

4. **Backend logs** (for each request):
   ```
   [detail.py] Received request for phase 1, project: bees
   [detail.py] Plan has 10 phases
   [detail.py] Parsing plan_data with 10 phases
   [detail.py] DevPlan created with 10 phases
     Phase 1: Project Initialization & Foundations
       Description: Establish the repositories...
     Phase 2: Local & CI Infrastructure
       Description: Provide reproducible...
   ```

---

## Possible Issues

### Issue 1: Plan Data Corruption
The plan object might be getting corrupted between PlanView and ExecutionView.

**Check**:
- Compare phase count in PlanView vs page.tsx vs ExecutionView logs
- Check if phase descriptions are intact

### Issue 2: Backend Parsing Error
The backend might be re-parsing the raw text instead of using structured data.

**Check**:
- Look for "raw_basic_response" in plan_data
- Check if DevPlan(**plan_data) is parsing correctly

### Issue 3: Execution Loop Bug
The Promise.race loop might not be handling completions correctly.

**Check**:
- Look for "[ExecutionView] Phase X completed" logs
- Check if phases are being removed from running Map

### Issue 4: Backend Hanging
The DetailedDevPlanGenerator might be hanging or timing out.

**Check**:
- Look for errors after "Starting phase X generation..."
- Check if streaming is working

---

## Testing Steps

1. **Clear browser console** and restart backend
2. **Generate a new plan** or regenerate existing
3. **Click "Approve & Start Execution"**
4. **Watch both consoles**:
   - Browser console for frontend logs
   - Terminal for backend logs
5. **Compare phase counts** at each step
6. **Check if phases complete** or hang

---

## Next Steps Based on Findings

### If phase count is wrong in PlanView:
- Fix the `parsePhasesFromText` function
- Check regex patterns

### If phase count is wrong in page.tsx:
- Check how plan is passed from PlanView
- Check if plan state is being modified

### If phase count is wrong in backend:
- Check DevPlan parsing
- Check if raw_basic_response is interfering

### If phases hang after 3:
- Check Promise.race loop
- Check if backend is responding
- Check for errors in streaming

---

## Files Modified

- `devussy-web/src/components/pipeline/PlanView.tsx` - Added approval logging
- `devussy-web/src/app/page.tsx` - Added plan received logging
- `devussy-web/src/components/pipeline/ExecutionView.tsx` - Added request logging
- `devussy-web/api/plan/detail.py` - Added parsing logging
