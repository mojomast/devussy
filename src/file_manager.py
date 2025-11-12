"""Markdown file utilities for reading/writing/updating sections."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, List

from .logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """Utility methods for working with markdown and text files."""

    def read_markdown(self, path: str | Path) -> str:
        p = Path(path)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def write_markdown(self, path: str | Path, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # --- Safe devplan writing helpers ---
    def _validate_devplan_content(self, content: str) -> Tuple[bool, List[str]]:
        """Validate that devplan dashboard content keeps required invariants.

        Returns (is_valid, reasons_if_invalid).
        """
        reasons: List[str] = []
        def has(s: str) -> bool:
            return s in content
        # Minimal invariants
        if not (has("# Development Plan") or has("## 📋 Project Dashboard")):
            reasons.append("missing dashboard header")
        if not (has("### 🚀 Phase Overview") and ("| Phase |" in content)):
            reasons.append("missing phase overview table")
        if "<!-- PROGRESS_LOG_START -->" not in content:
            reasons.append("missing PROGRESS_LOG anchors")
        if "<!-- NEXT_TASK_GROUP_START -->" not in content:
            reasons.append("missing NEXT_TASK_GROUP anchors")
        return (len(reasons) == 0, reasons)

    def safe_write_devplan(self, path: str | Path, content: str) -> Tuple[bool, str]:
        """Safely write devplan.md with backup and invariant checks.

        - Creates a .bak of the existing file (if present) before any write.
        - Validates the new content keeps dashboard/table and core anchors.
        - If invalid, writes to <path>.tmp instead and keeps the original.

        Returns (success, written_path).
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        if p.exists():
            try:
                bak = p.with_suffix(p.suffix + ".bak")
                bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
                logger.info(f"Backed up devplan to {bak}")
            except Exception as e:
                logger.warning(f"Failed to create backup for {p}: {e}")

        is_valid, reasons = self._validate_devplan_content(content)
        if not is_valid:
            tmp_path = str(p) + ".tmp"
            try:
                Path(tmp_path).write_text(content, encoding="utf-8")
                logger.warning(
                    "Refused to overwrite devplan.md due to invariants missing: %s. "
                    "Wrote candidate content to %s",
                    ", ".join(reasons),
                    tmp_path,
                )
            except Exception as e:
                logger.error(f"Failed to write devplan tmp file {tmp_path}: {e}")
            return False, tmp_path

        # Proceed with normal write
        try:
            p.write_text(content, encoding="utf-8")
            logger.info(f"Wrote devplan dashboard to {p}")
            return True, str(p)
        except Exception as e:
            logger.error(f"Failed to write devplan {p}: {e}")
            tmp_path = str(p) + ".tmp"
            try:
                Path(tmp_path).write_text(content, encoding="utf-8")
            except Exception:
                pass
            return False, tmp_path

    def append_to_file(self, path: str | Path, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(content)

    def update_section(self, path: str | Path, section_name: str, content: str) -> None:
        """Replace a markdown section identified by a heading with new content.

        A section is identified by a heading line like `# Section Name` or
        `## Section Name`. Replacement includes the heading line and continues
        up to (but not including) the next heading of the same or higher level.
        If the section does not exist, it will be appended at the end.
        """
        text = self.read_markdown(path)
        if not text:
            # create new document with a top-level heading
            new_text = f"# {section_name}\n\n{content}\n"
            self.write_markdown(path, new_text)
            return

        # Match headings like: ### Section Name
        heading_pattern = rf"^(?P<hashes>#{{1,6}})\s+{re.escape(section_name)}\s*$"
        matches = list(re.finditer(heading_pattern, text, flags=re.MULTILINE))

        if not matches:
            # Append new section
            new_text = text.rstrip() + f"\n\n## {section_name}\n\n{content}\n"
            self.write_markdown(path, new_text)
            return

        # Replace the first matching section
        first = matches[0]
        level = len(first.group("hashes"))
        start = first.start()

        # Find the next heading with level <= current level
        next_heading_regex = rf"^#{{1,{level}}}\s+.+$"
        next_match = re.search(
            next_heading_regex, text[first.end() :], flags=re.MULTILINE
        )
        if next_match:
            end = first.end() + next_match.start()
        else:
            end = len(text)

        replacement = f"{'#' * level} {section_name}\n\n{content}\n"
        new_text = text[:start] + replacement + text[end:]
        self.write_markdown(path, new_text)

    def write_report(
        self, report_type: str, content: str, timestamp: bool = True
    ) -> None:
        """Write a formatted report to the docs/ directory with structured naming.

        Args:
            report_type: Type of report ('project_design', 'devplan', 'handoff')
            content: The content to write
            timestamp: Whether to add timestamp to filename
        """
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)

        # Create structured filename
        if timestamp:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_{timestamp_str}.md"
        else:
            filename = f"{report_type}.md"

        file_path = docs_dir / filename
        self.write_markdown(file_path, content)
