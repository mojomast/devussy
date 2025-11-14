import json
import os
from pathlib import Path

from src.interview.repository_analyzer import RepoAnalysis, RepositoryAnalyzer


def test_detects_python_project_type(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[build-system]\nrequires = ['setuptools']\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert isinstance(analysis, RepoAnalysis)
    assert analysis.project_type == "python"


def test_detects_node_project_type(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert analysis.project_type == "node"


def test_structure_lists_top_level_dirs_and_files(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (tmp_path / "README.md").write_text("# Test\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert "src" in analysis.structure.directories
    assert "README.md" in analysis.structure.files


def test_dependency_manifests_detected(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("pytest==7.0.0\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    manifest_names = {p.name for p in analysis.dependencies.manifests}
    assert "requirements.txt" in manifest_names


def test_code_metrics_counts_files(tmp_path: Path) -> None:
    file_path = tmp_path / "file.py"
    file_path.write_text("line1\nline2\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert analysis.code_metrics.total_files >= 1
    assert analysis.code_metrics.total_lines >= 2


def test_patterns_infer_basic_test_frameworks(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("pytest==7.0.0\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert "pytest" in analysis.patterns.test_frameworks


def test_collects_basic_config_files(tmp_path: Path) -> None:
    (tmp_path / "pytest.ini").write_text("[pytest]\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    config_names = {p.name for p in analysis.config_files.files}
    assert "pytest.ini" in config_names


def test_handles_unknown_project_type(tmp_path: Path) -> None:
    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert analysis.project_type == "unknown"


def test_dependency_info_parses_python_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("pytest==7.0.0\nrequests>=2.0\n")

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert "pytest" in analysis.dependencies.python
    assert "requests" in analysis.dependencies.python


def test_dependency_info_parses_node_package_json(tmp_path: Path) -> None:
    package_json = {
        "dependencies": {"react": "^18.0.0"},
        "devDependencies": {"jest": "^29.0.0"},
    }
    (tmp_path / "package.json").write_text(json.dumps(package_json))

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    assert "react" in analysis.dependencies.node
    assert "jest" in analysis.dependencies.node
    assert "jest" in analysis.patterns.test_frameworks


def test_directory_structure_classifies_common_folders(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / ".github").mkdir()

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    structure = analysis.structure
    assert "src" in structure.source_dirs
    assert "tests" in structure.test_dirs
    assert "config" in structure.config_dirs
    assert ".github" in structure.ci_dirs


def test_dependency_info_parses_go_mod(tmp_path: Path) -> None:
    go_mod_content = """module example.com/demo

go 1.21

require (
    github.com/stretchr/testify v1.8.4
    golang.org/x/tools v0.15.0
)
"""
    (tmp_path / "go.mod").write_text(go_mod_content)

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    go_deps = analysis.dependencies.go
    assert "github.com/stretchr/testify" in go_deps
    assert "golang.org/x/tools" in go_deps
    assert "testify" in analysis.patterns.test_frameworks
    assert "go" in analysis.patterns.build_tools


def test_dependency_info_parses_rust_cargo_toml(tmp_path: Path) -> None:
    cargo_toml_content = """[package]
name = "demo"
version = "0.1.0"

[dependencies]
rstest = "0.18"
proptest = "1.0"
"""
    (tmp_path / "Cargo.toml").write_text(cargo_toml_content)

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    rust_deps = analysis.dependencies.rust
    assert "rstest" in rust_deps
    assert "proptest" in rust_deps
    patterns = analysis.patterns
    assert "rstest" in patterns.test_frameworks
    assert "proptest" in patterns.test_frameworks
    assert "cargo" in patterns.build_tools


def test_dependency_info_parses_java_pom_xml(tmp_path: Path) -> None:
    pom_xml_content = """<project xmlns=\"http://maven.apache.org/POM/4.0.0\">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>demo</artifactId>
  <version>1.0-SNAPSHOT</version>
  <dependencies>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13.2</version>
    </dependency>
  </dependencies>
</project>
"""
    (tmp_path / "pom.xml").write_text(pom_xml_content)

    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()

    java_deps = analysis.dependencies.java
    assert any("junit" in dep for dep in java_deps)
    patterns = analysis.patterns
    assert "junit" in patterns.test_frameworks
    assert "maven" in patterns.build_tools


def test_repo_analysis_to_prompt_context(tmp_path):
    """Test that RepoAnalysis.to_prompt_context() produces a clean JSON-friendly dict."""
    # Create a Python project with dependencies
    (tmp_path / "requirements.txt").write_text("pytest>=7.0\nrequests>=2.28\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github").mkdir()
    
    analyzer = RepositoryAnalyzer(tmp_path)
    analysis = analyzer.analyze()
    
    # Get prompt context
    context = analysis.to_prompt_context()
    
    # Verify structure
    assert isinstance(context, dict)
    assert context["project_type"] == "python"
    assert "structure" in context
    assert "dependencies" in context
    assert "metrics" in context
    assert "patterns" in context
    
    # Verify structure details
    assert "src" in context["structure"]["source_dirs"]
    assert "tests" in context["structure"]["test_dirs"]
    assert context["structure"]["has_ci"] is True
    
    # Verify dependencies are limited and present
    assert "python" in context["dependencies"]
    assert "pytest" in context["dependencies"]["python"]
    assert "requests" in context["dependencies"]["python"]
    assert len(context["dependencies"]["python"]) <= 10  # Should be capped
    
    # Verify metrics
    assert context["metrics"]["total_files"] > 0
    assert context["metrics"]["total_lines"] >= 0
    
    # Verify patterns
    assert "pytest" in context["patterns"]["test_frameworks"]
