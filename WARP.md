# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

DevPlan Orchestrator is an LLM-based orchestration tool that generates development plans and handoff prompts by coordinating multiple LLMs in a provider-agnostic way. It uses a multi-phase pipeline: user inputs → project design → basic devplan → detailed devplan → handoff prompt.

## Essential Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Unix/MacOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys
```

### Testing
```bash
# Run all tests
pytest tests/

# Run tests with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest tests/unit/test_config.py

# Run tests matching pattern
pytest -k "test_config"
```

### Code Quality
```bash
# Format code
black src/

# Check style (errors only)
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Check style (full check)
flake8 src/

# Sort imports
isort src/

# Check formatting without making changes
black --check --diff src/

# Check import sorting
isort --check-only --diff src/
```

### CLI Usage
```bash
# Initialize repository
devussy init-repo [PATH]

# Generate project design
devussy generate-design --name "Project" --languages "Python" --requirements "Build an API"

# Generate devplan from design
devussy generate-devplan docs/design.json

# Generate handoff prompt
devussy generate-handoff docs/devplan.json --name "Project"

# Run full pipeline
devussy run-full-pipeline --name "Project" --languages "Python" --requirements "Build an API"
```

## Architecture Overview

### Core Abstraction Pattern

The codebase follows a **factory pattern with provider-agnostic abstractions**:

1. **LLMClient Interface** (`src/llm_client.py`): Abstract base class defining async-first interface for all LLM providers
   - All concrete clients implement `generate_completion()` 
   - Supports streaming via `generate_completion_streaming()`
   - Built-in sync wrappers with proper event loop handling

2. **Client Factory** (`src/clients/factory.py`): Creates concrete LLM clients based on configuration
   - Supported providers: OpenAI, Generic OpenAI-compatible, Requesty
   - Single entry point: `create_llm_client(config)`

3. **Dynamic Provider Switching**: `PipelineOrchestrator.switch_provider()` allows runtime provider changes

### Pipeline Orchestration

The **PipelineOrchestrator** (`src/pipeline/compose.py`) coordinates four sequential stages:

1. **ProjectDesignGenerator** → `ProjectDesign` model
2. **BasicDevPlanGenerator** → Initial `DevPlan` structure
3. **DetailedDevPlanGenerator** → Enriched `DevPlan` (concurrent phase processing)
4. **HandoffPromptGenerator** → `HandoffPrompt` document

Each stage:
- Takes output from previous stage as input
- Uses Jinja2 templates from `templates/` directory
- Supports state checkpoints via `StateManager`
- Optionally commits to Git after completion

### Key Components

**Concurrency Management** (`src/concurrency.py`):
- `ConcurrencyManager` controls concurrent API calls
- Uses `asyncio.Semaphore` for rate limiting
- Configured via `max_concurrent_requests` in config

**Retry Logic** (`src/retry.py`):
- Exponential backoff with configurable parameters
- Integrates with `tenacity` library
- Applied to all LLM API calls

**State Persistence** (`src/state_manager.py`):
- Checkpoint-based resumable workflows
- Saves intermediate pipeline results to `.devussy_state/`
- Enables recovery from interruptions

**Git Integration** (`src/git_manager.py`):
- Automatic commits after each pipeline stage
- Configurable commit messages and behavior
- Checks for repo validity before operations

**Template System** (`src/templates.py`):
- Jinja2-based prompt generation
- Citation embedding via `src/citations.py`
- Templates in `templates/` directory

### Data Models

All models (`src/models.py`) are Pydantic-based with JSON serialization:

- **ProjectDesign**: Project metadata, tech stack, architecture overview, dependencies
- **DevPlan**: Hierarchical phases and steps with status tracking
  - `DevPlanPhase`: Container for related steps
  - `DevPlanStep`: Atomic actionable step with `done` flag
- **HandoffPrompt**: Final document with next steps

### Configuration Hierarchy

Configuration is loaded in order of precedence:
1. CLI arguments (highest)
2. Environment variables (`.env`)
3. Config file (`config/config.yaml`)
4. Built-in defaults (lowest)

Key config sections:
- `llm`: Provider, model, temperature, max_tokens
- `retry`: max_attempts, delays, exponential_base
- `git`: enabled, commit triggers
- `pipeline`: checkpoints, validation, intermediate saves

## Development Practices

### Code Style Requirements

- **Black**: 88 character line length (enforced)
- **Flake8**: PEP 8 compliance with E203/W503 exceptions
- **isort**: Sorted imports
- **Type hints**: Required for all function parameters and return values
- **Docstrings**: Google-style docstrings for all public functions/classes

### Testing Standards

- Tests in `tests/unit/` (117+ tests, >80% coverage)
- Use pytest fixtures for reusable test data
- Mock external dependencies (LLM APIs, Git, file I/O)
- Run `pytest-asyncio` for async tests
- Coverage threshold: 80% minimum (configured in `pytest.ini`)

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:
- Black formatting
- Flake8 linting  
- isort import sorting

Install: `pre-commit install`

### Commit Message Format

Follow Conventional Commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/corrections
- `refactor:` Code changes without feature/fix
- `chore:` Build/tooling changes

### Adding New LLM Providers

1. Create new client in `src/clients/` implementing `LLMClient`
2. Add provider configuration to `LLMConfig` in `src/config.py`
3. Update factory in `src/clients/factory.py`
4. Add comprehensive tests in `tests/unit/test_llm_clients.py`
5. Document in `docs/PROVIDERS.md`

## Important Constraints

- **Async-first**: All LLM operations use `async/await`
- **No nested event loops**: Use async methods inside async contexts
- **Provider independence**: Never hardcode provider-specific logic outside `clients/`
- **Git safety**: Git operations gracefully degrade if not in a repo
- **API keys**: Never commit secrets; use `.env` file (excluded via `.gitignore`)

## Windows-Specific Notes

- Virtual environment activation: `venv\Scripts\activate`
- PowerShell execution policy may need adjustment: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Use forward slashes or raw strings in Path objects to avoid escaping issues
