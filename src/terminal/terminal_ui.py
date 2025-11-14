"""Textual-based terminal UI for streaming phase generation.

This module provides a modern TUI for displaying 5 phases (plan, design,
implement, test, review) in a responsive grid layout with real-time streaming.
"""

import asyncio
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import Header, Footer, Static, Label
from textual.reactive import reactive
from textual.binding import Binding
from rich.text import Text

from .phase_state import PhaseStateManager, PhaseStatus
from .phase_generator import TerminalPhaseGenerator
from ..models import DevPlan


class PhaseBox(Static):
    """Widget displaying a single phase with status and content."""
    
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
    
    PhaseBox .phase-title {
        text-style: bold;
        background: $boost;
        padding: 0 1;
    }
    
    PhaseBox .phase-status {
        color: $text-muted;
        padding: 0 1;
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
    
    def watch_status(self, new_status: PhaseStatus) -> None:
        """React to status changes."""
        # Update CSS class for border color
        self.remove_class("idle", "streaming", "complete", "interrupted", "error", "regenerating")
        self.add_class(new_status.value)
        
        # Update status label
        status_label = self.query_one(".phase-status", Label)
        status_label.update(self._get_status_text())
    
    def watch_content(self, new_content: str) -> None:
        """React to content changes."""
        content_widget = self.query_one(".phase-content", Static)
        content_widget.update(new_content)
    
    def update_from_state(self, state) -> None:
        """Update widget from phase state.
        
        Args:
            state: PhaseStreamState object
        """
        self.status = state.status
        self.content = state.content


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
    
    def action_help(self) -> None:
        """Show help screen."""
        help_text = [
            "Keyboard Shortcuts:",
            "  q - Quit",
            "  c - Cancel focused phase",
            "  f - Fullscreen view (coming soon)",
            "  ? - Show this help",
        ]
        self.notify("\n".join(help_text))
    
    def action_cancel_phase(self) -> None:
        """Cancel the currently focused phase."""
        # For now, cancel the first streaming phase
        if not self.phase_generator:
            self.notify("No phase generator configured", severity="warning")
            return
        
        for phase_name in self.phase_names:
            state = self.state_manager.get_state(phase_name)
            if state.status == PhaseStatus.STREAMING:
                self.phase_generator.cancel_phase(phase_name)
                self.notify(f"Cancelled phase: {phase_name}", severity="warning")
                return
        
        self.notify("No streaming phase to cancel", severity="information")
    
    def action_fullscreen(self) -> None:
        """Show fullscreen view of focused phase."""
        self.notify("Fullscreen view coming soon!")


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
