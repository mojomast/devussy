"""Textual-based terminal UI for streaming phase generation.

This module provides a modern TUI for displaying 5 phases (plan, design,
implement, test, review) in a responsive grid layout with real-time streaming.
"""

import asyncio
from typing import Optional

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Center, Vertical, HorizontalScroll
from textual.widgets import Header, Footer, Static, Label, Input, TextArea, Button
from textual.reactive import reactive
from textual.binding import Binding
from textual.dom import NoMatches
from textual.screen import ModalScreen
from rich.text import Text

from .phase_state import PhaseStateManager, PhaseStatus
from .phase_generator import TerminalPhaseGenerator
from ..models import DevPlan


class PhaseBox(Static):
    """Widget displaying a single phase with status, tokens, and content."""
    
    _MAX_VISIBLE_LINES = 40
    can_focus = True
    
    DEFAULT_CSS = """
    PhaseBox {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }
    
    PhaseBox.idle {
        border: solid $secondary;
    }
    
    PhaseBox.streaming {
        border: solid $accent;
    }
    
    PhaseBox.complete {
        border: solid $success;
    }
    
    PhaseBox.interrupted {
        border: solid $warning;
    }
    
    PhaseBox.error {
        border: solid $error;
    }
    
    PhaseBox.regenerating {
        border: solid $accent;
    }

    PhaseBox:focus {
        border: solid $accent;
    }
    
    PhaseBox:focus .phase-title {
        text-style: bold reverse;
    }
    
    PhaseBox .phase-title {
        text-style: bold;
        background: $boost;
        padding: 0 1;
    }
    
    PhaseBox .phase-status {
        color: $text-muted;
        padding: 0 1;
        text-style: bold;
    }
    
    PhaseBox.idle .phase-status {
        color: $secondary;
    }
    
    PhaseBox.streaming .phase-status {
        color: $accent;
        text-style: bold italic;
    }
    
    PhaseBox.complete .phase-status {
        color: $success;
        text-style: bold;
    }
    
    PhaseBox.interrupted .phase-status {
        color: $warning;
        text-style: italic;
    }
    
    PhaseBox.error .phase-status {
        color: $error;
        text-style: bold;
    }
    
    PhaseBox.regenerating .phase-status {
        color: $accent;
        text-style: bold italic;
    }
    
    PhaseBox .phase-tokens {
        color: $text-muted;
        padding: 0 1;
        text-style: italic;
    }
    
    PhaseBox .phase-content {
        padding: 1;
        height: 1fr;
        overflow-y: auto;
    }
    """
    
    phase_name = reactive("")
    status = reactive(PhaseStatus.IDLE)
    content = reactive("")
    token_count = reactive(0)
    
    def __init__(self, phase_name: str, **kwargs):
        """Initialize phase box.
        
        Args:
            phase_name: Name of the phase (e.g., 'plan', 'design')
        """
        super().__init__(**kwargs)
        self.phase_name = phase_name
    
    def compose(self) -> ComposeResult:
        """Compose the phase box layout."""
        yield Label(self.phase_name.upper(), classes="phase-title")
        yield Label(self._get_status_text(), classes="phase-status")
        yield Label(self._get_token_text(), classes="phase-tokens")
        yield Static(self.content, classes="phase-content")
    
    def _get_status_text(self) -> str:
        """Get status badge text."""
        status_map = {
            PhaseStatus.IDLE: "⏸ Idle",
            PhaseStatus.STREAMING: "▶ Streaming...",
            PhaseStatus.COMPLETE: "✓ Complete",
            PhaseStatus.INTERRUPTED: "⏸ Interrupted",
            PhaseStatus.ERROR: "✗ Error",
            PhaseStatus.REGENERATING: "↻ Regenerating...",
        }
        return status_map.get(self.status, "Unknown")
    
    def _get_token_text(self) -> str:
        """Get token count display."""
        if self.token_count == 1:
            return "1 token"
        return f"{self.token_count} tokens"
    
    def watch_status(self, new_status: PhaseStatus) -> None:
        """React to status changes."""
        # Update CSS class for border color
        self.remove_class("idle", "streaming", "complete", "interrupted", "error", "regenerating")
        self.add_class(new_status.value)
        
        # Update status label
        try:
            status_label = self.query_one(".phase-status", Label)
        except NoMatches:
            # Can happen early in the widget lifecycle before children are composed
            return
        status_label.update(self._get_status_text())
    
    def watch_token_count(self, new_count: int) -> None:
        """React to token count changes."""
        try:
            token_label = self.query_one(".phase-tokens", Label)
        except NoMatches:
            return
        token_label.update(self._get_token_text())
    
    def watch_content(self, new_content: str) -> None:
        """React to content changes."""
        try:
            content_widget = self.query_one(".phase-content", Static)
        except NoMatches:
            return
        content_widget.update(self._truncate_content(new_content))
    
    def _truncate_content(self, content: str) -> str:
        """Truncate content to the last N lines for grid display."""
        lines = content.splitlines()
        if len(lines) <= self._MAX_VISIBLE_LINES:
            return content
        visible = lines[-self._MAX_VISIBLE_LINES :]
        return "…\n" + "\n".join(visible)
    
    def update_from_state(self, state) -> None:
        """Update widget from phase state.
        
        Args:
            state: PhaseStreamState object
        """
        self.status = state.status
        self.content = state.content
        self.token_count = state.token_count

    def on_click(self, event: events.Click) -> None:
        self.focus()


class HelpScreen(ModalScreen):
    """Modal help screen showing keyboard shortcuts and usage."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("?", "dismiss", "Close"),
    ]
    
    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    
    #help-container {
        width: 80%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }
    
    #help-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    
    #help-content {
        height: 1fr;
        margin: 1 0;
    }
    
    .help-section {
        margin: 1 0;
    }
    
    .help-section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0 0 0;
    }
    
    .help-key {
        color: $accent;
        text-style: bold;
    }
    
    .help-desc {
        color: $text;
        margin: 0 0 0 2;
    }
    
    #help-footer {
        text-align: center;
        color: $text-muted;
        margin: 1 0 0 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Container(id="help-container"):
            yield Static("🎼 DEVUSSY TERMINAL UI - HELP", id="help-title")
            
            with Vertical(id="help-content"):
                # Navigation section
                with Container(classes="help-section"):
                    yield Static("Navigation", classes="help-section-title")
                    yield Static("Tab / Shift+Tab / Arrow keys", classes="help-key")
                    yield Static("Move focus between phases", classes="help-desc")
                    yield Static("Mouse click", classes="help-key")
                    yield Static("Focus a phase", classes="help-desc")
                
                # Actions section
                with Container(classes="help-section"):
                    yield Static("Actions", classes="help-section-title")
                    yield Static("c", classes="help-key")
                    yield Static("Cancel focused phase and show steering feedback", classes="help-desc")
                    yield Static("f", classes="help-key")
                    yield Static("Fullscreen view for focused phase", classes="help-desc")
                
                # System section
                with Container(classes="help-section"):
                    yield Static("System", classes="help-section-title")
                    yield Static("q", classes="help-key")
                    yield Static("Quit Devussy", classes="help-desc")
                    yield Static("?", classes="help-key")
                    yield Static("Show this help screen", classes="help-desc")
                    yield Static("Escape", classes="help-key")
                    yield Static("Close dialogs/overlays", classes="help-desc")
                
                # Steering section
                with Container(classes="help-section"):
                    yield Static("Steering Workflow", classes="help-section-title")
                    yield Static("1. Press 'c' on a streaming phase", classes="help-key")
                    yield Static("Cancel generation and open steering dialog", classes="help-desc")
                    yield Static("2. Provide feedback in the form", classes="help-key")
                    yield Static("Describe issues and desired changes", classes="help-desc")
                    yield Static("3. Submit to regenerate", classes="help-key")
                    yield Static("Phase regenerates with your feedback", classes="help-desc")
                
                # Status section
                with Container(classes="help-section"):
                    yield Static("Phase Status Indicators", classes="help-section-title")
                    yield Static("⏸ Idle", classes="help-key")
                    yield Static("Phase has not started", classes="help-desc")
                    yield Static("▶ Streaming", classes="help-key")
                    yield Static("Phase is actively generating", classes="help-desc")
                    yield Static("✓ Complete", classes="help-key")
                    yield Static("Phase finished successfully", classes="help-desc")
                    yield Static("⏸ Interrupted", classes="help-key")
                    yield Static("Phase was cancelled", classes="help-desc")
                    yield Static("✗ Error", classes="help-key")
                    yield Static("Phase encountered an error", classes="help-desc")
                    yield Static("↻ Regenerating", classes="help-key")
                    yield Static("Phase is regenerating with feedback", classes="help-desc")
            
            yield Static("Press ESC, q, or ? to close this help", id="help-footer")


class FullscreenScreen(ModalScreen):
    """Modal fullscreen screen for viewing phase content with scrolling."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Return to Grid"),
        Binding("q", "dismiss", "Return to Grid"),
        Binding("f", "dismiss", "Return to Grid"),
        Binding("j", "scroll_down", "Scroll Down"),
        Binding("k", "scroll_up", "Scroll Up"),
        Binding("down", "scroll_down", "Scroll Down"),
        Binding("up", "scroll_up", "Scroll Up"),
        Binding("home", "scroll_top", "Scroll to Top"),
        Binding("end", "scroll_bottom", "Scroll to Bottom"),
        Binding("pageup", "scroll_page_up", "Page Up"),
        Binding("pagedown", "scroll_page_down", "Page Down"),
    ]
    
    DEFAULT_CSS = """
    FullscreenScreen {
        align: center middle;
    }
    
    #fullscreen-container {
        width: 90%;
        height: 90%;
        border: thick $accent;
        background: $surface;
        padding: 1;
    }
    
    #fullscreen-header {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 0;
        border-bottom: solid $primary;
    }
    
    #fullscreen-title {
        text-align: center;
        text-style: bold reverse;
        color: $accent;
        background: $primary;
        padding: 0 1;
    }
    
    #fullscreen-status {
        text-align: center;
        text-style: bold;
        margin: 1 0 0 0;
    }
    
    #fullscreen-content {
        height: 1fr;
        margin: 1 0;
        border: solid $panel;
        background: $panel;
    }
    
    #fullscreen-content-text {
        padding: 1;
        text-wrap: nowrap;
        height: 100%;
    }
    
    #fullscreen-footer {
        height: auto;
        margin: 1 0 0 0;
        padding: 1 0;
        border-top: solid $primary;
        text-align: center;
        color: $text-muted;
    }
    
    .status-complete {
        color: $success;
    }
    
    .status-streaming {
        color: $accent;
        text-style: italic;
    }
    
    .status-error {
        color: $error;
    }
    
    .status-interrupted {
        color: $warning;
    }
    
    .status-idle {
        color: $secondary;
    }
    
    .status-regenerating {
        color: $accent;
        text-style: bold italic;
    }
    """
    
    def __init__(self, phase_name: str, phase_state, **kwargs):
        """Initialize fullscreen screen.
        
        Args:
            phase_name: Name of the phase to display
            phase_state: PhaseStreamState object with content and status
        """
        super().__init__(**kwargs)
        self.phase_name = phase_name
        self.phase_state = phase_state
    
    def compose(self) -> ComposeResult:
        """Compose the fullscreen screen layout."""
        with Container(id="fullscreen-container"):
            # Header with phase name and status
            with Container(id="fullscreen-header"):
                yield Static(f"🎼 {self.phase_name.upper()} - FULLSCREEN VIEW", id="fullscreen-title")
                status_class = f"status-{self.phase_state.status.value}"
                yield Static(self._get_status_display(), classes=f"fullscreen-status {status_class}")
            
            # Scrollable content area
            with HorizontalScroll(id="fullscreen-content"):
                yield Static(self.phase_state.content or "(No content yet)", id="fullscreen-content-text")
            
            # Footer with character count and help
            with Container(id="fullscreen-footer"):
                char_count = len(self.phase_state.content)
                token_count = self.phase_state.token_count
                yield Static(f"Characters: {char_count} | Tokens: {token_count} | ESC/q/f: Return to Grid | j/k or ↑/↓: Scroll | Home/End: Top/Bottom")
    
    def _get_status_display(self) -> str:
        """Get formatted status display for header."""
        status_map = {
            PhaseStatus.IDLE: "⏸ Idle",
            PhaseStatus.STREAMING: "▶ Streaming...",
            PhaseStatus.COMPLETE: "✓ Complete",
            PhaseStatus.INTERRUPTED: "⏸ Interrupted",
            PhaseStatus.ERROR: "✗ Error",
            PhaseStatus.REGENERATING: "↻ Regenerating...",
        }
        return status_map.get(self.phase_state.status, "Unknown")
    
    def action_scroll_down(self) -> None:
        """Scroll content down."""
        try:
            content = self.query_one("#fullscreen-content", HorizontalScroll)
            content.scroll_down()
        except NoMatches:
            pass
    
    def action_scroll_up(self) -> None:
        """Scroll content up."""
        try:
            content = self.query_one("#fullscreen-content", HorizontalScroll)
            content.scroll_up()
        except NoMatches:
            pass
    
    def action_scroll_top(self) -> None:
        """Scroll to top."""
        try:
            content = self.query_one("#fullscreen-content", HorizontalScroll)
            content.scroll_to(0, 0)
        except NoMatches:
            pass
    
    def action_scroll_bottom(self) -> None:
        """Scroll to bottom."""
        try:
            content = self.query_one("#fullscreen-content", HorizontalScroll)
            content.scroll_to(0, content.scroll_y_max)
        except NoMatches:
            pass
    
    def action_page_up(self) -> None:
        """Scroll page up."""
        try:
            content = self.query_one("#fullscreen-content", HorizontalScroll)
            content.scroll_up(amount=10)
        except NoMatches:
            pass
    
    def action_page_down(self) -> None:
        """Scroll page down."""
        try:
            content = self.query_one("#fullscreen-content", HorizontalScroll)
            content.scroll_down(amount=10)
        except NoMatches:
            pass


class SteeringScreen(ModalScreen):
    """Modal steering interview screen for collecting user feedback."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+enter", "submit", "Submit Feedback"),
    ]
    
    DEFAULT_CSS = """
    SteeringScreen {
        align: center middle;
    }
    
    #steering-container {
        width: 80%;
        height: 80%;
        border: thick $warning;
        background: $surface;
        padding: 2;
    }
    
    #steering-header {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 0;
        border-bottom: solid $warning;
    }
    
    #steering-title {
        text-align: center;
        text-style: bold reverse;
        color: $warning;
        background: $primary;
        padding: 0 1;
    }
    
    #steering-subtitle {
        text-align: center;
        color: $text-muted;
        margin: 1 0 0 0;
    }
    
    #steering-preview {
        height: 20%;
        margin: 1 0;
        border: solid $panel;
        background: $panel;
        padding: 1;
    }
    
    #steering-preview-text {
        text-wrap: nowrap;
        height: 100%;
        overflow-y: auto;
    }
    
    #steering-form {
        height: 1fr;
        margin: 1 0;
    }
    
    .form-field {
        margin: 1 0;
    }
    
    .form-label {
        text-style: bold;
        color: $primary;
        margin: 0 0 0 0;
    }
    
    .form-input {
        margin: 0 0 0 0;
    }
    
    #steering-actions {
        height: auto;
        margin: 1 0 0 0;
        padding: 1 0;
        border-top: solid $primary;
        text-align: center;
    }
    
    Button {
        margin: 0 1;
    }
    
    #cancel-btn {
        background: $error;
    }
    
    #submit-btn {
        background: $success;
    }
    """
    
    def __init__(self, phase_name: str, phase_state, on_submit, **kwargs):
        """Initialize steering screen.
        
        Args:
            phase_name: Name of the phase being steered
            phase_state: PhaseStreamState object with partial content
            on_submit: Callback function to handle feedback submission
        """
        super().__init__(**kwargs)
        self.phase_name = phase_name
        self.phase_state = phase_state
        self.on_submit = on_submit
    
    def compose(self) -> ComposeResult:
        """Compose the steering interview layout."""
        with Container(id="steering-container"):
            # Header
            with Container(id="steering-header"):
                yield Static(f"🎼 {self.phase_name.upper()} - STEERING FEEDBACK", id="steering-title")
                yield Static("Help us improve this phase by providing feedback", id="steering-subtitle")
            
            # Preview of partial content
            with Container(id="steering-preview"):
                yield Static("Partial output so far:", classes="form-label")
                preview_text = self.phase_state.content or "(No content yet)"
                if len(preview_text) > 500:
                    preview_text = preview_text[:500] + "\n... (truncated)"
                yield Static(preview_text, id="steering-preview-text")
            
            # Feedback form
            with Vertical(id="steering-form"):
                # Issue description
                with Container(classes="form-field"):
                    yield Static("What's wrong with the current output?", classes="form-label")
                    yield TextArea(id="issue-input", classes="form-input")
                
                # Desired change
                with Container(classes="form-field"):
                    yield Static("What would you like to see instead?", classes="form-label")
                    yield TextArea(id="desired-input", classes="form-input")
                
                # Constraints
                with Container(classes="form-field"):
                    yield Static("Any constraints or requirements for the new output?", classes="form-label")
                    yield TextArea(id="constraints-input", classes="form-input")
            
            # Action buttons
            with Container(id="steering-actions"):
                yield Button("Cancel (ESC)", id="cancel-btn", variant="error")
                yield Button("Submit Feedback (Ctrl+Enter)", id="submit-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "submit-btn":
            self.action_submit()
    
    def action_cancel(self) -> None:
        """Cancel steering and return to grid."""
        self.dismiss(None)
    
    def action_submit(self) -> None:
        """Submit feedback and return to grid."""
        try:
            issue = self.query_one("#issue-input", TextArea).text
            desired = self.query_one("#desired-input", TextArea).text
            constraints = self.query_one("#constraints-input", TextArea).text
            
            feedback = {
                "issue": issue.strip(),
                "desired": desired.strip(),
                "constraints": constraints.strip(),
            }
            
            # Validate that at least some feedback was provided
            if not feedback["issue"] and not feedback["desired"]:
                self.notify("Please provide at least some feedback before submitting", severity="warning")
                return
            
            self.dismiss(feedback)
            
        except NoMatches:
            self.notify("Error: Could not find form inputs", severity="error")


class DevussyTerminalUI(App):
    """Main Textual app for Devussy terminal streaming UI."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #phase-grid {
        grid-size: 5 1;
        grid-gutter: 1;
        padding: 1;
        height: 1fr;
    }
    
    #phase-grid.medium {
        grid-size: 3 2;
    }
    
    #phase-grid.narrow {
        grid-size: 1 5;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("?", "help", "Help"),
        Binding("c", "cancel_phase", "Cancel Phase"),
        Binding("f", "fullscreen", "Fullscreen"),
        Binding("tab", "focus_next_phase", "Next Phase"),
        Binding("shift+tab", "focus_previous_phase", "Previous Phase"),
        Binding("left", "focus_previous_phase", "Previous Phase"),
        Binding("right", "focus_next_phase", "Next Phase"),
        Binding("up", "focus_previous_phase", "Previous Phase"),
        Binding("down", "focus_next_phase", "Next Phase"),
    ]
    
    TITLE = "Devussy - Terminal Streaming UI"
    SUB_TITLE = "Phase Generation in Progress"
    
    def __init__(
        self,
        phase_names: list[str] = None,
        phase_generator: Optional[TerminalPhaseGenerator] = None,
        devplan: Optional[DevPlan] = None,
    ):
        """Initialize the terminal UI.
        
        Args:
            phase_names: List of phase names (default: ['plan', 'design', 'implement', 'test', 'review'])
            phase_generator: Optional phase generator for streaming
            devplan: Optional devplan for phase generation
        """
        super().__init__()
        self.phase_names = phase_names or ["plan", "design", "implement", "test", "review"]
        self.state_manager = PhaseStateManager(self.phase_names)
        self.phase_boxes = {}
        self.phase_generator = phase_generator
        self.devplan = devplan
        self._generation_tasks: list[asyncio.Task] = []
        self._update_interval = 0.1  # Update UI every 100ms
    
    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        
        # Create grid container
        grid = Grid(id="phase-grid")
        
        # Add phase boxes to grid
        for phase_name in self.phase_names:
            box = PhaseBox(phase_name)
            self.phase_boxes[phase_name] = box
            grid.compose_add_child(box)
        
        yield grid
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle app mount."""
        self._update_grid_layout()
        
        # Start UI update loop
        self.set_interval(self._update_interval, self._update_ui_loop)
        
        # Start phase generation if configured
        if self.phase_generator and self.devplan:
            self._start_generation()
    
    def on_resize(self) -> None:
        """Handle terminal resize."""
        self._update_grid_layout()
    
    def _update_grid_layout(self) -> None:
        """Update grid layout based on terminal width."""
        grid = self.query_one("#phase-grid", Grid)
        width = self.size.width
        
        # Remove existing layout classes
        grid.remove_class("medium", "narrow")
        
        # Apply responsive layout
        if width >= 120:
            # Wide: 5 columns
            grid.styles.grid_size_columns = 5
            grid.styles.grid_size_rows = 1
        elif width >= 80:
            # Medium: 3x2 grid
            grid.add_class("medium")
            grid.styles.grid_size_columns = 3
            grid.styles.grid_size_rows = 2
        else:
            # Narrow: vertical stack
            grid.add_class("narrow")
            grid.styles.grid_size_columns = 1
            grid.styles.grid_size_rows = 5
    
    def _get_focused_phase_name(self) -> Optional[str]:
        focused = getattr(self, "focused", None)
        if focused is None and hasattr(self, "screen"):
            focused = getattr(self.screen, "focused", None)
        if isinstance(focused, PhaseBox):
            return focused.phase_name
        return None
    
    def update_phase(self, phase_name: str) -> None:
        """Update a phase box from state manager.
        
        Args:
            phase_name: Name of phase to update
        """
        if phase_name not in self.phase_boxes:
            return
        
        state = self.state_manager.get_state(phase_name)
        self.phase_boxes[phase_name].update_from_state(state)
    
    def update_all_phases(self) -> None:
        """Update all phase boxes from state manager."""
        for phase_name in self.phase_names:
            self.update_phase(phase_name)
    
    def _update_ui_loop(self) -> None:
        """Periodic UI update loop."""
        self.update_all_phases()
    
    def _start_generation(self) -> None:
        """Start phase generation tasks."""
        if not self.phase_generator or not self.devplan:
            return
        
        # Create generation task
        task = asyncio.create_task(self._run_generation())
        self._generation_tasks.append(task)
    
    async def _run_generation(self) -> None:
        """Run phase generation with streaming."""
        try:
            await self.phase_generator.generate_all_phases(
                self.devplan,
                phase_names=self.phase_names,
            )
            
            # Notify completion
            self.notify("All phases complete!", severity="information")
            
        except Exception as e:
            self.notify(f"Generation error: {e}", severity="error")
    
    def action_focus_next_phase(self) -> None:
        """Move focus to the next phase box in order."""
        boxes = [self.phase_boxes[name] for name in self.phase_names if name in self.phase_boxes]
        if not boxes:
            return

        focused = None
        if hasattr(self, "screen"):
            focused = getattr(self.screen, "focused", None)

        if isinstance(focused, PhaseBox):
            try:
                index = boxes.index(focused)
            except ValueError:
                index = -1
        else:
            index = -1

        next_index = (index + 1) % len(boxes)
        boxes[next_index].focus()

    def action_focus_previous_phase(self) -> None:
        """Move focus to the previous phase box in order."""
        boxes = [self.phase_boxes[name] for name in self.phase_names if name in self.phase_boxes]
        if not boxes:
            return

        focused = None
        if hasattr(self, "screen"):
            focused = getattr(self.screen, "focused", None)

        if isinstance(focused, PhaseBox):
            try:
                index = boxes.index(focused)
            except ValueError:
                index = 0
        else:
            index = 0

        prev_index = (index - 1) % len(boxes)
        boxes[prev_index].focus()
    
    def action_help(self) -> None:
        """Show help screen."""
        self.push_screen(HelpScreen())
    
    def action_cancel_phase(self) -> None:
        """Cancel the currently focused phase and show steering dialog."""
        if not self.phase_generator:
            self.notify("No phase generator configured", severity="warning")
            return

        focused_phase = self._get_focused_phase_name()
        phase_to_cancel = None
        
        if focused_phase is not None:
            state = self.state_manager.get_state(focused_phase)
            if state.status == PhaseStatus.STREAMING:
                phase_to_cancel = focused_phase
        
        # If no focused streaming phase, find the first streaming phase
        if not phase_to_cancel:
            for phase_name in self.phase_names:
                state = self.state_manager.get_state(phase_name)
                if state.status == PhaseStatus.STREAMING:
                    phase_to_cancel = phase_name
                    break
        
        if not phase_to_cancel:
            self.notify("No streaming phase to cancel", severity="information")
            return
        
        # Cancel the phase
        self.phase_generator.cancel_phase(phase_to_cancel)
        self.state_manager.record_cancellation(phase_to_cancel)
        
        # Get the phase state for steering
        phase_state = self.state_manager.get_state(phase_to_cancel)
        
        # Show steering dialog
        def handle_steering_feedback(feedback):
            """Handle feedback from steering screen."""
            if feedback:
                # User provided feedback, regenerate with steering
                self._regenerate_with_steering(phase_to_cancel, feedback)
            else:
                # User cancelled steering, leave phase as interrupted
                self.notify(f"Phase '{phase_to_cancel}' cancelled without regeneration", severity="information")
        
        self.push_screen(SteeringScreen(phase_to_cancel, phase_state, handle_steering_feedback))
    
    def action_fullscreen(self) -> None:
        """Show fullscreen view of focused phase."""
        phase_name = self._get_focused_phase_name()
        if phase_name is None:
            self.notify("No phase focused - use Tab or arrow keys to focus a phase first", severity="warning")
            return
        
        # Get phase state from state manager
        phase_state = self.state_manager.get_state(phase_name)
        
        # Push fullscreen screen
        self.push_screen(FullscreenScreen(phase_name, phase_state))
    
    def _regenerate_with_steering(self, phase_name: str, feedback: dict) -> None:
        """Regenerate a phase with steering feedback.
        
        Args:
            phase_name: Name of the phase to regenerate
            feedback: Dictionary with issue, desired, and constraints
        """
        if not self.phase_generator:
            self.notify("No phase generator configured for regeneration", severity="error")
            return
        
        if not self.devplan:
            self.notify("No devplan available for regeneration", severity="error")
            return
        
        # Record steering feedback
        self.state_manager.record_steering_answers(phase_name, feedback)
        
        # Reset phase for regeneration
        self.state_manager.reset_for_regeneration(phase_name)
        
        # Start regeneration in background
        async def _run_regeneration():
            """Run the regeneration with steering."""
            try:
                await self.phase_generator.regenerate_phase_with_steering(
                    phase_name, 
                    self.devplan, 
                    feedback
                )
                self.notify(f"Phase '{phase_name}' regenerated successfully", severity="success")
            except Exception as e:
                self.notify(f"Regeneration failed for '{phase_name}': {e}", severity="error")
                self.state_manager.record_error(phase_name, str(e))
        
        # Create and start the regeneration task
        task = asyncio.create_task(_run_regeneration())
        self._generation_tasks.append(task)
        
        self.notify(f"Regenerating phase '{phase_name}' with feedback...", severity="information")


def run_terminal_ui(
    phase_names: list[str] = None,
    phase_generator: Optional[TerminalPhaseGenerator] = None,
    devplan: Optional[DevPlan] = None,
) -> None:
    """Run the terminal UI app.
    
    Args:
        phase_names: List of phase names (default: ['plan', 'design', 'implement', 'test', 'review'])
        phase_generator: Optional phase generator for streaming
        devplan: Optional devplan for phase generation
    """
    app = DevussyTerminalUI(
        phase_names=phase_names,
        phase_generator=phase_generator,
        devplan=devplan,
    )
    app.run()


if __name__ == "__main__":
    # Demo mode with simulated phases
    run_terminal_ui()
