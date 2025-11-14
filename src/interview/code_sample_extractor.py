"""
Code sample extraction for enriching interview prompts.

This module extracts relevant code samples from a repository based on:
- Architecture samples (key files showing project structure)
- Pattern examples (representative code showing conventions)
- Relevant files based on user's stated goals
- Representative test files
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from src.interview.repository_analyzer import RepoAnalysis

logger = logging.getLogger(__name__)


@dataclass
class CodeSample:
    """Represents a code sample extracted from the repository."""
    
    file_path: str
    content: str
    reason: str  # Why this sample was selected
    category: str  # 'architecture', 'pattern', 'test', 'relevant'
    language: Optional[str] = None
    line_count: int = 0


class CodeSampleExtractor:
    """Extracts relevant code samples from a repository."""
    
    def __init__(self, root_path: str, max_samples: int = 10, max_lines_per_sample: int = 200):
        """
        Initialize the code sample extractor.
        
        Args:
            root_path: Root directory of the repository
            max_samples: Maximum number of samples to extract
            max_lines_per_sample: Maximum lines to include per sample
        """
        self.root_path = Path(root_path)
        self.max_samples = max_samples
        self.max_lines_per_sample = max_lines_per_sample
        
        # File extensions to consider for code samples
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.clj', '.ex', '.exs'
        }
        
        # Directories to skip
        self.skip_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'env', 'dist', 'build', 'target', '.pytest_cache', '.mypy_cache',
            'coverage', '.coverage', 'htmlcov', '.tox', 'eggs', '.eggs'
        }
    
    def extract_samples(
        self,
        analysis: RepoAnalysis,
        selected_parts: Optional[List[str]] = None,
        goals: Optional[str] = None
    ) -> List[CodeSample]:
        """
        Extract code samples based on repository analysis and user goals.
        
        Args:
            analysis: Repository analysis results
            selected_parts: List of specific parts/directories user wants to focus on
            goals: User's stated development goals
            
        Returns:
            List of extracted code samples
        """
        samples = []
        
        # Extract architecture samples (entry points, main files)
        samples.extend(self._extract_architecture_samples(analysis))
        
        # Extract pattern examples (representative code)
        samples.extend(self._extract_pattern_samples(analysis))
        
        # Extract test samples
        samples.extend(self._extract_test_samples(analysis))
        
        # Extract goal-relevant samples if goals provided
        if goals:
            samples.extend(self._extract_goal_relevant_samples(analysis, goals))
        
        # Extract samples from selected parts if specified
        if selected_parts:
            samples.extend(self._extract_from_selected_parts(analysis, selected_parts))
        
        # Deduplicate and limit samples
        samples = self._deduplicate_samples(samples)
        samples = samples[:self.max_samples]
        
        return samples
    
    def _extract_architecture_samples(self, analysis: RepoAnalysis) -> List[CodeSample]:
        """Extract key architectural files (entry points, main modules)."""
        samples = []
        
        # Common entry point patterns by project type
        entry_patterns = {
            'python': ['__main__.py', 'main.py', 'cli.py', 'app.py', '__init__.py'],
            'node': ['index.js', 'index.ts', 'main.js', 'main.ts', 'app.js', 'app.ts', 'server.js'],
            'go': ['main.go', 'cmd/main.go'],
            'rust': ['main.rs', 'lib.rs'],
            'java': ['Main.java', 'Application.java']
        }
        
        patterns = entry_patterns.get(analysis.project_type, [])
        
        for pattern in patterns:
            for src_dir in analysis.structure.source_dirs:
                src_path = self.root_path / src_dir
                if not src_path.exists():
                    continue
                
                # Search for pattern in source directory
                matches = list(src_path.rglob(pattern))
                for match in matches[:2]:  # Limit to 2 per pattern
                    sample = self._read_file_sample(
                        match,
                        reason=f"Entry point: {pattern}",
                        category="architecture"
                    )
                    if sample:
                        samples.append(sample)
        
        return samples
    
    def _extract_pattern_samples(self, analysis: RepoAnalysis) -> List[CodeSample]:
        """Extract representative code showing common patterns."""
        samples = []
        
        # Look for common pattern files based on project type
        if analysis.project_type == 'python':
            # Look for models, utils, config files
            pattern_files = ['models.py', 'config.py', 'utils.py', 'helpers.py']
        elif analysis.project_type in ['node', 'typescript']:
            pattern_files = ['models.ts', 'config.ts', 'utils.ts', 'helpers.ts',
                           'models.js', 'config.js', 'utils.js', 'helpers.js']
        else:
            pattern_files = []
        
        for pattern in pattern_files:
            for src_dir in analysis.structure.source_dirs:
                src_path = self.root_path / src_dir
                if not src_path.exists():
                    continue
                
                matches = list(src_path.rglob(pattern))
                for match in matches[:1]:  # One per pattern
                    sample = self._read_file_sample(
                        match,
                        reason=f"Common pattern: {pattern}",
                        category="pattern"
                    )
                    if sample:
                        samples.append(sample)
        
        return samples
    
    def _extract_test_samples(self, analysis: RepoAnalysis) -> List[CodeSample]:
        """Extract representative test files."""
        samples = []
        
        for test_dir in analysis.structure.test_dirs:
            test_path = self.root_path / test_dir
            if not test_path.exists():
                continue
            
            # Find test files
            test_files = []
            for ext in self.code_extensions:
                if analysis.project_type == 'python' and ext == '.py':
                    test_files.extend(test_path.rglob('test_*.py'))
                elif analysis.project_type in ['node', 'typescript']:
                    test_files.extend(test_path.rglob(f'*.test{ext}'))
                    test_files.extend(test_path.rglob(f'*.spec{ext}'))
            
            # Take first 2 test files
            for test_file in list(test_files)[:2]:
                sample = self._read_file_sample(
                    test_file,
                    reason="Representative test file",
                    category="test"
                )
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _extract_goal_relevant_samples(self, analysis: RepoAnalysis, goals: str) -> List[CodeSample]:
        """Extract samples relevant to user's stated goals."""
        samples = []
        
        # Simple keyword-based relevance (could be enhanced with embeddings/LLM)
        keywords = self._extract_keywords_from_goals(goals)
        
        if not keywords:
            return samples
        
        # Search for files matching keywords
        for src_dir in analysis.structure.source_dirs:
            src_path = self.root_path / src_dir
            if not src_path.exists():
                continue
            
            for code_file in src_path.rglob('*'):
                if not code_file.is_file():
                    continue
                if code_file.suffix not in self.code_extensions:
                    continue
                if any(skip in code_file.parts for skip in self.skip_dirs):
                    continue
                
                # Check if filename or path contains keywords
                file_str = str(code_file).lower()
                for keyword in keywords:
                    if keyword in file_str:
                        sample = self._read_file_sample(
                            code_file,
                            reason=f"Relevant to goal: {keyword}",
                            category="relevant"
                        )
                        if sample:
                            samples.append(sample)
                            break  # One sample per file
        
        return samples[:3]  # Limit goal-relevant samples
    
    def _extract_from_selected_parts(
        self,
        analysis: RepoAnalysis,
        selected_parts: List[str]
    ) -> List[CodeSample]:
        """Extract samples from user-selected parts of the codebase."""
        samples = []
        
        for part in selected_parts:
            part_path = self.root_path / part
            if not part_path.exists():
                continue
            
            if part_path.is_file():
                # Single file selected
                sample = self._read_file_sample(
                    part_path,
                    reason=f"User-selected file: {part}",
                    category="relevant"
                )
                if sample:
                    samples.append(sample)
            else:
                # Directory selected - get representative files
                code_files = []
                for ext in self.code_extensions:
                    code_files.extend(part_path.rglob(f'*{ext}'))
                
                # Take first 2 files from selected directory
                for code_file in list(code_files)[:2]:
                    if any(skip in code_file.parts for skip in self.skip_dirs):
                        continue
                    
                    sample = self._read_file_sample(
                        code_file,
                        reason=f"From selected part: {part}",
                        category="relevant"
                    )
                    if sample:
                        samples.append(sample)
        
        return samples
    
    def _read_file_sample(
        self,
        file_path: Path,
        reason: str,
        category: str
    ) -> Optional[CodeSample]:
        """Read a file and create a code sample."""
        try:
            # Make path relative to root
            rel_path = file_path.relative_to(self.root_path)
            
            # Read file content
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            # Truncate if too long
            if len(lines) > self.max_lines_per_sample:
                content = '\n'.join(lines[:self.max_lines_per_sample])
                content += f"\n\n... (truncated, {len(lines) - self.max_lines_per_sample} more lines)"
            
            return CodeSample(
                file_path=str(rel_path).replace('\\', '/'),  # Normalize path separators
                content=content,
                reason=reason,
                category=category,
                language=file_path.suffix[1:] if file_path.suffix else None,
                line_count=len(lines)
            )
        
        except Exception as e:
            logger.debug(f"Could not read file {file_path}: {e}")
            return None
    
    def _extract_keywords_from_goals(self, goals: str) -> Set[str]:
        """Extract relevant keywords from user's goals."""
        # Simple keyword extraction (could be enhanced)
        # Remove common words and extract meaningful terms
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'i', 'we',
            'you', 'they', 'it', 'this', 'that', 'these', 'those', 'my', 'our',
            'your', 'their', 'want', 'need', 'add', 'create', 'build', 'make'
        }
        
        words = goals.lower().split()
        keywords = {
            word.strip('.,!?;:')
            for word in words
            if len(word) > 3 and word.lower() not in common_words
        }
        
        return keywords
    
    def _deduplicate_samples(self, samples: List[CodeSample]) -> List[CodeSample]:
        """Remove duplicate samples based on file path."""
        seen_paths = set()
        unique_samples = []
        
        for sample in samples:
            if sample.file_path not in seen_paths:
                seen_paths.add(sample.file_path)
                unique_samples.append(sample)
        
        return unique_samples
    
    def format_samples_for_prompt(self, samples: List[CodeSample]) -> str:
        """Format code samples for inclusion in LLM prompts."""
        if not samples:
            return "No code samples available."
        
        formatted = []
        for i, sample in enumerate(samples, 1):
            formatted.append(f"### Sample {i}: {sample.file_path}")
            formatted.append(f"**Reason**: {sample.reason}")
            formatted.append(f"**Category**: {sample.category}")
            if sample.language:
                formatted.append(f"**Language**: {sample.language}")
            formatted.append(f"**Lines**: {sample.line_count}")
            formatted.append(f"\n```{sample.language or ''}")
            formatted.append(sample.content)
            formatted.append("```\n")
        
        return '\n'.join(formatted)
