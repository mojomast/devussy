# Devussy Frontend Handoff Document

**Date**: 2025-11-18  
**Status**: In Progress  
**Current Agent**: Completed streaming fixes and pipeline integration

---

## Recent Accomplishments (2025-11-18)

### 1. Fixed "Approve & Plan" Button Enablement
**Problem**: After the System Design generation completed, the "Approve & Plan" button remained disabled indefinitely.

**Root Cause**: The frontend was waiting for the HTTP stream to close before setting `isGenerating` to false. The backend was sending a `done` message but keeping the connection open with `Connection: keep-alive`.

**Solution**: 
- Modified `DesignView.tsx` to explicitly `return` from the stream reading loop when the `done` message is received.
- This triggers the `finally` block immediately, setting `isGenerating = false` and enabling the button.

**Files Changed**:
- `devussy-web/src/components/pipeline/DesignView.tsx` (line 90-94)

---

### 2. Fixed Plan Generation Connection Timeout
**Problem**: When clicking "Approve & Plan", the Development Plan window appeared but showed "Error: Failed to generate plan" after a few seconds. The backend logged `WinError 10053` (connection aborted by software).

**Root Cause**: Plan generation takes a long time. The original implementation used a blocking request that waited for the entire plan to generate before sending any response. This caused the client (or Next.js proxy) to timeout and abort the connection.

**Solution**:
- Switched `api/plan/basic.py` to use **Server-Sent Events (SSE)** streaming, similar to the Design phase.
- Backend now sends keep-alive chunks during generation and a final `done` message with the plan data.
- Updated `PlanView.tsx` to consume the SSE stream using a `ReadableStream` reader.
- Bypasses Next.js proxy by hitting backend directly (`http://${window.location.hostname}:8000/api/plan/basic`).

**Files Changed**:
- `devussy-web/api/plan/basic.py` (complete rewrite to support SSE)
- `devussy-web/src/components/pipeline/PlanView.tsx` (lines 25-88)

---

## Current Architecture

### Pipeline Phases
1. **Interview** → `InterviewView.tsx` (SSE streaming)
2. **Design** → `DesignView.tsx` (SSE streaming) ✅ Fixed button enablement
3. **Plan** → `PlanView.tsx` (SSE streaming) ✅ Fixed timeout
4. **Execute** → `PhaseDetailView.tsx` (not yet tested)
5. **Handoff** → `HandoffView.tsx` (not yet tested)

### Multi-Window System
- `page.tsx` manages window state array
- Each phase spawns a new window while keeping previous windows accessible
- `WindowFrame.tsx` provides draggable, minimizable, focusable windows
- `Taskbar.tsx` shows all open windows

### Streaming Pattern
All generation endpoints use SSE:
- Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`
- Format: `data: {"content": "..."}\n\n` for chunks, `data: {"done": true, "result": {...}}\n\n` for completion
- Frontend bypasses Next.js proxy by connecting directly to port 8000

---

## Known Issues / Next Steps

### Outstanding Tasks
1. **Auto-scroll during streaming**: User requested that streaming windows auto-scroll to follow new content so they don't have to manually scroll.
   - **Affected Components**: `DesignView.tsx`, `InterviewView.tsx`, potentially `PlanView.tsx`
   - **Implementation**: Add a `useRef` to the scroll container and call `scrollIntoView()` or `scrollTop = scrollHeight` when content updates.

2. **Change default model**: User wants default model to be `gpt-5-mini` instead of `gpt-4o`.
   - **Location**: `page.tsx` line 51 (currently `model: 'gpt-4o'`)
   - **Change to**: `model: 'gpt-5-mini'`

3. **Test Execute and Handoff phases**: These haven't been tested yet in the new multi-window streaming architecture.

4. **Error handling**: Add better error UI for stream failures, timeout retries, etc.

### API Backend Status
- **Design API** (`/api/design`): ✅ Working with SSE
- **Plan API** (`/api/plan/basic`): ✅ Working with SSE
- **Execute API** (`/api/execute/*`): ⚠️ Not tested
- **Handoff API** (`/api/handoff`): ⚠️ Not tested

### Dependencies
- Backend runs on port 8000 (Python dev server)
- Frontend runs on port 3000 (Next.js)
- All API calls bypass Next.js proxy to avoid buffering issues

---

## Technical Notes for Next Agent

### Debugging Streaming Issues
If you encounter timeout or buffering issues:
1. Check that the backend endpoint sends `Content-Type: text/event-stream` header
2. Verify frontend uses `response.body.getReader()` not `response.json()`
3. Ensure direct backend connection (`http://${window.location.hostname}:8000/...`)
4. Look for the `done` message in server logs and frontend console

### Auto-Scroll Implementation
For auto-scroll, use this pattern:
```typescript
const scrollRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (scrollRef.current) {
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }
}, [content]); // or designContent, interviewMessages, etc.
```

### Model Configuration
Model config is managed in `page.tsx` state:
- Global defaults at line 49-60
- Can be overridden per-stage (interview, design, plan, execute, handoff)
- Passed to each component via `modelConfig` prop

---

## Files Reference

### Frontend Components
- `devussy-web/src/app/page.tsx` - Main app, window management
- `devussy-web/src/components/pipeline/DesignView.tsx` - Design phase
- `devussy-web/src/components/pipeline/PlanView.tsx` - Plan phase
- `devussy-web/src/components/pipeline/InterviewView.tsx` - Interview phase
- `devussy-web/src/components/window/WindowFrame.tsx` - Window wrapper
- `devussy-web/src/components/window/Taskbar.tsx` - Window taskbar

### Backend API
- `devussy-web/api/design.py` - Design generation SSE endpoint
- `devussy-web/api/plan/basic.py` - Plan generation SSE endpoint
- `devussy-web/api/interview.py` - Interview SSE endpoint

### Documentation
- `frontend_implementation_plan.md` - Overall frontend roadmap
- This file (`handoff.md`) - Current status and context
