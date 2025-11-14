"""Citation management utilities for documentation generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class CitationManager:
    """Manages citation embedding and tracking for generated documentation."""

    def __init__(self, citations_file: str | Path = "docs/citations.md"):
        """Initialize the citation manager.

        Args:
            citations_file: Path to the citations mapping file
        """
        self.citations_file = Path(citations_file)
        self.citations_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize citations file if it doesn't exist
        if not self.citations_file.exists():
            self._initialize_citations_file()

    def _initialize_citations_file(self) -> None:
        """Initialize the citations file with header."""
        header = """# Citations Mapping

This file maps citation placeholders to their sources.

| Placeholder | Source | Description |
|-------------|--------|-------------|
"""
        self.citations_file.write_text(header, encoding="utf-8")

    def embed_citations(
        self, content: str, citations: dict[str, dict[str, Any]]
    ) -> str:
        """Embed citations into content by replacing placeholders.

        Args:
            content: The content containing citation placeholders
            citations: Dictionary mapping placeholder names to citation info
                      Format: {"source": {"url": "...", "title": "...",
                               "description": "..."}}

        Returns:
            Content with embedded citations
        """
        if not citations:
            return content

        # Pattern to match citation placeholders like 【cursor†source】
        citation_pattern = r"【cursor†(\w+)】"

        def replace_citation(match):
            placeholder_name = match.group(1)
            if placeholder_name in citations:
                citation_info = citations[placeholder_name]

                # Create citation link
                if "url" in citation_info:
                    citation_text = (
                        f"[{citation_info.get('title', placeholder_name)}]"
                        f"({citation_info['url']})"
                    )
                else:
                    citation_text = citation_info.get("title", placeholder_name)

                return f"【{citation_text}】"
            else:
                # Keep placeholder if no mapping found
                return match.group(0)

        # Replace all citation placeholders
        updated_content = re.sub(citation_pattern, replace_citation, content)

        # Update citations mapping file
        self._update_citations_mapping(citations)

        return updated_content

    def _update_citations_mapping(self, citations: dict[str, dict[str, Any]]) -> None:
        """Update the citations mapping file with new citations.

        Args:
            citations: Dictionary of citations to add/update
        """
        # Read existing content
        existing_content = self.citations_file.read_text(encoding="utf-8")

        # Parse existing citations (simple approach)
        existing_citations = self._parse_existing_citations(existing_content)

        # Merge with new citations
        existing_citations.update(citations)

        # Rebuild the file
        header = """# Citations Mapping

This file maps citation placeholders to their sources.

| Placeholder | Source | Description |
|-------------|--------|-------------|
"""

        rows = []
        for placeholder, info in existing_citations.items():
            source = info.get("url", info.get("title", "Unknown"))
            description = info.get("description", "No description")
            rows.append(f"| {placeholder} | {source} | {description} |")

        new_content = header + "\n".join(rows) + "\n"
        self.citations_file.write_text(new_content, encoding="utf-8")

    def _parse_existing_citations(self, content: str) -> dict[str, dict[str, Any]]:
        """Parse existing citations from the mapping file.

        Args:
            content: Content of the citations file

        Returns:
            Dictionary of existing citations
        """
        citations = {}

        # Simple regex to parse table rows
        row_pattern = r"\|\s*(\w+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"

        for match in re.finditer(row_pattern, content):
            placeholder = match.group(1).strip()
            source = match.group(2).strip()
            description = match.group(3).strip()

            # Skip header row
            if placeholder.lower() == "placeholder":
                continue

            citations[placeholder] = {
                "title": placeholder,
                "url": source if source.startswith("http") else None,
                "description": description,
            }

        return citations

    def add_citation(
        self,
        placeholder: str,
        url: str = None,
        title: str = None,
        description: str = None,
    ) -> None:
        """Add a new citation mapping.

        Args:
            placeholder: The placeholder name (without 【cursor†】)
            url: URL to the source (optional)
            title: Title of the source (optional)
            description: Description of the source
        """
        citation = {
            "title": title or placeholder,
            "description": description or "No description",
        }

        if url:
            citation["url"] = url

        self._update_citations_mapping({placeholder: citation})

    def get_standard_citations(self) -> dict[str, dict[str, Any]]:
        """Get standard citations for DevPlan Orchestrator.

        Returns:
            Dictionary of standard citations
        """
        return {
            "source": {
                "title": "DevPlan Orchestrator",
                "url": "https://github.com/mojomast/devussy",
                "description": "LLM-based development plan orchestration tool",
            },
            "devplan": {
                "title": "Development Plan",
                "description": "Generated development plan document",
            },
            "handoff": {
                "title": "Handoff Prompt",
                "description": "Generated handoff instructions",
            },
            "design": {
                "title": "Project Design",
                "description": "Generated project design document",
            },
        }

    def clear_citations(self) -> None:
        """Clear all citations and reinitialize the mapping file."""
        self._initialize_citations_file()

    def get_citations_summary(self) -> dict[str, int]:
        """Get summary of citations in the mapping file.

        Returns:
            Dictionary with citation statistics
        """
        if not self.citations_file.exists():
            return {"total_citations": 0}

        content = self.citations_file.read_text(encoding="utf-8")
        existing_citations = self._parse_existing_citations(content)

        return {
            "total_citations": len(existing_citations),
            "with_urls": sum(1 for c in existing_citations.values() if c.get("url")),
            "without_urls": sum(
                1 for c in existing_citations.values() if not c.get("url")
            ),
        }
