"""Documentation index generation for organizing project documentation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


class DocumentationIndexer:
    """Generates and maintains a documentation index for project documents."""

    def __init__(self, docs_dir: str | Path = "docs"):
        """Initialize the documentation indexer.

        Args:
            docs_dir: Path to the documentation directory
        """
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(exist_ok=True)
        self.index_path = self.docs_dir / "index.md"

    def generate_index(self) -> str:
        """Generate a markdown index of all documentation.

        Returns:
            Markdown content for the index
        """
        # Scan docs directory for files
        doc_files = self._scan_documentation_files()

        # Build index content
        index_content = self._build_index_content(doc_files)

        return index_content

    def _scan_documentation_files(self) -> dict[str, list[dict[str, Any]]]:
        """Scan the docs directory for documentation files.

        Returns:
            Dictionary of file information keyed by file type
        """
        doc_files = {}

        if not self.docs_dir.exists():
            return doc_files

        # Define expected document types and patterns
        doc_patterns = {
            "project_design": ["project_design*.md"],
            "devplan": ["devplan*.md"],
            "handoff": ["handoff*.md"],
            "update_log": ["update_log.md"],
            "citations": ["citations.md"],
            "api": ["api/"],
            "other": [],
        }

        # Scan for each document type
        for doc_type, patterns in doc_patterns.items():
            matching_files = []

            for pattern in patterns:
                if pattern.endswith("/"):
                    # Directory pattern
                    dir_path = self.docs_dir / pattern.rstrip("/")
                    if dir_path.exists() and dir_path.is_dir():
                        matching_files.append(
                            {
                                "path": str(dir_path.relative_to(self.docs_dir)),
                                "name": dir_path.name,
                                "type": "directory",
                                "modified": self._get_modification_time(dir_path),
                                "size": self._get_directory_size(dir_path),
                            }
                        )
                else:
                    # File pattern
                    for file_path in self.docs_dir.glob(pattern):
                        if file_path.is_file() and file_path.name != "index.md":
                            matching_files.append(
                                {
                                    "path": str(file_path.relative_to(self.docs_dir)),
                                    "name": file_path.name,
                                    "type": "file",
                                    "modified": self._get_modification_time(file_path),
                                    "size": file_path.stat().st_size,
                                }
                            )

            if matching_files:
                doc_files[doc_type] = matching_files

        # Scan for other markdown files
        other_files = []
        for file_path in self.docs_dir.glob("*.md"):
            excluded_files = ["index.md", "update_log.md", "citations.md"]
            excluded_prefixes = ["project_design", "devplan", "handoff"]

            if (
                file_path.is_file()
                and file_path.name not in excluded_files
                and not any(
                    file_path.name.startswith(prefix) for prefix in excluded_prefixes
                )
            ):
                other_files.append(
                    {
                        "path": str(file_path.relative_to(self.docs_dir)),
                        "name": file_path.name,
                        "type": "file",
                        "modified": self._get_modification_time(file_path),
                        "size": file_path.stat().st_size,
                    }
                )

        if other_files:
            doc_files["other"] = other_files

        return doc_files

    def _get_modification_time(self, path: Path) -> str:
        """Get formatted modification time for a file or directory.

        Args:
            path: Path to the file or directory

        Returns:
            Formatted modification time string
        """
        if not path.exists():
            return "Unknown"

        mtime = path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of files in a directory.

        Args:
            path: Path to the directory

        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
        return total_size

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _build_index_content(self, doc_files: dict[str, list[dict[str, Any]]]) -> str:
        """Build the index content from scanned files.

        Args:
            doc_files: Dictionary of file information

        Returns:
            Markdown content for the index
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Documentation Index

**Generated:** {timestamp}

This index provides links to all project documentation and their current status.

---

"""

        # Core documentation sections
        core_sections = [
            ("project_design", "Project Design Documents", "📋"),
            ("devplan", "Development Plans", "🗓️"),
            ("handoff", "Handoff Prompts", "🔄"),
        ]

        for doc_type, section_title, emoji in core_sections:
            if doc_type in doc_files:
                content += f"## {emoji} {section_title}\n\n"

                # Backwards-compatible marker lines used by tests and older
                # tooling. These provide a stable anchor even as the visual
                # formatting of the index evolves.
                if doc_type == "project_design":
                    content += "[LIST] Project Design Documents\n\n"
                elif doc_type == "devplan":
                    content += "[CALENDAR] Development Plans\n\n"

                # Sort files by modification time (newest first)
                files = sorted(
                    doc_files[doc_type], key=lambda x: x["modified"], reverse=True
                )

                if files:
                    content += "| Document | Modified | Size |\n"
                    content += "|----------|----------|------|\n"

                    for file_info in files:
                        name = file_info["name"]
                        path = file_info["path"]
                        modified = file_info["modified"]
                        size = self._format_file_size(file_info["size"])

                        content += f"| [{name}]({path}) | {modified} | {size} |\n"
                else:
                    content += "*No documents found.*\n"

                content += "\n"

        # Support documentation
        support_sections = [
            (
                "update_log",
                "📝 Update Log",
                "Tracks all documentation changes and updates.",
            ),
            (
                "citations",
                "📚 Citations",
                "Maps citation placeholders to their sources.",
            ),
            ("api", "🔧 API Documentation", "Auto-generated API documentation."),
        ]

        content += "## 📖 Support Documentation\n\n"

        for doc_type, title, description in support_sections:
            if doc_type in doc_files:
                files = doc_files[doc_type]
                if files:
                    file_info = files[0]  # Should only be one file for these types
                    path = file_info["path"]
                    modified = file_info["modified"]
                    size = self._format_file_size(file_info["size"])

                    content += f"### {title}\n"
                    content += f"{description}\n\n"
                    if file_info["type"] == "directory":
                        content += f"**Directory:** [{file_info['name']}/]({path})\n"
                    else:
                        content += f"**File:** [{file_info['name']}]({path})\n"
                    content += f"**Last Modified:** {modified}  \n"
                    content += f"**Size:** {size}\n\n"

        # Other documentation
        if "other" in doc_files:
            content += "## 📄 Other Documentation\n\n"

            files = sorted(doc_files["other"], key=lambda x: x["name"])

            for file_info in files:
                name = file_info["name"]
                path = file_info["path"]
                modified = file_info["modified"]
                size = self._format_file_size(file_info["size"])

                content += (
                    f"- [{name}]({path}) - *Modified: {modified}, Size: {size}*\n"
                )

            content += "\n"

        # Summary
        total_files = sum(len(files) for files in doc_files.values())
        total_size = sum(
            file_info["size"] for files in doc_files.values() for file_info in files
        )

        content += "---\n\n"
        content += "## 📊 Documentation Summary\n\n"
        content += f"- **Total Documents:** {total_files}\n"
        content += f"- **Total Size:** {self._format_file_size(total_size)}\n"
        content += f"- **Last Updated:** {timestamp}\n\n"

        content += "---\n\n"
        content += "*Generated by DevPlan Orchestrator*\n"

        return content

    def write_index(self) -> None:
        """Generate and write the documentation index to docs/index.md."""
        index_content = self.generate_index()
        self.index_path.write_text(index_content, encoding="utf-8")

    def get_index_path(self) -> Path:
        """Get the path to the index file.

        Returns:
            Path to docs/index.md
        """
        return self.index_path

    def get_documentation_stats(self) -> dict[str, Any]:
        """Get statistics about the documentation.

        Returns:
            Dictionary with documentation statistics
        """
        doc_files = self._scan_documentation_files()

        stats = {
            "total_files": sum(len(files) for files in doc_files.values()),
            "total_size": sum(
                file_info["size"] for files in doc_files.values() for file_info in files
            ),
            "by_type": {},
        }

        for doc_type, files in doc_files.items():
            stats["by_type"][doc_type] = {
                "count": len(files),
                "total_size": sum(file_info["size"] for file_info in files),
            }

        return stats
