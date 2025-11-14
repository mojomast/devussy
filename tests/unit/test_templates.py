"""Template loading and rendering tests for DevPlan Orchestrator."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from jinja2 import TemplateNotFound

from src.citations import CitationManager
from src.templates import load_template, render_template


@pytest.fixture
def temp_templates_dir():
    """Create temporary templates directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_path = Path(temp_dir)

        # Create test templates
        basic_template = templates_path / "basic.jinja"
        basic_template.write_text("Hello {{ name }}!", encoding="utf-8")

        complex_template = templates_path / "complex.jinja"
        complex_content = """# {{ title }}

## Project: {{ project_name }}

Requirements:
{% for req in requirements %}
- {{ req }}
{% endfor %}

Configuration:
- Language: {{ config.language }}
- Framework: {{ config.framework }}
{% if config.database %}
- Database: {{ config.database }}
{% endif %}
"""
        complex_template.write_text(complex_content, encoding="utf-8")

        # Template with citation placeholder
        citation_template = templates_path / "with_citations.jinja"
        citation_content = """# Documentation

This is based on 【cursor†source】 research.

Key findings:
- Finding 1 【cursor†study1】
- Finding 2 【cursor†study2】

Reference: {{ reference }}
"""
        citation_template.write_text(citation_content, encoding="utf-8")

        yield templates_path


class TestTemplateLoading:
    """Test template loading functionality."""

    def test_templates_dir_function(self):
        """Test _templates_dir function returns correct path."""
        from src.templates import _templates_dir

        templates_dir = _templates_dir()
        assert isinstance(templates_dir, Path)
        assert templates_dir.name == "templates"

    def test_load_existing_template(self):
        """Test loading existing template from actual templates directory."""
        # Use an actual template that exists
        template = load_template("project_design.jinja")
        assert template is not None

        # Test that it can be rendered (with minimal context)
        # Don't assert on specific content since template may change
        result = template.render(
            project_name="Test", requirements=[], languages=[], frameworks=[], apis=[]
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_load_nonexistent_template(self):
        """Test loading non-existent template raises TemplateNotFound."""
        with pytest.raises(TemplateNotFound):
            load_template("nonexistent_template.jinja")

    def test_jinja_template_basic_functionality(self, temp_templates_dir):
        """Test Jinja2 template functionality directly."""
        from jinja2 import Environment, FileSystemLoader

        # Create environment directly for testing
        env = Environment(loader=FileSystemLoader(str(temp_templates_dir)))

        template = env.get_template("basic.jinja")
        result = template.render(name="World")
        assert result == "Hello World!"

        # Test complex template
        complex_template = env.get_template("complex.jinja")
        context = {
            "title": "Development Plan",
            "project_name": "My Project",
            "requirements": ["Feature A", "Feature B"],
            "config": {
                "language": "Python",
                "framework": "FastAPI",
                "database": "PostgreSQL",
            },
        }

        result = complex_template.render(**context)
        assert "# Development Plan" in result
        assert "## Project: My Project" in result
        assert "- Feature A" in result
        assert "- Feature B" in result
        assert "- Language: Python" in result
        assert "- Framework: FastAPI" in result
        assert "- Database: PostgreSQL" in result


class TestTemplateRendering:
    """Test render_template convenience function."""

    def test_render_template_with_real_template(self):
        """Test rendering with actual template file."""
        # Use real template that exists
        result = render_template(
            "project_design.jinja",
            {
                "project_name": "Test Project",
                "requirements": ["Req 1", "Req 2"],
                "languages": ["Python"],
                "frameworks": ["FastAPI"],
                "apis": [],
            },
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test Project" in result

    def test_render_template_missing_context(self, temp_templates_dir):
        """Test template rendering with missing context variables."""
        from jinja2 import Environment, FileSystemLoader, StrictUndefined

        # Use StrictUndefined to force errors on missing variables
        env = Environment(
            loader=FileSystemLoader(str(temp_templates_dir)), undefined=StrictUndefined
        )
        template = env.get_template("basic.jinja")  # This template requires 'name'

        with pytest.raises(Exception):  # Missing 'name' variable will raise an error
            template.render()

    def test_jinja_template_rendering_directly(self, temp_templates_dir):
        """Test template rendering functionality directly."""
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(temp_templates_dir)))

        # Basic template test
        template = env.get_template("basic.jinja")
        result = template.render(name="Test")
        assert result == "Hello Test!"

        # Test with extra context (should be ignored)
        result_extra = template.render(
            name="Test", extra_var="ignored", another_extra=123
        )
        assert result_extra == "Hello Test!"


class TestCitationEmbedding:
    """Test citation embedding functionality."""

    def test_citation_manager_init(self):
        """Test CitationManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            citations_file = Path(temp_dir) / "citations.md"
            cm = CitationManager(citations_file)

            assert cm.citations_file == citations_file
            assert citations_file.exists()

            content = citations_file.read_text(encoding="utf-8")
            assert "# Citations Mapping" in content
            assert "| Placeholder | Source | Description |" in content

    def test_embed_citations_basic(self):
        """Test basic citation embedding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            content = "This is based on 【cursor†source】 research."
            citations = {
                "source": {
                    "title": "Research Paper",
                    "url": "https://example.com/paper",
                    "description": "Academic paper on the topic",
                }
            }

            result = cm.embed_citations(content, citations)
            expected = (
                "This is based on 【[Research Paper](https://example.com/paper)】 "
                "research."
            )

            assert result == expected

    def test_embed_citations_no_url(self):
        """Test citation embedding without URL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            content = "Reference to 【cursor†book】 here."
            citations = {
                "book": {
                    "title": "Great Book",
                    "description": "A great book about the topic",
                }
            }

            result = cm.embed_citations(content, citations)
            expected = "Reference to 【Great Book】 here."

            assert result == expected

    def test_embed_citations_multiple(self):
        """Test embedding multiple citations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            content = """Based on 【cursor†study1】 and 【cursor†study2】 research.
Also see 【cursor†book】 for more info."""

            citations = {
                "study1": {
                    "title": "Study 1",
                    "url": "https://example.com/study1",
                    "description": "First study",
                },
                "study2": {
                    "title": "Study 2",
                    "url": "https://example.com/study2",
                    "description": "Second study",
                },
                "book": {"title": "Reference Book", "description": "A reference book"},
            }

            result = cm.embed_citations(content, citations)

            assert "【[Study 1](https://example.com/study1)】" in result
            assert "【[Study 2](https://example.com/study2)】" in result
            assert "【Reference Book】" in result

    def test_embed_citations_missing_citation(self):
        """Test embedding with missing citation keeps placeholder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            content = "Reference to 【cursor†missing】 here."
            citations = {}  # Empty citations

            result = cm.embed_citations(content, citations)
            expected = "Reference to 【cursor†missing】 here."  # Unchanged

            assert result == expected

    def test_embed_citations_empty_content(self):
        """Test embedding with empty content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            result = cm.embed_citations("", {"source": {"title": "Test"}})
            assert result == ""

    def test_embed_citations_no_citations(self):
        """Test embedding with no citations returns original content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            content = "Some content without citations."
            result = cm.embed_citations(content, {})
            assert result == content

    def test_template_with_citations(self, temp_templates_dir):
        """Test template rendering with citation placeholders."""
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(temp_templates_dir)))

        # Render template first
        template = env.get_template("with_citations.jinja")
        context = {"reference": "Additional Reference"}
        result = template.render(**context)

        # Verify placeholders are preserved
        assert "【cursor†source】" in result
        assert "【cursor†study1】" in result
        assert "【cursor†study2】" in result
        assert "Reference: Additional Reference" in result

        # Now embed citations
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            citations = {
                "source": {
                    "title": "Main Source",
                    "url": "https://example.com/main",
                    "description": "Primary research source",
                },
                "study1": {
                    "title": "First Study",
                    "description": "First research study",
                },
                "study2": {
                    "title": "Second Study",
                    "url": "https://example.com/study2",
                    "description": "Second research study",
                },
            }

            final_result = cm.embed_citations(result, citations)

            assert "【[Main Source](https://example.com/main)】" in final_result
            assert "【First Study】" in final_result
            assert "【[Second Study](https://example.com/study2)】" in final_result

    def test_get_standard_citations(self):
        """Test getting standard citations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            standard = cm.get_standard_citations()

            assert "source" in standard
            assert "devplan" in standard
            assert "handoff" in standard
            assert "design" in standard

            assert standard["source"]["title"] == "DevPlan Orchestrator"
            assert "url" in standard["source"]
            assert "description" in standard["source"]

    def test_add_citation(self):
        """Test adding individual citations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            cm.add_citation(
                placeholder="test_source",
                url="https://example.com/test",
                title="Test Source",
                description="A test source",
            )

            # Check if citation was added to file
            content = cm.citations_file.read_text(encoding="utf-8")
            assert "test_source" in content
            assert "https://example.com/test" in content
            assert "A test source" in content

    def test_citations_file_updates(self):
        """Test that citations file is properly updated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            # Initial state - should have header only
            initial_content = cm.citations_file.read_text(encoding="utf-8")
            assert "# Citations Mapping" in initial_content

            # Add citations via embedding
            citations = {
                "test1": {
                    "title": "Test 1",
                    "url": "https://example.com/1",
                    "description": "First test",
                },
                "test2": {"title": "Test 2", "description": "Second test"},
            }

            cm.embed_citations(
                "Content with 【cursor†test1】 and 【cursor†test2】", citations
            )

            # Check file was updated
            updated_content = cm.citations_file.read_text(encoding="utf-8")
            assert "test1" in updated_content
            assert "test2" in updated_content
            assert "https://example.com/1" in updated_content
            assert "First test" in updated_content
            assert "Second test" in updated_content

    def test_get_citations_summary(self):
        """Test getting citations summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            # Initially empty
            summary = cm.get_citations_summary()
            assert summary["total_citations"] == 0

            # Add citations
            citations = {
                "with_url": {
                    "title": "With URL",
                    "url": "https://example.com",
                    "description": "Has URL",
                },
                "without_url": {"title": "Without URL", "description": "No URL"},
            }

            cm.embed_citations(
                "Test 【cursor†with_url】 and 【cursor†without_url】", citations
            )

            summary = cm.get_citations_summary()
            assert summary["total_citations"] == 2
            assert summary["with_urls"] == 1
            assert summary["without_urls"] == 1

    def test_clear_citations(self):
        """Test clearing all citations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            # Add some citations
            cm.add_citation("test", title="Test", description="Test citation")

            # Verify citation exists
            content = cm.citations_file.read_text(encoding="utf-8")
            assert "test" in content

            # Clear citations
            cm.clear_citations()

            # Verify only header remains
            cleared_content = cm.citations_file.read_text(encoding="utf-8")
            assert "# Citations Mapping" in cleared_content
            assert "test" not in cleared_content


class TestTemplateErrorHandling:
    """Test error handling in template operations."""

    @patch("src.templates._templates_dir")
    def test_load_template_from_nonexistent_directory(self, mock_templates_dir):
        """Test loading template from non-existent directory."""
        mock_templates_dir.return_value = Path("/nonexistent/directory")

        with pytest.raises(Exception):  # Should raise some kind of exception
            load_template("any_template.jinja")

    def test_citation_manager_with_invalid_path(self):
        """Test CitationManager with invalid file path."""
        # Path that should be creatable
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "nested" / "citations.md"
            CitationManager(invalid_path)  # Should create parent directories

            # Should create parent directories
            assert invalid_path.exists()
            assert invalid_path.parent.exists()

    def test_citation_embedding_with_malformed_placeholders(self):
        """Test citation embedding with malformed placeholders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = CitationManager(Path(temp_dir) / "citations.md")

            content = """Various malformed placeholders:
            【cursor†】
            【cursor†invalid-name】
            【cursor†123numbers】
            【notcursor†source】
            【cursor†valid_name】
            """

            citations = {
                "valid_name": {
                    "title": "Valid Citation",
                    "description": "This should work",
                }
            }

            result = cm.embed_citations(content, citations)

            # Only valid_name should be replaced
            assert "【Valid Citation】" in result
            # Others should remain unchanged
            assert "【cursor†】" in result
            assert "【cursor†invalid-name】" in result
            assert "【cursor†123numbers】" in result
            assert "【notcursor†source】" in result
