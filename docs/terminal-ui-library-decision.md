# Terminal UI Library Decision for Devussy Phase 4

## Requirements

Based on DEVUSSYPLAN.md, the terminal UI needs to:

1. **5-phase grid layout** - Display plan, design, implement, test, review phases simultaneously
2. **Real-time streaming** - Show LLM tokens as they arrive
3. **Responsive layout** - Adapt to terminal width (5 cols / 2x3 grid / vertical stack)
4. **Interactive controls** - Mouse + keyboard navigation, focus management
5. **Fullscreen viewer** - Click/focus a phase to see full content with scrolling
6. **Steering workflow** - Cancel mid-generation, collect feedback, regenerate
7. **Status indicators** - Color-coded borders, status badges, progress tracking

## Python Terminal UI Library Options

### 1. Rich (Current Choice)
**Status**: Already in use for console output

**Pros**:
- Already integrated (used for panels, progress, console)
- Excellent text formatting and styling
- Live display and progress bars
- Good documentation and active development
- No additional dependencies

**Cons**:
- Not designed for complex interactive TUIs
- Limited layout management for grids
- No built-in mouse support for complex interactions
- Would need significant custom code for grid layout

**Verdict**: Good for current CLI output, insufficient for Phase 4 requirements

### 2. Textual (Recommended)
**GitHub**: https://github.com/Textualize/textual  
**Built by**: Same team as Rich (Textualize)

**Pros**:
- Modern, async-first TUI framework
- Built-in grid/layout system perfect for 5-phase display
- Mouse and keyboard support out of the box
- Reactive widgets and data binding
- CSS-like styling system
- Excellent documentation and examples
- Active development and community
- Works seamlessly with Rich (same ecosystem)
- Built-in scrolling, focus management, modals

**Cons**:
- Additional dependency (~2MB)
- Learning curve for widget system
- Requires async event loop (already using asyncio)

**Example Use Cases**:
- Grid layout: `Grid` widget with 5 containers
- Streaming: Custom `RichLog` widget with live updates
- Fullscreen: Modal overlay with scrollable content
- Steering: Modal dialog with form inputs

**Verdict**: ✅ **RECOMMENDED** - Purpose-built for our exact use case

### 3. urwid
**GitHub**: https://github.com/urwid/urwid

**Pros**:
- Mature, stable library (15+ years)
- Good widget system
- Mouse support

**Cons**:
- Older API design (not async-friendly)
- Less intuitive than Textual
- Smaller community
- More verbose code

**Verdict**: ❌ Superseded by Textual

### 4. blessed / blessed-python
**GitHub**: https://github.com/jquast/blessed

**Pros**:
- Simple, low-level terminal control
- Good for basic positioning and colors

**Cons**:
- No high-level widget system
- Would need to build everything from scratch
- No built-in layout management
- Not designed for complex TUIs

**Verdict**: ❌ Too low-level for our needs

### 5. py-cui
**GitHub**: https://github.com/jwlodek/py_cui

**Pros**:
- Simple grid-based layout
- Widgets for common UI elements

**Cons**:
- Less mature than alternatives
- Smaller community
- Limited documentation
- Not as feature-rich as Textual

**Verdict**: ❌ Textual is superior

## Decision: Textual

**Chosen Library**: Textual  
**Rationale**:
1. Purpose-built for complex TUI applications
2. Grid layout system matches our 5-phase requirement perfectly
3. Async-first design aligns with our existing architecture
4. Rich integration means we keep our existing console output
5. Active development and excellent documentation
6. Built-in support for all our requirements (mouse, keyboard, modals, scrolling)

## Implementation Plan

### Phase 4.1: Setup and Basic Grid (Day 1)
- Add textual to requirements.txt
- Create `src/terminal/terminal_ui.py` with basic Textual app
- Implement 5-phase grid layout with responsive sizing
- Test layout adaptation (5 cols / 2x3 / vertical)

### Phase 4.2: Phase State Display (Day 1-2)
- Create `PhaseBox` widget for individual phase display
- Implement status badges and border colors
- Add scrollable content area
- Wire to `PhaseStateManager` from existing code

### Phase 4.3: Streaming Integration (Day 2)
- Connect `TerminalPhaseGenerator` to phase boxes
- Implement real-time token streaming display
- Add status updates (idle/streaming/complete/error)

### Phase 4.4: Fullscreen Viewer (Day 2-3)
- Create modal overlay for fullscreen phase view
- Implement scrolling with vim/arrow keys
- Add character count footer
- ESC to return to grid

### Phase 4.5: Steering Workflow (Day 3-4)
- Implement cancel handler (C key)
- Create steering interview modal
- Wire feedback collection
- Integrate regeneration with context

### Phase 4.6: Polish and Testing (Day 4-5)
- Add keyboard shortcuts help (? key)
- Implement focus management
- Add error handling and edge cases
- Write tests for UI components

## Code Structure

```
src/terminal/
├── __init__.py
├── terminal_ui.py          # Main Textual app
├── widgets/
│   ├── __init__.py
│   ├── phase_box.py        # Individual phase display widget
│   ├── fullscreen_viewer.py  # Modal for fullscreen view
│   └── steering_modal.py   # Steering interview overlay
├── phase_state.py          # Phase state management (existing)
└── generation_orchestrator.py  # Coordinates generation + UI
```

## Migration Path

1. **Keep existing CLI** - All current commands continue to work
2. **Add new command** - `devussy generate-terminal <devplan>` for TUI mode
3. **Gradual rollout** - TUI is opt-in, not replacing existing flow
4. **Fallback** - If Textual unavailable, gracefully degrade to current output

## Next Steps

1. Add textual to requirements.txt
2. Create basic proof-of-concept with 5-box grid
3. Test on different terminal sizes
4. Get user feedback on layout and interactions
5. Iterate on design before full implementation

## References

- Textual docs: https://textual.textualize.io/
- Textual examples: https://github.com/Textualize/textual/tree/main/examples
- Rich docs: https://rich.readthedocs.io/
