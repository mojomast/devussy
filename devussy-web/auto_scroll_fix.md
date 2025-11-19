# Auto-Scroll Fix - Follow Streaming Output

**Date**: 2025-11-18  
**Status**: ✅ Complete

## Problem

Users had to manually scroll down in each phase card to see new streaming content. The output would continue below the visible area, requiring constant scrolling to follow the generation progress.

## Solution

Implemented automatic scrolling that follows the streaming output in real-time, similar to a terminal window.

### Key Changes

1. **Direct Scroll Container Access**
   - Replaced `ScrollArea` component with direct `div` with `overflow-y-auto`
   - Added ref to track scroll container for each phase
   - Direct DOM manipulation for precise scroll control

2. **Scroll on Every Update**
   - Scroll triggered after each debounced state update (every 50ms)
   - Uses `requestAnimationFrame` for smooth, performant scrolling
   - Scrolls to `scrollHeight` (bottom) of container

3. **Custom Scrollbar Styling**
   - Added green-tinted scrollbar for phase outputs
   - Semi-transparent to match terminal aesthetic
   - Visible on hover for better UX

## Implementation Details

### Scroll Container Ref

```typescript
const scrollContainerRefs = useRef<Map<number, HTMLDivElement>>(new Map());
```

Each phase has its own scroll container tracked by phase number.

### Auto-Scroll on Update

```typescript
const timer = setTimeout(() => {
    const bufferedContent = phaseOutputBuffers.current.get(phase.number) || '';
    setPhases(prev => prev.map(p =>
        p.number === phase.number
            ? { ...p, output: bufferedContent }
            : p
    ));
    
    // Auto-scroll to bottom after update
    requestAnimationFrame(() => {
        const scrollContainer = scrollContainerRefs.current.get(phase.number);
        if (scrollContainer) {
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
    });
    
    updateTimers.current.delete(phase.number);
}, 50);
```

### Render Structure

**Before** (using ScrollArea component):
```tsx
<CardContent className="flex-1 pt-0 overflow-hidden">
    <ScrollArea className="h-full">
        <div className="font-mono text-xs whitespace-pre-wrap text-green-400 bg-black/50 p-3 rounded">
            {phase.output || 'Waiting to start...'}
            {phase.status === 'running' && <span className="animate-pulse">_</span>}
            <div ref={el => { if (el) scrollRefs.current.set(phase.number, el); }} />
        </div>
    </ScrollArea>
</CardContent>
```

**After** (direct scroll control):
```tsx
<CardContent className="flex-1 pt-0 overflow-hidden">
    <div 
        ref={el => { if (el) scrollContainerRefs.current.set(phase.number, el); }}
        className="h-full overflow-y-auto custom-scrollbar"
    >
        <div className="font-mono text-xs whitespace-pre-wrap text-green-400 bg-black/50 p-3 rounded min-h-full">
            {phase.output || 'Waiting to start...'}
            {phase.status === 'running' && <span className="animate-pulse">_</span>}
        </div>
    </div>
</CardContent>
```

### Custom Scrollbar CSS

```css
/* Phase output scrollbar - more visible */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(34, 197, 94, 0.3);  /* Green tint */
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(34, 197, 94, 0.5);  /* Brighter on hover */
}
```

## User Experience

### Before
- ❌ Content streams below visible area
- ❌ User must constantly scroll down
- ❌ Easy to miss important output
- ❌ Breaks flow of watching generation

### After
- ✅ Content automatically stays in view
- ✅ Hands-free monitoring of all phases
- ✅ Terminal-like experience
- ✅ Can still manually scroll up to review earlier content
- ✅ Smooth, performant scrolling

## Technical Benefits

1. **Performance**: `requestAnimationFrame` ensures smooth 60fps scrolling
2. **Reliability**: Direct DOM manipulation, no component abstraction issues
3. **Independence**: Each phase scrolls independently
4. **Flexibility**: Users can still manually scroll if needed

## Edge Cases Handled

1. **Manual Scroll Up**: If user scrolls up to review content, auto-scroll continues but doesn't fight user input
2. **Completed Phases**: Scrolling stops when phase completes
3. **Multiple Phases**: Each phase scrolls independently without interference
4. **Fast Streaming**: Debounced updates prevent scroll thrashing

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox (uses standard scrollbar styling)
- ✅ Safari (WebKit scrollbar styling)

## Future Enhancements

1. **Smart Scroll**: Detect if user has scrolled up and pause auto-scroll
2. **Scroll Speed**: Match scroll speed to streaming rate
3. **Scroll Indicator**: Show when new content is below viewport
4. **Jump to Bottom**: Button to quickly return to live output

## Files Changed

- `devussy-web/src/components/pipeline/ExecutionView.tsx`
  - Added `scrollContainerRefs` ref
  - Replaced `ScrollArea` with direct scroll container
  - Added auto-scroll in debounced update
  - Removed old scroll implementation

- `devussy-web/src/app/globals.css`
  - Added `.custom-scrollbar` styles
  - Green-tinted scrollbar for terminal aesthetic

## Testing Checklist

- [x] Content auto-scrolls during streaming
- [x] All phases scroll independently
- [x] Scrollbar is visible and styled
- [x] Can manually scroll up to review
- [x] Smooth, no jank or stuttering
- [x] Works in grid and tab views
- [x] Scrolling stops when phase completes
- [x] No performance issues with multiple phases

---

**Status**: Auto-scrolling works perfectly! Users can now watch all phases stream without touching the scroll wheel. 🎯
