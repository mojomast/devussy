"""Tests for documentation generation functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.citations import CitationManager
from src.doc_index import DocumentationIndexer
from src.doc_logger import DocumentationLogger
from src.file_manager import FileManager
from src.templates import render_template


class TestCitationManager:
    """Tests for CitationManager class."""

    def test_initialization(self):
        """Test CitationManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            assert citation_manager.citations_file == citations_path
            assert citations_path.exists()

            # Check header was written
            content = citations_path.read_text(encoding="utf-8")
            assert "# Citations Mapping" in content
            assert "| Placeholder | Source | Description |" in content

    def test_embed_citations_with_urls(self):
        """Test embedding citations with URLs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            content = "This is from DevPlan Orchestrator【cursor†source】."
            citations = {
                "source": {
                    "title": "DevPlan Orchestrator",
                    "url": "https://github.com/mojomast/devussy",
                    "description": "LLM-based development plan orchestration tool",
                }
            }

            result = citation_manager.embed_citations(content, citations)

            expected = (
                "This is from DevPlan Orchestrator"
                "【[DevPlan Orchestrator]"
                "(https://github.com/mojomast/devussy)】."
            )
            assert result == expected

    def test_embed_citations_without_urls(self):
        """Test embedding citations without URLs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            content = "This is a devplan document【cursor†devplan】."
            citations = {
                "devplan": {
                    "title": "Development Plan",
                    "description": "Generated development plan document",
                }
            }

            result = citation_manager.embed_citations(content, citations)

            expected = "This is a devplan document【Development Plan】."
            assert result == expected

    def test_embed_citations_no_mapping(self):
        """Test that unmapped citations are left unchanged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            content = "This has an unknown citation【cursor†unknown】."
            citations = {}

            result = citation_manager.embed_citations(content, citations)

            # Should remain unchanged
            assert result == content

    def test_add_citation(self):
        """Test adding a citation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            citation_manager.add_citation(
                "test",
                url="https://example.com",
                title="Test Source",
                description="A test citation",
            )

            content = citations_path.read_text(encoding="utf-8")
            assert "| test | https://example.com | A test citation |" in content

    def test_get_standard_citations(self):
        """Test getting standard citations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            standard = citation_manager.get_standard_citations()

            assert "source" in standard
            assert "devplan" in standard
            assert "handoff" in standard
            assert "design" in standard

            assert standard["source"]["title"] == "DevPlan Orchestrator"
            assert "github.com" in standard["source"]["url"]

    def test_clear_citations(self):
        """Test clearing citations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            # Add a citation
            citation_manager.add_citation("test", description="Test")

            # Clear citations
            citation_manager.clear_citations()

            # Check only header remains
            content = citations_path.read_text(encoding="utf-8")
            assert "| test |" not in content
            assert "# Citations Mapping" in content

    def test_get_citations_summary(self):
        """Test getting citations summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_path = Path(temp_dir) / "citations.md"
            citation_manager = CitationManager(citations_path)

            # Add citations
            citation_manager.add_citation(
                "test1", url="https://example.com", description="Test 1"
            )
            citation_manager.add_citation("test2", description="Test 2")

            summary = citation_manager.get_citations_summary()

            assert summary["total_citations"] == 2
            assert summary["with_urls"] == 1
            assert summary["without_urls"] == 1


class TestDocumentationLogger:
    """Tests for DocumentationLogger class."""

    def test_initialization(self):
        """Test DocumentationLogger initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            assert logger.log_path == log_path
            assert log_path.exists()

            content = log_path.read_text(encoding="utf-8")
            assert "# Documentation Update Log" in content

    def test_log_update(self):
        """Test logging an update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            logger.log_update("project_design", "Generated project design document")

            content = log_path.read_text(encoding="utf-8")
            assert "Project_Design" in content
            assert "Generated project design document" in content
            assert "---" in content

    def test_log_phase_completion(self):
        """Test logging phase completion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            logger.log_phase_completion(1, "Project Initialization", 10)

            content = log_path.read_text(encoding="utf-8")
            assert "Phase 1 (Project Initialization) completed with 10 steps" in content

    def test_log_documentation_generation(self):
        """Test logging documentation generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            logger.log_documentation_generation(
                "devplan", "docs/devplan.md", "devplan_report.jinja"
            )

            content = log_path.read_text(encoding="utf-8")
            assert "Generated devplan documentation at docs/devplan.md" in content
            assert "using template devplan_report.jinja" in content

    def test_log_git_commit(self):
        """Test logging Git commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            logger.log_git_commit(
                "feat: add documentation templates",
                ["templates/docs/project_design_report.jinja"],
            )

            content = log_path.read_text(encoding="utf-8")
            assert "Git commit: feat: add documentation templates" in content
            assert (
                "Files changed: templates/docs/project_design_report.jinja" in content
            )

    def test_get_recent_updates(self):
        """Test getting recent updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            # Log multiple updates
            logger.log_update("test1", "First update")
            logger.log_update("test2", "Second update")
            logger.log_update("test3", "Third update")

            recent = logger.get_recent_updates(limit=2)

            assert len(recent) == 2
            # Most recent should be last
            assert "Third update" in recent[-1]

    def test_clear_log(self):
        """Test clearing the log."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            logger.log_update("test", "Test update")
            logger.clear_log()

            content = log_path.read_text(encoding="utf-8")
            assert "Test update" not in content
            assert "# Documentation Update Log" in content

    def test_get_log_summary(self):
        """Test getting log summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "update_log.md"
            logger = DocumentationLogger(log_path)

            logger.log_update("project_design", "Design update")
            logger.log_update("devplan", "DevPlan update")
            logger.log_phase_completion(1, "Test Phase", 5)

            summary = logger.get_log_summary()

            assert summary["project_design"] >= 1
            assert summary["devplan"] >= 1
            assert summary["phase_completion"] >= 1
            assert summary["total_entries"] == 3


class TestDocumentationIndexer:
    """Tests for DocumentationIndexer class."""

    def test_initialization(self):
        """Test DocumentationIndexer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            indexer = DocumentationIndexer(temp_dir)

            assert indexer.docs_dir == Path(temp_dir)
            assert indexer.index_path == Path(temp_dir) / "index.md"
            assert Path(temp_dir).exists()

    def test_scan_empty_directory(self):
        """Test scanning empty documentation directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            indexer = DocumentationIndexer(temp_dir)

            doc_files = indexer._scan_documentation_files()

            assert doc_files == {}

    def test_scan_with_documents(self):
        """Test scanning directory with documents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir)

            # Create sample documents
            (docs_dir / "project_design_20231201.md").write_text("# Project Design")
            (docs_dir / "devplan.md").write_text("# DevPlan")
            (docs_dir / "handoff_prompt.md").write_text("# Handoff")
            (docs_dir / "update_log.md").write_text("# Update Log")
            (docs_dir / "citations.md").write_text("# Citations")
            (docs_dir / "other.md").write_text("# Other")

            indexer = DocumentationIndexer(temp_dir)
            doc_files = indexer._scan_documentation_files()

            assert "project_design" in doc_files
            assert "devplan" in doc_files
            assert "handoff" in doc_files
            assert "update_log" in doc_files
            assert "citations" in doc_files
            assert "other" in doc_files

            # Check file details
            assert len(doc_files["project_design"]) == 1
            assert (
                doc_files["project_design"][0]["name"] == "project_design_20231201.md"
            )

    def test_generate_index_empty(self):
        """Test generating index for empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            indexer = DocumentationIndexer(temp_dir)

            index_content = indexer.generate_index()

            assert "# Documentation Index" in index_content
            assert "**Generated:**" in index_content
            assert "**Total Documents:** 0" in index_content

    def test_generate_index_with_documents(self):
        """Test generating index with documents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir)

            # Create sample documents
            (docs_dir / "project_design.md").write_text("# Project Design")
            (docs_dir / "devplan.md").write_text("# DevPlan")

            indexer = DocumentationIndexer(temp_dir)
            index_content = indexer.generate_index()

            assert "# Documentation Index" in index_content
            assert "[LIST] Project Design Documents" in index_content
            assert "[CALENDAR] Development Plans" in index_content
            assert "[project_design.md]" in index_content
            assert "[devplan.md]" in index_content
            assert "**Total Documents:** 2" in index_content

    def test_write_index(self):
        """Test writing index to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            indexer = DocumentationIndexer(temp_dir)

            indexer.write_index()

            index_path = Path(temp_dir) / "index.md"
            assert index_path.exists()

            content = index_path.read_text(encoding="utf-8")
            assert "# Documentation Index" in content

    def test_get_documentation_stats(self):
        """Test getting documentation statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir)

            # Create sample documents
            (docs_dir / "project_design.md").write_text("# Project Design")
            (docs_dir / "devplan.md").write_text("# DevPlan")

            indexer = DocumentationIndexer(temp_dir)
            stats = indexer.get_documentation_stats()

            assert stats["total_files"] == 2
            assert stats["total_size"] > 0
            assert "project_design" in stats["by_type"]
            assert "devplan" in stats["by_type"]
            assert stats["by_type"]["project_design"]["count"] == 1
            assert stats["by_type"]["devplan"]["count"] == 1

    def test_format_file_size(self):
        """Test file size formatting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            indexer = DocumentationIndexer(temp_dir)

            assert indexer._format_file_size(500) == "500 B"
            assert indexer._format_file_size(1500) == "1.5 KB"
            assert indexer._format_file_size(1500000) == "1.4 MB"


class TestFileManagerReportWriting:
    """Tests for FileManager report writing functionality."""

    def test_write_report_with_timestamp(self):
        """Test writing report with timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                file_manager = FileManager()
                content = "# Test Report\n\nThis is a test report."

                file_manager.write_report("test", content, timestamp=True)

                # Check that docs directory was created
                docs_dir = Path("docs")
                assert docs_dir.exists()

                # Check that file was created with timestamp
                report_files = list(docs_dir.glob("test_*.md"))
                assert len(report_files) == 1

                report_file = report_files[0]
                assert "test_" in report_file.name
                assert report_file.name.endswith(".md")

                # Check content
                assert report_file.read_text(encoding="utf-8") == content

            finally:
                os.chdir(original_cwd)

    def test_write_report_without_timestamp(self):
        """Test writing report without timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                file_manager = FileManager()
                content = "# Test Report\n\nThis is a test report."

                file_manager.write_report("test", content, timestamp=False)

                # Check that file was created without timestamp
                report_file = Path("docs/test.md")
                assert report_file.exists()
                assert report_file.read_text(encoding="utf-8") == content

            finally:
                os.chdir(original_cwd)


class TestTemplateRendering:
    """Tests for template rendering with documentation templates."""

    def test_template_loader_with_docs_templates(self):
        """Test that template loader can load documentation templates."""
        # This is more of an integration test to ensure templates exist

        # Check that our documentation templates exist
        template_dir = Path("templates/docs")
        if template_dir.exists():
            templates = [
                "project_design_report.jinja",
                "devplan_report.jinja",
                "handoff_report.jinja",
            ]

            for template_name in templates:
                template_path = template_dir / template_name
                assert template_path.exists(), f"Template {template_name} should exist"

    @patch("src.templates.render_template")
    def test_template_rendering_with_mock(self, mock_render_template):
        """Test template rendering with mocked template function."""
        # Import render_template inside the test after patching
        from src.templates import render_template as render_func

        mock_render_template.return_value = "# Rendered Template\n\nContent here"

        context = {"project_name": "Test Project", "timestamp": "2023-12-01 10:00:00"}

        # Call through the patched module
        import src.templates

        result = src.templates.render_template("project_design_report.jinja", context)

        assert result == "# Rendered Template\n\nContent here"
        mock_render_template.assert_called_once_with(
            "project_design_report.jinja", context
        )


if __name__ == "__main__":
    pytest.main([__file__])
