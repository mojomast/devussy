"""Documentation update logging for tracking changes and progress."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class DocumentationLogger:
    """Logger for tracking documentation updates with timestamps."""

    def __init__(self, log_path: str | Path = "docs/update_log.md"):
        """Initialize the documentation logger.

        Args:
            log_path: Path to the update log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize log file if it doesn't exist
        if not self.log_path.exists():
            self._initialize_log()

    def _initialize_log(self) -> None:
        """Initialize the update log with header."""
        header = """# Documentation Update Log

This log tracks all documentation updates and generation events.

---

"""
        self.log_path.write_text(header, encoding="utf-8")

    def log_update(self, stage: str, description: str) -> None:
        """Log a documentation update with timestamp.

        Args:
            stage: The pipeline stage ('project_design', 'devplan', 'handoff', etc.)
            description: Description of what was updated
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = f"""## {timestamp} - {stage.title()}

{description}

---

"""

        # Append to log file
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(log_entry)

    def log_phase_completion(
        self, phase_number: int, phase_name: str, completed_steps: int
    ) -> None:
        """Log completion of a development phase.

        Args:
            phase_number: Phase number (1, 2, 3, etc.)
            phase_name: Human-readable phase name
            completed_steps: Number of steps completed in the phase
        """
        description = (
            f"Phase {phase_number} ({phase_name}) "
            f"completed with {completed_steps} steps"
        )
        self.log_update("phase_completion", description)

    def log_documentation_generation(
        self, doc_type: str, output_path: str, template_used: str = None
    ) -> None:
        """Log generation of a documentation file.

        Args:
            doc_type: Type of documentation ('project_design', 'devplan', 'handoff')
            output_path: Path where the documentation was written
            template_used: Name of template used (if applicable)
        """
        description = f"Generated {doc_type} documentation at {output_path}"
        if template_used:
            description += f" using template {template_used}"

        self.log_update("documentation_generation", description)

    def log_git_commit(
        self, commit_message: str, files_changed: list[str] = None
    ) -> None:
        """Log Git commits made during documentation process.

        Args:
            commit_message: The commit message
            files_changed: List of files that were changed (optional)
        """
        description = f"Git commit: {commit_message}"
        if files_changed:
            description += f"\nFiles changed: {', '.join(files_changed)}"

        self.log_update("git_commit", description)

    def get_recent_updates(self, limit: int = 10) -> list[str]:
        """Get the most recent update entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent log entries
        """
        if not self.log_path.exists():
            return []

        content = self.log_path.read_text(encoding="utf-8")

        # Split by the separator and filter out header
        entries = [entry.strip() for entry in content.split("---") if entry.strip()]

        # Remove the header (first entry)
        if entries and "Documentation Update Log" in entries[0]:
            entries = entries[1:]

        # Return most recent entries (reverse order since we append to file)
        return entries[-limit:] if entries else []

    def clear_log(self) -> None:
        """Clear the update log and reinitialize."""
        self._initialize_log()

    def get_log_summary(self) -> dict[str, int]:
        """Get summary statistics of logged updates.

        Returns:
            Dictionary with counts of different update types
        """
        if not self.log_path.exists():
            return {}

        content = self.log_path.read_text(encoding="utf-8")

        # Count different types of updates by parsing headers
        # Headers are in format: ## YYYY-MM-DD HH:MM:SS - Stage_Name
        summary = {
            "project_design": 0,
            "devplan": 0,
            "handoff": 0,
            "phase_completion": 0,
            "documentation_generation": 0,
            "git_commit": 0,
            "total_entries": 0,
        }

        # Split by lines and look for headers with timestamps
        lines = content.split("\n")
        for line in lines:
            if line.startswith("## ") and " - " in line:
                summary["total_entries"] += 1
                # Extract stage name and normalize it
                # Format: ## YYYY-MM-DD HH:MM:SS - Stage_Name
                stage = line.split(" - ", 1)[1].strip().lower().replace(" ", "_")
                if stage in summary:
                    summary[stage] += 1

        return summary
