"""Progress reporting for pipeline execution.

Provides visual feedback during pipeline stages using Rich library,
including spinners, token counts, and file creation updates.
"""

from __future__ import annotations

from typing import Any, Optional
from contextlib import contextmanager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from .logger import get_logger

logger = get_logger(__name__)


class PipelineProgressReporter:
    """Reports pipeline progress with visual feedback."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the progress reporter.
        
        Args:
            console: Optional Rich console instance. Creates a new one if not provided.
        """
        self.console = console or Console()
        self.current_stage = ""
        self.total_stages = 4  # design, basic devplan, detailed devplan, handoff
        self.completed_stages = 0
        self.files_created = []
        self.total_tokens_used = 0
        self.last_usage = {}
        # Live status bar and phase progress
        self._status_live: Live | None = None
        self._phase_progress: Progress | None = None
        self._phase_task_id: int | None = None
        self._phase_total: int = 0
        # Track if we paused status for a nested progress/spinner
        self._status_paused_for_progress: bool = False
        
    def start_pipeline(self, project_name: str) -> None:
        """Display pipeline start banner.
        
        Args:
            project_name: Name of the project being generated
        """
        self.console.print()
        self.console.print("=" * 60, style="bold cyan")
        self.console.print(f"[ROCKET] Pipeline Started: {project_name}", style="bold cyan")
        self.console.print("=" * 60, style="bold cyan")
        self.console.print()
        
    def _render_status_text(self) -> Text:
        usage = self.last_usage or {}
        p = usage.get("prompt_tokens")
        c = usage.get("completion_tokens")
        t = usage.get("total_tokens")
        model = usage.get("model") or ""
        # Fallback placeholders
        def fmt(v):
            return "-" if v is None else str(v)
        text = Text(
            f"{model} | Stage: {self.current_stage or '-'} | Tokens p:{fmt(p)} c:{fmt(c)} tot:{fmt(t)} | Accum:{self.total_tokens_used}",
            style="black on white",
        )
        return text

    def start_status(self) -> None:
        if self._status_live is None:
            self._status_live = Live(self._render_status_text(), refresh_per_second=4, console=self.console)
            self._status_live.start()

    def stop_status(self) -> None:
        if self._status_live is not None:
            self._status_live.stop()
            self._status_live = None

    def refresh_status(self) -> None:
        if self._status_live is not None:
            self._status_live.update(self._render_status_text(), refresh=True)

    def start_stage(self, stage_name: str, stage_number: int) -> None:
        """Mark the start of a pipeline stage.
        
        Args:
            stage_name: Name of the stage being executed
            stage_number: Stage number (1-4)
        """
        self.current_stage = stage_name
        self.console.print()
        self.console.print(
            f"[bold yellow]Stage {stage_number}/{self.total_stages}:[/bold yellow] "
            f"[cyan]{stage_name}[/cyan]"
        )
        logger.info(f"Starting stage {stage_number}/{self.total_stages}: {stage_name}")
        self.refresh_status()
        
    def end_stage(self, stage_name: str, success: bool = True) -> None:
        """Mark the end of a pipeline stage.
        
        Args:
            stage_name: Name of the completed stage
            success: Whether the stage completed successfully
        """
        self.completed_stages += 1
        status = "✓" if success else "✗"
        color = "green" if success else "red"
        self.console.print(f"[{color}]{status} {stage_name} complete[/{color}]")
        logger.info(f"Completed stage: {stage_name} (success={success})")
        self.refresh_status()
        
    def update_tokens(self, usage_metadata: Optional[dict]) -> None:
        """Update token usage information.
        
        Args:
            usage_metadata: Dictionary containing token usage info from LLM client
        """
        if not usage_metadata:
            return
            
        self.last_usage = usage_metadata
        prompt_tokens = usage_metadata.get("prompt_tokens", 0) or 0
        completion_tokens = usage_metadata.get("completion_tokens", 0) or 0
        total = usage_metadata.get("total_tokens", 0) or 0
        
        if total > 0:
            self.total_tokens_used += total
            
        logger.debug(
            f"Token usage - Prompt: {prompt_tokens}, "
            f"Completion: {completion_tokens}, Total: {total}"
        )
        self.refresh_status()
        
    def report_file_created(
        self, 
        file_path: str, 
        file_type: str = "file",
        token_count: Optional[int] = None
    ) -> None:
        """Report that a file has been created.
        
        Args:
            file_path: Path to the created file
            file_type: Type/description of file (e.g., "design", "devplan", "phase")
            token_count: Optional token count for the file content
        """
        self.files_created.append({
            "path": file_path,
            "type": file_type,
            "tokens": token_count
        })
        
        token_info = f" ({token_count:,} tokens)" if token_count else ""
        self.console.print(
            f"  [dim]→[/dim] Created [green]{file_type}[/green]: "
            f"[blue]{file_path}[/blue]{token_info}"
        )
        logger.info(f"Created {file_type}: {file_path} (tokens={token_count})")
        
    def show_checkpoint_saved(self, checkpoint_key: str, stage: str) -> None:
        """Display checkpoint save information.
        
        Args:
            checkpoint_key: Key identifier for the checkpoint
            stage: Stage name that was checkpointed
        """
        self.console.print(
            f"  [dim][SAVE] Checkpoint saved: {checkpoint_key} ({stage})[/dim]"
        )
        
    def show_phase_generation(self, phase_number: int, phase_title: str) -> None:
        """Display that a phase is being generated.
        
        Args:
            phase_number: Number of the phase
            phase_title: Title of the phase
        """
        self.console.print(
            f"  [dim]→ Generating Phase {phase_number}: {phase_title}...[/dim]"
        )
        
    def show_concurrent_phases(self, phase_count: int) -> None:
        """Display that phases are being generated concurrently.
        
        Args:
            phase_count: Number of phases being generated
        """
        self.console.print(
            f"  [yellow][FAST] Generating {phase_count} phases concurrently...[/yellow]"
        )
        
    def start_phase_progress(self, total: int, description: str = "Generating phases") -> None:
        if self._phase_progress is None:
            # Avoid overlapping Live renders: pause status bar if running
            if self._status_live is not None:
                self.stop_status()
                self._status_paused_for_progress = True
            self._phase_total = total
            self._phase_progress = Progress(
                SpinnerColumn(),
                TextColumn("[cyan]" + description + "[/cyan]"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn(" • {task.completed}/{task.total}"),
                console=self.console,
                transient=True,
            )
            self._phase_progress.start()
            self._phase_task_id = self._phase_progress.add_task(description, total=total)

    def advance_phase(self) -> None:
        if self._phase_progress is not None and self._phase_task_id is not None:
            self._phase_progress.update(self._phase_task_id, advance=1)

    def stop_phase_progress(self) -> None:
        if self._phase_progress is not None:
            try:
                if self._phase_task_id is not None:
                    self._phase_progress.update(self._phase_task_id, completed=self._phase_total)
            except Exception:
                pass
            self._phase_progress.stop()
            self._phase_progress = None
            self._phase_task_id = None
            self._phase_total = 0
            # Resume status bar if we paused it for progress
            if self._status_paused_for_progress:
                self.start_status()
                self.refresh_status()
                self._status_paused_for_progress = False

    def create_spinner_context(self, description: str, show_tokens: bool = True):
        """Create a context manager for spinner display during async operations.
        
        Args:
            description: Description of the operation
            show_tokens: Whether to show token usage in the spinner
            
        Returns:
            Rich Progress context manager
        """
        if show_tokens and self.last_usage:
            prompt_tokens = self.last_usage.get("prompt_tokens", 0) or 0
            completion_tokens = self.last_usage.get("completion_tokens", 0) or 0
            token_display = f" (tokens: {prompt_tokens}→{completion_tokens})"
        else:
            token_display = ""

        @contextmanager
        def _spinner_cm():
            # If a Progress bar is active, avoid creating another Live context.
            # Just yield a no-op so calling code can use `with` uniformly.
            if self._phase_progress is not None:
                try:
                    yield None
                finally:
                    return
            # To prevent clashing Live renderers, pause status if running
            status_was_running = self._status_live is not None
            if status_was_running:
                self.stop_status()
            try:
                with self.console.status(
                    f"[cyan]{description}{token_display}[/cyan]",
                    spinner="dots",
                ) as _cm:
                    yield _cm
            finally:
                if status_was_running:
                    self.start_status()
                    self.refresh_status()

        return _spinner_cm()
        
    def display_summary(self) -> None:
        """Display a summary of the completed pipeline."""
        self.console.print()
        self.console.print("=" * 60, style="bold green")
        self.console.print("✓ Pipeline Complete!", style="bold green")
        self.console.print("=" * 60, style="bold green")
        self.console.print()
        
        # Stop status bar and any phase progress
        self.stop_phase_progress()
        self.stop_status()
        
        # Create summary table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Stages Completed", f"{self.completed_stages}/{self.total_stages}")
        table.add_row("Files Created", str(len(self.files_created)))
        table.add_row("Total Tokens Used", f"{self.total_tokens_used:,}")
        
        self.console.print(table)
        self.console.print()
        
        # List created files
        if self.files_created:
            self.console.print("[bold]Generated Files:[/bold]")
            for file_info in self.files_created:
                file_path = file_info["path"]
                file_type = file_info["type"]
                tokens = file_info.get("tokens")
                
                token_str = f" ({tokens:,} tokens)" if tokens else ""
                self.console.print(
                    f"  [green]•[/green] {file_type}: [blue]{file_path}[/blue]{token_str}"
                )
            self.console.print()
            
        logger.info(
            f"Pipeline summary - Stages: {self.completed_stages}/{self.total_stages}, "
            f"Files: {len(self.files_created)}, Tokens: {self.total_tokens_used}"
        )
        
    def display_error(self, error_message: str) -> None:
        """Display an error message.
        
        Args:
            error_message: The error message to display
        """
        self.console.print()
        self.console.print(f"[bold red][ERROR] Error:[/bold red] {error_message}")
        self.console.print()
        logger.error(f"Pipeline error: {error_message}")
