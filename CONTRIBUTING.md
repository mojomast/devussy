# Contributing to DevPlan Orchestrator

Thank you for your interest in contributing to DevPlan Orchestrator! This document provides guidelines for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A GitHub account

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/devussy.git
   cd devussy
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/mojomast/devussy.git
   ```

## Development Environment

### Setting Up Your Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

### Verify Installation

Run the test suite to ensure everything is working:
```bash
pytest tests/
```

Run code quality checks:
```bash
black src/
flake8 src/
isort src/
```

## Code Style and Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with the following tools:

- **Black**: Code formatting (88 character line length)
- **Flake8**: Style and error checking
- **isort**: Import sorting

### Configuration

The project uses these configuration files:
- `.flake8`: Flake8 configuration
- `pyproject.toml`: Black and isort configuration (when created)

### Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before commits:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

### Code Quality Standards

- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Follow Google-style docstrings for all public functions and classes
- **Error Handling**: Implement proper error handling with meaningful error messages
- **Logging**: Use the configured logging system instead of print statements

### Example Code Style

```python
"""Module docstring describing the module purpose."""

import asyncio
from typing import Any, Dict, List, Optional

from src.config import AppConfig


class ExampleClass:
    """Example class following project conventions.
    
    Args:
        config: Application configuration object
        timeout: Optional timeout in seconds
    """

    def __init__(self, config: AppConfig, timeout: Optional[int] = None) -> None:
        self._config = config
        self._timeout = timeout or 30

    async def process_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process input data and return results.
        
        Args:
            data: List of data dictionaries to process
            
        Returns:
            Dictionary containing processed results
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
            
        # Implementation here
        return {"processed_count": len(data)}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_config.py

# Run tests matching pattern
pytest -k "test_config"
```

### Writing Tests

- **Location**: Tests go in `tests/unit/` or `tests/integration/`
- **Naming**: Test files should be named `test_<module_name>.py`
- **Structure**: Use pytest fixtures for reusable test data
- **Coverage**: Aim for >80% code coverage for new code
- **Isolation**: Use temporary directories and mocking for external dependencies

### Test Example

```python
"""Tests for example_module functionality."""

import pytest
from unittest.mock import Mock

from src.example_module import ExampleClass


class TestExampleClass:
    """Tests for ExampleClass."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return Mock(timeout=30, max_retries=3)

    def test_init(self, mock_config):
        """Test ExampleClass initialization."""
        instance = ExampleClass(mock_config)
        assert instance._config == mock_config

    @pytest.mark.asyncio
    async def test_process_data_success(self, mock_config):
        """Test successful data processing."""
        instance = ExampleClass(mock_config)
        data = [{"key": "value"}]
        
        result = await instance.process_data(data)
        
        assert result["processed_count"] == 1

    def test_process_data_empty_raises_error(self, mock_config):
        """Test that empty data raises ValueError."""
        instance = ExampleClass(mock_config)
        
        with pytest.raises(ValueError, match="Data cannot be empty"):
            instance.process_data([])
```

## Submitting Changes

### Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Write tests** for new functionality

4. **Run the test suite** to ensure nothing is broken:
   ```bash
   pytest tests/
   ```

5. **Run code quality checks**:
   ```bash
   black src/
   flake8 src/
   isort src/
   ```

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request** on GitHub

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat: add support for new LLM provider
fix: resolve configuration loading issue
docs: update API documentation
test: add unit tests for retry logic
```

### Pull Request Guidelines

- **Title**: Use a clear, descriptive title
- **Description**: Explain what changes you made and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update documentation if needed
- **Breaking Changes**: Clearly document any breaking changes

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Test improvement

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Code coverage maintained

## Documentation
- [ ] Documentation updated
- [ ] Code comments added where necessary

## Breaking Changes
List any breaking changes (if applicable)
```

## Reporting Issues

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Check the documentation** to see if it's a known limitation
3. **Test with the latest version** to see if the issue still exists

### Issue Template

When reporting bugs, please include:

- **DevPlan Orchestrator version**
- **Python version** 
- **Operating system**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Error messages/logs**
- **Configuration** (remove sensitive information)

### Example Bug Report

```markdown
## Bug Description
Configuration loading fails when YAML contains special characters

## Environment
- DevPlan Orchestrator version: 0.1.0
- Python version: 3.9.0
- OS: Windows 11

## Steps to Reproduce
1. Create config.yaml with special characters in project name
2. Run `devussy generate-design --config config.yaml`
3. Error occurs during configuration loading

## Expected Behavior
Configuration should load successfully with special characters

## Actual Behavior
ValueError: Invalid YAML configuration

## Error Log
```
[Include relevant error messages]
```

## Configuration
```yaml
# Sanitized configuration that reproduces the issue
```
```

## Feature Requests

### Guidelines

- **Use Case**: Clearly describe the use case for the feature
- **Benefit**: Explain how it would benefit users
- **Implementation**: Suggest how it might be implemented (optional)
- **Examples**: Provide examples of how it would be used

### Feature Request Template

```markdown
## Feature Description
Clear description of the requested feature

## Use Case
Specific use case that would benefit from this feature

## Proposed Solution
How you envision this feature working

## Alternatives Considered
Other ways this problem could be solved

## Additional Context
Any other relevant information
```

## Development Guidelines

### Architecture Decisions

- Follow the existing architecture patterns
- Maintain separation of concerns
- Use dependency injection where appropriate
- Keep modules loosely coupled

### Adding New Features

1. **Design First**: Consider how the feature fits into the existing architecture
2. **Configuration**: Add configuration options if needed
3. **Tests**: Write comprehensive tests
4. **Documentation**: Update relevant documentation
5. **Examples**: Add usage examples

### Adding New LLM Providers

1. Implement the `LLMClient` interface
2. Add provider configuration to `LLMConfig`
3. Update the client factory
4. Add comprehensive tests
5. Update documentation

### Performance Considerations

- Use async/await for I/O operations
- Implement proper concurrency controls
- Consider caching for expensive operations
- Profile performance-critical code

### Security Guidelines

- Never commit API keys or secrets
- Validate all user inputs
- Use secure HTTP connections
- Follow security best practices

## Communication

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing documentation first

### Code Review Process

- All changes require review before merging
- Address review comments promptly
- Be open to feedback and suggestions
- Maintain a collaborative attitude

### Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help other contributors when possible
- Follow the project's code of conduct

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in appropriate files
- [ ] Release notes prepared

## Thank You!

Thank you for contributing to DevPlan Orchestrator! Your contributions help make this project better for everyone.