# SSE Newline Fix - Critical Bug

**Date**: 2025-11-18  
**Issue**: Backend generating content but frontend not receiving it  
**Status**: ✅ FIXED

---

## The Bug

The backend was using `\\n\\n` (escaped backslashes) instead of `\n\n` (actual newlines) in SSE messages.

### What Was Happening

**Backend code**:
```python
self.wfile.write(f"data: {data}\\n\\n".encode('utf-8'))
```

This created:
```
data: {"content": "..."}\\n\\n
```

Instead of proper SSE format:
```
data: {"content": "..."}

```

### Why It Broke

SSE (Server-Sent Events) requires messages to be separated by **two actual newline characters** (`\n\n`).

When using `\\n\\n`, Python creates a literal backslash followed by 'n', not a newline character.

The frontend was waiting for `\n\n` to split messages, but never found it, so it buffered everything without processing.

---

## The Fix

Changed all SSE writes from `\\n\\n` to `\n\n`:

### Before (BROKEN):
```python
self.writer.write(f"data: {data}\\n\\n".encode('utf-8'))
```

### After (FIXED):
```python
self.writer.write(f"data: {data}\n\n".encode('utf-8'))
```

### Files Changed

**devussy-web/api/plan/detail.py** - 4 locations:
1. Line ~85: `on_token_async` - streaming handler
2. Line ~128: Start message
3. Line ~147: Steps count message  
4. Line ~152: Completion message
5. Line ~161: Error message

---

## How SSE Works

### Proper Format:
```
data: {"content": "Hello"}

data: {"content": " World"}

data: {"done": true}

```

Each message:
1. Starts with `data: `
2. Contains JSON payload
3. Ends with **two newlines** (`\n\n`)

### Frontend Parsing:
```typescript
buffer.split('\n\n')  // Splits on double newline
```

If backend sends `\\n\\n`, the split never happens and messages accumulate in the buffer without being processed.

---

## Testing

After restarting the backend:

1. **Frontend should receive messages**:
   ```
   [executePhase] Phase 1: Content #1: Starting phase 1 generation...
   [executePhase] Phase 1: Content #2: ## Step 1: Create Repository
   [executePhase] Phase 1: Content #3: Initialize a new Git...
   ```

2. **Terminal output should stream in real-time** in the execution phase cards

3. **Phases should complete** and show "✓ Complete" status

---

## Additional Debugging Added

### Frontend (ExecutionView.tsx):
- Logs chunk count every 10 chunks
- Logs first 5 content messages and every 50th after
- Logs when stream starts/ends
- Logs when done signal received

### Backend (detail.py):
- Already had token count logging
- Logs phase details before generation
- Logs completion with step count

---

## Success Criteria

✅ Frontend console shows: `[executePhase] Phase X: Content #1: ...`  
✅ Terminal output appears in execution phase cards  
✅ Phases complete and show green checkmark  
✅ Multiple phases execute concurrently  
✅ All phases finish successfully  

---

## Root Cause Analysis

This bug was introduced because:
1. Python f-strings require careful attention to escaping
2. `\n` in an f-string is a newline
3. `\\n` in an f-string is a literal backslash + n
4. The code was likely copied from somewhere that needed escaping
5. No immediate error because the HTTP response was valid, just not proper SSE format

---

## Prevention

To avoid this in the future:
1. Test SSE endpoints with curl: `curl -N http://localhost:8000/api/plan/detail`
2. Check browser Network tab for proper SSE format
3. Use raw strings or explicit `\n` characters
4. Add SSE format validation in tests

---

## Files Modified

- `devussy-web/api/plan/detail.py` - Fixed all SSE writes (5 locations)
- `devussy-web/src/components/pipeline/ExecutionView.tsx` - Added debugging
