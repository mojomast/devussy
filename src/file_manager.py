"""Markdown file utilities for reading/writing/updating sections."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


class FileManager:
    """Utility methods for working with markdown and text files."""

    def read_markdown(self, path: str | Path) -> str:
        p = Path(path)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def write_markdown(self, path: str | Path, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

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
