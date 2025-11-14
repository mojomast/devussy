"""
Unit tests for CodeSampleExtractor.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.interview.code_sample_extractor import CodeSampleExtractor, CodeSample
from src.interview.repository_analyzer import (
    RepoAnalysis,
    DirectoryStructure,
    DependencyInfo,
    CodeMetrics,
    CodePatterns,
    ConfigFiles,
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # Create directory structure
    (repo_path / "src").mkdir()
    (repo_path / "tests").mkdir()
    (repo_path / "config").mkdir()
    
    # Create sample Python files
    (repo_path / "src" / "__init__.py").write_text("# Init file\n")
    (repo_path / "src" / "main.py").write_text(
        "def main():\n    print('Hello')\n\nif __name__ == '__main__':\n    main()\n"
    )
    (repo_path / "src" / "models.py").write_text(
        "class User:\n    def __init__(self, name):\n        self.name = name\n"
    )
    (repo_path / "src" / "utils.py").write_text(
        "def helper():\n    return 42\n"
    )
    (repo_path / "src" / "config.py").write_text(
        "CONFIG = {'debug': True}\n"
    )
    
    # Create test files
    (repo_path / "tests" / "test_main.py").write_text(
        "def test_main():\n    assert True\n"
    )
    (repo_path / "tests" / "test_models.py").write_text(
        "def test_user():\n    assert True\n"
    )
    
    yield repo_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_analysis(temp_repo):
    """Create a sample RepoAnalysis for testing."""
    return RepoAnalysis(
        root_path=temp_repo,
        project_type="python",
        structure=DirectoryStructure(
            root_path=temp_repo,
            directories=["src", "tests", "config"],
            files=["README.md", "requirements.txt"],
            source_dirs=["src"],
            test_dirs=["tests"],
            config_dirs=["config"],
            ci_dirs=[]
        ),
        dependencies=DependencyInfo(
            manifests=[temp_repo / "requirements.txt"],
            python=["pytest", "pydantic"],
            node=[],
            go=[],
            rust=[],
            java=[]
        ),
        code_metrics=CodeMetrics(
            total_files=7,
            total_lines=50
        ),
        patterns=CodePatterns(
            test_frameworks=["pytest"],
            build_tools=[]
        ),
        config_files=ConfigFiles(files=[]),
        errors=[]
    )


def test_extractor_initialization(temp_repo):
    """Test CodeSampleExtractor initialization."""
    extractor = CodeSampleExtractor(str(temp_repo))
    
    assert extractor.root_path == temp_repo
    assert extractor.max_samples == 10
    assert extractor.max_lines_per_sample == 200
    assert '.py' in extractor.code_extensions
    assert 'node_modules' in extractor.skip_dirs


def test_extract_architecture_samples(temp_repo, sample_analysis):
    """Test extraction of architecture samples."""
    extractor = CodeSampleExtractor(str(temp_repo))
    samples = extractor._extract_architecture_samples(sample_analysis)
    
    # Should find main.py and __init__.py
    assert len(samples) > 0
    file_paths = [s.file_path for s in samples]
    assert any('main.py' in path for path in file_paths)
    
    # Check sample properties
    for sample in samples:
        assert sample.category == "architecture"
        assert sample.content
        assert sample.reason


def test_extract_pattern_samples(temp_repo, sample_analysis):
    """Test extraction of pattern samples."""
    extractor = CodeSampleExtractor(str(temp_repo))
    samples = extractor._extract_pattern_samples(sample_analysis)
    
    # Should find models.py, config.py, utils.py
    assert len(samples) > 0
    file_paths = [s.file_path for s in samples]
    assert any('models.py' in path or 'config.py' in path or 'utils.py' in path 
               for path in file_paths)
    
    for sample in samples:
        assert sample.category == "pattern"


def test_extract_test_samples(temp_repo, sample_analysis):
    """Test extraction of test samples."""
    extractor = CodeSampleExtractor(str(temp_repo))
    samples = extractor._extract_test_samples(sample_analysis)
    
    # Should find test files
    assert len(samples) > 0
    file_paths = [s.file_path for s in samples]
    assert any('test_' in path for path in file_paths)
    
    for sample in samples:
        assert sample.category == "test"
        assert 'test' in sample.file_path.lower()


def test_extract_goal_relevant_samples(temp_repo, sample_analysis):
    """Test extraction of goal-relevant samples."""
    extractor = CodeSampleExtractor(str(temp_repo))
    
    # Goals mentioning "models"
    samples = extractor._extract_goal_relevant_samples(
        sample_analysis,
        "I want to add new user models and authentication"
    )
    
    # Should find models.py
    assert len(samples) > 0
    file_paths = [s.file_path for s in samples]
    assert any('models.py' in path for path in file_paths)
    
    for sample in samples:
        assert sample.category == "relevant"


def test_extract_from_selected_parts_file(temp_repo, sample_analysis):
    """Test extraction from user-selected file."""
    extractor = CodeSampleExtractor(str(temp_repo))
    
    samples = extractor._extract_from_selected_parts(
        sample_analysis,
        ["src/models.py"]
    )
    
    assert len(samples) == 1
    assert samples[0].file_path == "src/models.py"
    assert samples[0].category == "relevant"
    assert "User-selected file" in samples[0].reason


def test_extract_from_selected_parts_directory(temp_repo, sample_analysis):
    """Test extraction from user-selected directory."""
    extractor = CodeSampleExtractor(str(temp_repo))
    
    samples = extractor._extract_from_selected_parts(
        sample_analysis,
        ["src"]
    )
    
    # Should get up to 2 files from src directory
    assert len(samples) > 0
    assert len(samples) <= 2
    
    for sample in samples:
        assert sample.file_path.startswith("src")
        assert sample.category == "relevant"


def test_read_file_sample(temp_repo):
    """Test reading a single file sample."""
    extractor = CodeSampleExtractor(str(temp_repo))
    
    file_path = temp_repo / "src" / "main.py"
    sample = extractor._read_file_sample(
        file_path,
        reason="Test reason",
        category="test"
    )
    
    assert sample is not None
    assert sample.file_path == "src/main.py"
    assert "def main()" in sample.content
    assert sample.reason == "Test reason"
    assert sample.category == "test"
    assert sample.language == "py"
    assert sample.line_count > 0


def test_read_file_sample_truncation(temp_repo):
    """Test that long files are truncated."""
    extractor = CodeSampleExtractor(str(temp_repo), max_lines_per_sample=3)
    
    # Create a long file
    long_file = temp_repo / "src" / "long.py"
    long_file.write_text('\n'.join([f"line {i}" for i in range(100)]))
    
    sample = extractor._read_file_sample(
        long_file,
        reason="Test",
        category="test"
    )
    
    assert sample is not None
    assert "truncated" in sample.content
    assert sample.line_count == 100


def test_extract_keywords_from_goals():
    """Test keyword extraction from goals."""
    extractor = CodeSampleExtractor(".")
    
    goals = "I want to add authentication and user management features"
    keywords = extractor._extract_keywords_from_goals(goals)
    
    assert "authentication" in keywords
    assert "user" in keywords
    assert "management" in keywords
    assert "features" in keywords
    
    # Common words should be filtered
    assert "want" not in keywords
    assert "add" not in keywords
    assert "the" not in keywords


def test_deduplicate_samples():
    """Test sample deduplication."""
    extractor = CodeSampleExtractor(".")
    
    samples = [
        CodeSample("file1.py", "content1", "reason1", "cat1"),
        CodeSample("file2.py", "content2", "reason2", "cat2"),
        CodeSample("file1.py", "content1_dup", "reason1_dup", "cat1"),  # Duplicate
        CodeSample("file3.py", "content3", "reason3", "cat3"),
    ]
    
    unique = extractor._deduplicate_samples(samples)
    
    assert len(unique) == 3
    file_paths = [s.file_path for s in unique]
    assert file_paths.count("file1.py") == 1


def test_extract_samples_integration(temp_repo, sample_analysis):
    """Test full sample extraction workflow."""
    extractor = CodeSampleExtractor(str(temp_repo), max_samples=5)
    
    samples = extractor.extract_samples(
        sample_analysis,
        selected_parts=["src/models.py"],
        goals="Add user authentication"
    )
    
    # Should have samples from different categories
    assert len(samples) > 0
    assert len(samples) <= 5  # Respects max_samples
    
    categories = {s.category for s in samples}
    assert len(categories) > 1  # Multiple categories
    
    # Should include the selected file
    file_paths = [s.file_path for s in samples]
    assert "src/models.py" in file_paths


def test_format_samples_for_prompt(temp_repo, sample_analysis):
    """Test formatting samples for LLM prompts."""
    extractor = CodeSampleExtractor(str(temp_repo))
    
    samples = [
        CodeSample(
            file_path="src/main.py",
            content="def main():\n    pass",
            reason="Entry point",
            category="architecture",
            language="py",
            line_count=2
        ),
        CodeSample(
            file_path="src/models.py",
            content="class User:\n    pass",
            reason="Data model",
            category="pattern",
            language="py",
            line_count=2
        )
    ]
    
    formatted = extractor.format_samples_for_prompt(samples)
    
    assert "Sample 1: src/main.py" in formatted
    assert "Sample 2: src/models.py" in formatted
    assert "Entry point" in formatted
    assert "Data model" in formatted
    assert "```py" in formatted
    assert "def main()" in formatted
    assert "class User" in formatted


def test_format_samples_empty():
    """Test formatting with no samples."""
    extractor = CodeSampleExtractor(".")
    formatted = extractor.format_samples_for_prompt([])
    
    assert "No code samples available" in formatted


def test_extractor_with_nonexistent_directory():
    """Test extractor handles nonexistent directories gracefully."""
    nonexistent_path = Path("/nonexistent/path")
    extractor = CodeSampleExtractor(str(nonexistent_path))
    
    analysis = RepoAnalysis(
        root_path=nonexistent_path,
        project_type="python",
        structure=DirectoryStructure(
            root_path=nonexistent_path,
            directories=[],
            files=[],
            source_dirs=["src"],
            test_dirs=["tests"],
            config_dirs=[],
            ci_dirs=[]
        ),
        dependencies=DependencyInfo(manifests=[], python=[], node=[], go=[], rust=[], java=[]),
        code_metrics=CodeMetrics(0, 0),
        patterns=CodePatterns([], []),
        config_files=ConfigFiles(files=[]),
        errors=[]
    )
    
    # Should not crash
    samples = extractor.extract_samples(analysis)
    assert samples == []
