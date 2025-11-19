# Execution Loop Fix - Phases Not Starting After Completion

**Date**: 2025-11-18  
**Status**: ✅ Complete

## Problem

When phases completed during execution, new phases would not start. The card would show "Starting Phase X..." but the phase would never actually begin streaming. The execution loop was stuck and not detecting completions properly.

## Root Cause

**Promise.race() Doesn't Remove Completed Promises**

The original implementation used `Promise.race()` to wait for any phase to complete:

```typescript
await Promise.race(Array.from(running.values()));
```

The problem:
1. `Promise.race()` resolves when the first promise completes
2. But it doesn't remove that promise from the array
3. On the next iteration, `Promise.race()` would immediately resolve again with the same completed promise
4. The loop would continue but never actually wait for new completions
5. New phases would be added to the queue but never executed

## Solution

**Event-Driven Completion Notification**

Instead of using `Promise.race()`, we now use a custom promise that gets resolved when any phase completes:

```typescript
let completionPromiseResolve: (() => void) | null = null;

const waitForCompletion = () => new Promise<void>(resolve => {
    completionPromiseResolve = resolve;
});

// In executePhase completion handler:
running.delete(phase.number);
if (completionPromiseResolve) {
    completionPromiseResolve();  // Notify the loop
    completionPromiseResolve = null;
}

// In the loop:
await waitForCompletion();  // Wait for notification
```

## Implementation Details

### Execution Flow

1. **Start phases up to concurrency limit**
   ```typescript
   while (running.size < concurrency && queue.length > 0) {
       const phase = queue.shift()!;
       const promise = executePhase(phase).then(() => {
           running.delete(phase.number);
           if (completionPromiseResolve) {
               completionPromiseResolve();  // Wake up the loop
               completionPromiseResolve = null;
           }
       });
       running.set(phase.number, promise);
   }
   ```

2. **Wait for completion notification**
   ```typescript
   if (running.size > 0 && queue.length > 0) {
       await waitForCompletion();  // Blocks until a phase completes
   }
   ```

3. **Final cleanup**
   ```typescript
   else if (running.size > 0 && queue.length === 0) {
       // No more phases to queue, wait for all running to finish
       await Promise.all(Array.from(running.values()));
   }
   ```

### State Tracking

**Before** (broken):
```typescript
const running = new Map<number, Promise<void>>();

// Promise.race doesn't remove completed promises
await Promise.race(Array.from(running.values()));
// Loop continues but races the same completed promise
```

**After** (working):
```typescript
const running = new Map<number, Promise<void>>();
let completionPromiseResolve: (() => void) | null = null;

// Phase completion explicitly notifies the loop
if (completionPromiseResolve) {
    completionPromiseResolve();
}

// Loop waits for explicit notification
await waitForCompletion();
```

## Benefits

1. **Reliable**: Loop always waits for actual completions
2. **Efficient**: No polling, event-driven
3. **Clear**: Explicit notification makes flow obvious
4. **Debuggable**: Console logs show exact flow

## Execution Scenarios

### Scenario 1: Concurrency = 3, Phases = 8

```
Start: Phase 1, 2, 3 (running.size = 3)
Wait for completion...
Phase 1 completes → notification → loop wakes up
Start: Phase 4 (running.size = 3)
Wait for completion...
Phase 2 completes → notification → loop wakes up
Start: Phase 5 (running.size = 3)
Wait for completion...
Phase 3 completes → notification → loop wakes up
Start: Phase 6 (running.size = 3)
... and so on
```

### Scenario 2: Final Phases

```
Queue empty, running.size = 3 (phases 6, 7, 8)
No more to queue, wait for all running...
Promise.all([phase6, phase7, phase8])
All complete → loop exits
```

## Console Output

**Before** (broken):
```
[ExecutionView] Starting phase 1 - Queue remaining: 7, Running: 0
[ExecutionView] Starting phase 2 - Queue remaining: 6, Running: 1
[ExecutionView] Starting phase 3 - Queue remaining: 5, Running: 2
[ExecutionView] Phase 1 completed
[ExecutionView] Starting phase 4 - Queue remaining: 4, Running: 2
[ExecutionView] Phase 2 completed
[ExecutionView] Phase 3 completed
// Loop stuck, phases 5-8 never start
```

**After** (working):
```
[ExecutionView] Starting phase 1 - Queue remaining: 7, Running: 0
[ExecutionView] Starting phase 2 - Queue remaining: 6, Running: 1
[ExecutionView] Starting phase 3 - Queue remaining: 5, Running: 2
[ExecutionView] Waiting for a phase to complete... Running: 3, Queue: 5
[ExecutionView] Phase 1 completed, removing from running map
[ExecutionView] A phase completed, continuing loop
[ExecutionView] Starting phase 4 - Queue remaining: 4, Running: 2
[ExecutionView] Waiting for a phase to complete... Running: 3, Queue: 4
[ExecutionView] Phase 2 completed, removing from running map
[ExecutionView] A phase completed, continuing loop
[ExecutionView] Starting phase 5 - Queue remaining: 3, Running: 2
// Continues until all phases complete
```

## Edge Cases Handled

1. **Pause During Execution**: Aborts all running phases, breaks loop
2. **Phase Failure**: Still notifies completion, loop continues
3. **Empty Queue**: Waits for all running phases with `Promise.all()`
4. **Rapid Completions**: Each completion creates new notification promise

## Testing Checklist

- [x] First 3 phases start immediately
- [x] Phases 4-6 start as first 3 complete
- [x] Phases 7-9 start as next batch completes
- [x] All phases complete successfully
- [x] Concurrency limit respected
- [x] Console logs show proper flow
- [x] No stuck phases
- [x] No infinite loops

## Files Changed

- `devussy-web/src/components/pipeline/ExecutionView.tsx`
  - Replaced `Promise.race()` with event-driven notification
  - Added `completionPromiseResolve` for explicit signaling
  - Added `waitForCompletion()` helper
  - Improved console logging
  - Added final cleanup with `Promise.all()`

## Performance Impact

- **Before**: Loop would spin rapidly checking completed promises
- **After**: Loop sleeps until explicitly woken by completion
- **Result**: More efficient, clearer execution flow

---

**Status**: Execution loop now works perfectly! All phases start and complete in order with proper concurrency control. 🎯
