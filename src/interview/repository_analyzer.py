from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union
import xml.etree.ElementTree as ET

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


@dataclass
class DirectoryStructure:
    root_path: Path
    directories: List[str]
    files: List[str]
    source_dirs: List[str]
    test_dirs: List[str]
    config_dirs: List[str]
    ci_dirs: List[str]


@dataclass
class DependencyInfo:
    manifests: List[Path]
    python: List[str] = field(default_factory=list)
    node: List[str] = field(default_factory=list)
    go: List[str] = field(default_factory=list)
    rust: List[str] = field(default_factory=list)
    java: List[str] = field(default_factory=list)


@dataclass
class CodeMetrics:
    total_files: int
    total_lines: int


@dataclass
class CodePatterns:
    test_frameworks: List[str]
    build_tools: List[str]


@dataclass
class ConfigFiles:
    files: List[Path]


@dataclass
class ProjectMetadata:
    """Project metadata extracted from manifest files."""
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None


@dataclass
class RepoAnalysis:
    root_path: Path
    project_type: str
    structure: DirectoryStructure
    dependencies: DependencyInfo
    code_metrics: CodeMetrics
    patterns: CodePatterns
    config_files: ConfigFiles
    project_metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    errors: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> dict:
        """Create a trimmed JSON-friendly representation for LLM prompts.
        
        Returns a concise dict with key repo information suitable for
        injection into devplan/handoff generation prompts.
        """
        # Get notable dependencies (limit to top 10 per ecosystem)
        notable_deps = {}
        if self.dependencies.python:
            notable_deps["python"] = self.dependencies.python[:10]
        if self.dependencies.node:
            notable_deps["node"] = self.dependencies.node[:10]
        if self.dependencies.go:
            notable_deps["go"] = self.dependencies.go[:10]
        if self.dependencies.rust:
            notable_deps["rust"] = self.dependencies.rust[:10]
        if self.dependencies.java:
            notable_deps["java"] = self.dependencies.java[:10]
        
        context = {
            "project_type": self.project_type,
            "structure": {
                "source_dirs": self.structure.source_dirs,
                "test_dirs": self.structure.test_dirs,
                "config_dirs": self.structure.config_dirs,
                "has_ci": len(self.structure.ci_dirs) > 0,
            },
            "dependencies": notable_deps,
            "metrics": {
                "total_files": self.code_metrics.total_files,
                "total_lines": self.code_metrics.total_lines,
            },
            "patterns": {
                "test_frameworks": self.patterns.test_frameworks,
                "build_tools": self.patterns.build_tools,
            },
        }
        
        # Add project metadata if available
        if self.project_metadata.name:
            context["project_name"] = self.project_metadata.name
        if self.project_metadata.description:
            context["description"] = self.project_metadata.description
        if self.project_metadata.version:
            context["version"] = self.project_metadata.version
        if self.project_metadata.author:
            context["author"] = self.project_metadata.author
        
        return context


class RepositoryAnalyzer:
    def __init__(self, root_path: Union[Path, str]) -> None:
        self.root_path = Path(root_path).resolve()

    def analyze(self) -> RepoAnalysis:
        project_type = self._detect_project_type()
        structure = self._analyze_structure()
        dependencies = self._detect_dependency_manifests()
        code_metrics = self._compute_code_metrics(structure)
        patterns = self._detect_patterns(dependencies)
        config_files = self._collect_config_files()
        project_metadata = self._extract_project_metadata()
        errors: List[str] = []

        return RepoAnalysis(
            root_path=self.root_path,
            project_type=project_type,
            structure=structure,
            dependencies=dependencies,
            code_metrics=code_metrics,
            patterns=patterns,
            config_files=config_files,
            project_metadata=project_metadata,
            errors=errors,
        )

    def _detect_project_type(self) -> str:
        markers = {
            "node": ["package.json"],
            "python": ["pyproject.toml", "requirements.txt"],
            "go": ["go.mod"],
            "rust": ["Cargo.toml"],
            "java": ["pom.xml"],
        }

        for project_type, files in markers.items():
            if any((self.root_path / name).exists() for name in files):
                return project_type

        return "unknown"

    def _analyze_structure(self) -> DirectoryStructure:
        directories: List[str] = []
        files: List[str] = []
        source_dirs: List[str] = []
        test_dirs: List[str] = []
        config_dirs: List[str] = []
        ci_dirs: List[str] = []

        for path in self.root_path.iterdir():
            if path.is_dir():
                name = path.name
                directories.append(name)
                lower = name.lower()
                if lower in {"src", "source"}:
                    source_dirs.append(name)
                if lower in {"test", "tests"}:
                    test_dirs.append(name)
                if lower in {"config", "configs", "settings"}:
                    config_dirs.append(name)
                if lower in {".github", ".gitlab", ".circleci"}:
                    ci_dirs.append(name)
            elif path.is_file():
                files.append(path.name)

        return DirectoryStructure(
            root_path=self.root_path,
            directories=sorted(directories),
            files=sorted(files),
            source_dirs=sorted(source_dirs),
            test_dirs=sorted(test_dirs),
            config_dirs=sorted(config_dirs),
            ci_dirs=sorted(ci_dirs),
        )

    def _detect_dependency_manifests(self) -> DependencyInfo:
        manifest_names = [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
        ]
        manifests: List[Path] = []
        python_deps: List[str] = []
        node_deps: List[str] = []
        go_deps: List[str] = []
        rust_deps: List[str] = []
        java_deps: List[str] = []

        for name in manifest_names:
            candidate = self.root_path / name
            if not candidate.exists():
                continue
            manifests.append(candidate)
            if name == "requirements.txt":
                python_deps.extend(self._parse_requirements_txt(candidate))
            elif name == "pyproject.toml":
                python_deps.extend(self._parse_pyproject_toml(candidate))
            elif name == "package.json":
                node_deps.extend(self._parse_package_json(candidate))
            elif name == "go.mod":
                go_deps.extend(self._parse_go_mod(candidate))
            elif name == "Cargo.toml":
                rust_deps.extend(self._parse_cargo_toml(candidate))
            elif name == "pom.xml":
                java_deps.extend(self._parse_pom_xml(candidate))

        return DependencyInfo(
            manifests=manifests,
            python=sorted(set(python_deps)),
            node=sorted(set(node_deps)),
            go=sorted(set(go_deps)),
            rust=sorted(set(rust_deps)),
            java=sorted(set(java_deps)),
        )

    def _compute_code_metrics(self, structure: DirectoryStructure) -> CodeMetrics:
        total_files = 0
        total_lines = 0
        
        # Skip problematic directories
        skip_dirs = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'node_modules', '.venv', 'venv', '.mypy_cache', 'build', 'dist'
        }
        
        # File extensions to analyze (text files only)
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala', '.clj',
            '.html', '.css', '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.conf', '.sh', '.bash', '.zsh', '.fish',
            '.md', '.rst', '.txt', '.sql', '.r', '.m', '.pl', '.lua', '.vim'
        }
        
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Skip problematic subdirectories
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            
            for filename in filenames:
                total_files += 1
                
                # Skip binary files and files without code extensions
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() not in code_extensions:
                    continue
                
                # Skip very large files (>10MB) to prevent hangs
                try:
                    if file_path.stat().st_size > 10 * 1024 * 1024:
                        continue
                except OSError:
                    continue
                
                # Count lines efficiently
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = 0
                        # Read file in chunks to handle large files efficiently
                        for _ in f:
                            line_count += 1
                            # Early exit for very large files (safety check)
                            if line_count > 100000:
                                break
                        total_lines += line_count
                except (OSError, UnicodeDecodeError):
                    continue

        return CodeMetrics(total_files=total_files, total_lines=total_lines)

    def _detect_patterns(self, dependencies: DependencyInfo) -> CodePatterns:
        test_frameworks: List[str] = []
        build_tools: List[str] = []
        python_deps = {name.lower() for name in dependencies.python}
        node_deps = {name.lower() for name in dependencies.node}
        go_deps = {name.lower() for name in dependencies.go}
        rust_deps = {name.lower() for name in dependencies.rust}
        java_deps = {name.lower() for name in dependencies.java}

        if "pytest" in python_deps:
            test_frameworks.append("pytest")
        if "unittest" in python_deps and "unittest" not in test_frameworks:
            test_frameworks.append("unittest")

        if "jest" in node_deps:
            test_frameworks.append("jest")
        if "mocha" in node_deps and "mocha" not in test_frameworks:
            test_frameworks.append("mocha")

        for name in ("webpack", "rollup", "vite", "gulp", "grunt"):
            if name in node_deps and name not in build_tools:
                build_tools.append(name)

        for name in ("setuptools", "poetry", "tox", "nox"):
            if name in python_deps and name not in build_tools:
                build_tools.append(name)

        if any("testify" in dep for dep in go_deps) and "testify" not in test_frameworks:
            test_frameworks.append("testify")

        if any("rstest" in dep for dep in rust_deps) and "rstest" not in test_frameworks:
            test_frameworks.append("rstest")
        if any("proptest" in dep for dep in rust_deps) and "proptest" not in test_frameworks:
            test_frameworks.append("proptest")

        if any("junit" in dep for dep in java_deps) and "junit" not in test_frameworks:
            test_frameworks.append("junit")

        manifest_names = {manifest.name for manifest in dependencies.manifests}
        if "go.mod" in manifest_names and "go" not in build_tools:
            build_tools.append("go")
        if "Cargo.toml" in manifest_names and "cargo" not in build_tools:
            build_tools.append("cargo")
        if "pom.xml" in manifest_names and "maven" not in build_tools:
            build_tools.append("maven")

        if not test_frameworks:
            for manifest in dependencies.manifests:
                manifest_name = manifest.name
                if manifest_name == "package.json" and "jest" not in test_frameworks:
                    test_frameworks.append("jest")
                if manifest_name in {"pyproject.toml", "requirements.txt"} and "pytest" not in test_frameworks:
                    test_frameworks.append("pytest")

        return CodePatterns(test_frameworks=test_frameworks, build_tools=build_tools)

    def _parse_go_mod(self, path: Path) -> List[str]:
        dependencies: List[str] = []
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return dependencies

        in_require_block = False
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            if stripped.startswith("require ("):
                in_require_block = True
                continue
            if in_require_block:
                if stripped.startswith(")"):
                    in_require_block = False
                    continue
                parts = stripped.split()
                if parts:
                    dependencies.append(parts[0])
                continue
            if stripped.startswith("require "):
                parts = stripped.split()
                if len(parts) >= 2:
                    dependencies.append(parts[1])
        return dependencies

    def _parse_cargo_toml(self, path: Path) -> List[str]:
        if tomllib is None:
            return []
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return []

        dependencies: List[str] = []
        for key in ("dependencies", "dev-dependencies", "build-dependencies"):
            section = data.get(key) or {}
            if isinstance(section, dict):
                for name in section.keys():
                    normalized = self._normalize_dependency_name(str(name))
                    if normalized:
                        dependencies.append(normalized)
        return dependencies

    def _parse_pom_xml(self, path: Path) -> List[str]:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except (OSError, ET.ParseError):
            return []

        namespace_prefix = ""
        if root.tag.startswith("{"):
            namespace_prefix = root.tag.split("}", 1)[0] + "}"

        dependencies: List[str] = []
        for dep in root.findall(f".//{namespace_prefix}dependency"):
            group_id_element = dep.find(f"{namespace_prefix}groupId")
            artifact_id_element = dep.find(f"{namespace_prefix}artifactId")
            group = (group_id_element.text or "").strip() if group_id_element is not None else ""
            artifact = (artifact_id_element.text or "").strip() if artifact_id_element is not None else ""
            if not group and not artifact:
                continue
            name = ":".join(part for part in (group, artifact) if part)
            normalized = self._normalize_dependency_name(name)
            if normalized:
                dependencies.append(normalized)
        return dependencies

    def _parse_requirements_txt(self, path: Path) -> List[str]:
        dependencies: List[str] = []
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return dependencies

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = self._normalize_dependency_name(line)
            if name:
                dependencies.append(name)
        return dependencies

    def _parse_pyproject_toml(self, path: Path) -> List[str]:
        if tomllib is None:
            return []
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return []

        dependencies: List[str] = []
        project_section = data.get("project") or {}
        for item in project_section.get("dependencies", []):
            name = self._normalize_dependency_name(str(item))
            if name:
                dependencies.append(name)

        optional = project_section.get("optional-dependencies") or {}
        for items in optional.values():
            for item in items:
                name = self._normalize_dependency_name(str(item))
                if name:
                    dependencies.append(name)
        return dependencies

    def _parse_package_json(self, path: Path) -> List[str]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        dependencies: List[str] = []
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            section = data.get(key) or {}
            if isinstance(section, dict):
                for name in section.keys():
                    normalized = self._normalize_dependency_name(str(name))
                    if normalized:
                        dependencies.append(normalized)
        return dependencies

    def _normalize_dependency_name(self, raw: str) -> str:
        raw = raw.strip()
        if not raw:
            return ""
        for separator in (";", "["):
            if separator in raw:
                raw = raw.split(separator, 1)[0]
        for separator in ("<", ">", "=", "~", "!"):
            if separator in raw:
                raw = raw.split(separator, 1)[0]
        if " " in raw:
            raw = raw.split(" ", 1)[0]
        return raw.strip()

    def _collect_config_files(self) -> ConfigFiles:
        names = [
            "pyproject.toml",
            "setup.cfg",
            "tox.ini",
            "pytest.ini",
            "package.json",
            "tsconfig.json",
            ".github/workflows",
        ]
        found: List[Path] = []

        for name in names:
            candidate = self.root_path / name
            if candidate.exists():
                found.append(candidate)

        return ConfigFiles(files=found)

    def _extract_project_metadata(self) -> ProjectMetadata:
        """Extract project metadata from manifest files."""
        metadata = ProjectMetadata()
        
        # Try pyproject.toml first (Python projects)
        pyproject_path = self.root_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with pyproject_path.open("rb") as f:
                    if tomllib is not None:
                        data = tomllib.load(f)
                    else:
                        return metadata  # Can't parse TOML
                
                # Extract from [project] section
                project = data.get("project", {})
                if isinstance(project, dict):
                    metadata.name = project.get("name")
                    metadata.version = project.get("version")
                    metadata.description = project.get("description")
                    
                    # Extract author from authors list
                    authors = project.get("authors", [])
                    if authors and isinstance(authors, list) and authors[0]:
                        author_info = authors[0]
                        if isinstance(author_info, dict):
                            metadata.author = author_info.get("name")
                    
                    # Extract homepage from URLs
                    urls = project.get("urls", {})
                    if isinstance(urls, dict):
                        metadata.homepage = urls.get("Homepage")
                
            except Exception:  # Catch any parsing errors
                pass
        
        # Try package.json (Node.js projects)
        package_path = self.root_path / "package.json"
        if package_path.exists():
            try:
                data = json.loads(package_path.read_text(encoding="utf-8"))
                if not metadata.name:  # Only set if not already set
                    metadata.name = data.get("name")
                if not metadata.version:
                    metadata.version = data.get("version")
                if not metadata.description:
                    metadata.description = data.get("description")
                if not metadata.author:
                    author = data.get("author")
                    if isinstance(author, str):
                        metadata.author = author
                    elif isinstance(author, dict):
                        metadata.author = author.get("name")
                if not metadata.homepage:
                    metadata.homepage = data.get("homepage")
            except (OSError, json.JSONDecodeError):
                pass
        
        # Try go.mod (Go projects)
        gomod_path = self.root_path / "go.mod"
        if gomod_path.exists() and not metadata.name:
            try:
                content = gomod_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("module "):
                        parts = line.split()
                        if len(parts) >= 2:
                            # Extract module name from path
                            module_path = parts[1]
                            # Remove version suffix if present
                            if " =>" in module_path:
                                module_path = module_path.split(" =>")[0]
                            metadata.name = module_path.split("/")[-1]  # Get last part
                            break
            except OSError:
                pass
        
        # Try Cargo.toml (Rust projects)
        cargo_path = self.root_path / "Cargo.toml"
        if cargo_path.exists() and not metadata.name:
            try:
                with cargo_path.open("rb") as f:
                    if tomllib is not None:
                        data = tomllib.load(f)
                        # Try [package] section first
                        package = data.get("package")
                        if isinstance(package, dict):
                            metadata.name = package.get("name")
                            metadata.version = package.get("version")
                            metadata.description = package.get("description")
                        
                        # Try root level for simpler Cargo.toml
                        if not metadata.name:
                            metadata.name = data.get("name")
                            metadata.version = data.get("version")
                            metadata.description = data.get("description")
            except Exception:  # Catch any parsing errors
                pass
        
        return metadata
