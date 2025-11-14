# Tech Stack

## Language & Runtime

- **Python 3.9+** (primary language)
- Async/await patterns with asyncio and aiohttp

## Core Dependencies

- **LLM Integration**: openai>=1.58.0, aiohttp>=3.11.0
- **Data Models**: pydantic>=2.10.0 (strict validation)
- **Templating**: jinja2>=3.1.0 (for prompt generation)
- **CLI**: typer>=0.12.0, rich>=13.0.0, prompt_toolkit>=3.0.0
- **Configuration**: python-dotenv>=1.0.0, pyyaml>=6.0.0
- **Git Integration**: gitpython>=3.1.0
- **Retry Logic**: tenacity>=8.2.0

## Development Tools

- **Testing**: pytest>=7.4.0, pytest-asyncio>=0.21.0, pytest-cov>=4.1.0
- **Code Quality**: black (formatting), flake8 (linting), isort (import sorting)
- **Documentation**: pdoc>=14.1.0

## Build System

- **Package Manager**: setuptools>=68.0 with pyproject.toml
- **Entry Point**: `devussy` CLI command via project.scripts

## Common Commands

```bash
# Installation (editable)
pip install -e .

# Run CLI
python -m src.cli <command>
python -m src.entry  # Interactive interview mode

# Testing
pytest -q                    # Quick test run
pytest --cov=src            # With coverage
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only

# Code Quality
black src && isort src && flake8 src

# Documentation
pdoc src --output-dir docs/api
```

## Configuration

- **Config file**: config/config.yaml (YAML format)
- **Environment**: .env file with provider API keys
- **State persistence**: .devussy_state/ directory
- **Output**: docs/ directory for generated artifacts

## Code Style

- **Line length**: 88 characters (black default)
- **Import order**: isort with black profile
- **Flake8**: Extends ignore E203, W503
- **Type hints**: Encouraged but not strictly enforced
- **Docstrings**: Google-style preferred
