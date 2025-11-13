# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview
Devussy is an LLM orchestration tool that transforms project ideas into complete, actionable development plans through a multi-stage pipeline: Design → Basic DevPlan → Detailed DevPlan (per-phase files) → Handoff.

**Core Capabilities:**
- Multi-provider LLM support (OpenAI, Generic OpenAI-compatible, Requesty, Aether AI, AgentRouter)
- Async concurrent phase generation for performance
- Resumable workflows via checkpoint system
- Interactive LLM-driven interview mode for design gathering
- Rich terminal UX with live spinners, progress bars, and persistent status lines

## Common Commands

### Development & Testing
```powershell
# Run all tests with coverage
pytest -q

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest -m unit
pytest -m integration

# Run tests with coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html

# Lint and format code
black src
isort src
flake8 src

# Or run all quality checks together
black src && isort src && flake8 src
```

### Running Devussy

```powershell
# Interactive interview mode (recommended)
python -m src.entry

# Or use the CLI
python -m src.cli interactive-design

# Full non-interactive pipeline
python -m src.cli run-full-pipeline `
  --name "My Project" `
  --languages "Python,TypeScript" `
  --requirements "Build a REST API" `
  --frameworks "FastAPI,React"

# Generate only design
python -m src.cli generate-design `
  --name "My App" `
  --languages "Python" `
  --requirements "Build an API"

# Initialize a new project repo with docs/ structure
python -m src.cli init-repo ./my-project

# Check version
python -m src.cli version
```

### Checkpoint Management
```powershell
# List all checkpoints
python -m src.cli list-checkpoints

# Resume from checkpoint
python -m src.cli run-full-pipeline --resume-from "myproject_pipeline"

# Delete specific checkpoint
python -m src.cli delete-checkpoint <key>

# Clean up old checkpoints (keep latest 5)
python -m src.cli cleanup-checkpoints --keep 5
```

### Pre-commit Hooks
```powershell
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run pre-commit on all files manually
pre-commit run --all-files
```

## Architecture

### Pipeline Stages
The orchestration pipeline (`src/pipeline/compose.py`) coordinates four main stages:

1. **Project Design** (`src/pipeline/project_design.py`)
   - Generates structured design from user inputs (name, languages, requirements, frameworks, APIs)
   - Produces `docs/project_design.md`
   - Uses `templates/project_design.jinja` prompt template

2. **Basic DevPlan** (`src/pipeline/basic_devplan.py`)
   - Creates high-level phases from the project design
   - Produces skeleton phase structure without detailed steps
   - Uses `templates/basic_devplan.jinja`

3. **Detailed DevPlan** (`src/pipeline/detailed_devplan.py`)
   - Expands each phase into numbered, actionable steps concurrently
   - Generates per-phase files (`docs/phase1.md`, `docs/phase2.md`, etc.)
   - Uses `ConcurrencyManager` for parallel phase generation
   - Includes fallback prompts if initial generation fails
   - Uses `templates/detailed_devplan.jinja`

4. **Handoff Prompt** (`src/pipeline/handoff_prompt.py`)
   - Synthesizes all previous stages into a navigation document
   - Produces `docs/handoff_prompt.md`
   - Uses `templates/handoff_prompt.jinja`

### Stage-Specific LLM Clients
The `PipelineOrchestrator` can use different LLM models/providers for each stage:
- Configure via `config/config.yaml` with `design_llm_provider`, `devplan_llm_provider`, `handoff_llm_provider`
- Design stage automatically aligns with devplan stage unless explicitly overridden
- Stage clients are created in `_initialize_stage_clients()` method

### Key Components

**LLM Clients** (`src/clients/`)
- Factory pattern in `factory.py` creates appropriate client based on provider
- All clients inherit common interface with `generate_completion()` method
- Providers: `openai_client.py`, `generic_client.py`, `requesty_client.py`, `aether_client.py`, `agentrouter_client.py`

**State Management** (`src/state_manager.py`)
- Saves/loads pipeline checkpoints to `.devussy_state/` directory
- Checkpoint format includes stage name, timestamp, data, and metadata
- Supports listing, deleting, and cleaning up checkpoints

**Concurrency** (`src/concurrency.py`)
- `ConcurrencyManager` controls max concurrent LLM requests
- Used for parallel phase generation in detailed devplan stage
- Configurable via `max_concurrent_requests` in config

**Configuration** (`src/config.py`)
- `AppConfig` model with nested `LLMConfig` for provider/model settings
- Loads from `config/config.yaml` and environment variables
- Supports per-stage LLM overrides

**Templates** (`templates/`)
- Jinja2 templates for all LLM prompts
- Rendered via `src/templates.py` helper module
- Key templates: `project_design.jinja`, `basic_devplan.jinja`, `detailed_devplan.jinja`, `handoff_prompt.jinja`

**Models** (`src/models.py`)
- Pydantic models: `ProjectDesign`, `DevPlan`, `DevPlanPhase`, `DevPlanStep`, `HandoffPrompt`
- Provide structure and validation for pipeline data

### Update Ritual & Anchors
Devussy enforces a task-group update ritual (see `docs/update-ritual.md`):
- Work proceeds in groups of N tasks (configurable: default 3 for devplan, 5 for handoff)
- After each group, update all three locations before continuing:
  1. `devplan.md` - progress log and next task group
  2. `phaseX.md` - outcomes and blockers
  3. `handoff_prompt.md` - status snapshot

**Stable Anchors** (for deterministic updates):
- `<!-- PROGRESS_LOG_START -->` / `<!-- PROGRESS_LOG_END -->` in devplan.md
- `<!-- NEXT_TASK_GROUP_START -->` / `<!-- NEXT_TASK_GROUP_END -->` in devplan.md
- `<!-- PHASE_PROGRESS_START -->` / `<!-- PHASE_PROGRESS_END -->` in phaseX.md
- `<!-- HANDOFF_NOTES_START -->` / `<!-- HANDOFF_NOTES_END -->` in handoff_prompt.md

### Interactive UI (`src/ui/menu.py`)
- Main menu system with Settings → Provider & Models configuration
- Unified model picker aggregates models from all configured providers
- Session preferences (provider, API keys, base URLs) persist between runs via `load_last_used_preferences()`
- Only Generic provider prompts for base URL; others use safe defaults

### File Management (`src/file_manager.py`)
- Writes markdown artifacts to `output_dir` (default: `./docs`)
- Handles document versioning and updates

### Git Integration (`src/git_manager.py`)
- Optional automatic commits after each stage
- Configurable via `git_enabled`, `git_commit_after_design`, etc. in config

## Development Practices

### Code Style
- Python 3.9+ with type hints
- Black formatter (line length: 88)
- isort for import sorting (black-compatible profile)
- flake8 for linting
- Config in `pyproject.toml` and `.flake8`

### Testing
- pytest framework with pytest-asyncio for async tests
- Test structure: `tests/unit/` and `tests/integration/`
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Coverage target: 80% (enforced in pytest.ini)
- Run with `pytest -q` for quick output

### Configuration Files
- **pyproject.toml** - Project metadata, dependencies, tool configs (black, isort, pytest, coverage)
- **pytest.ini** - Additional pytest configuration (coverage thresholds, verbosity)
- **config/config.yaml** - Runtime configuration (LLM providers, models, API settings)
- **.env.example** - Template for environment variables (API keys)
- **.pre-commit-config.yaml** - Git pre-commit hooks (black, flake8, isort)

### Async Patterns
- All LLM generation methods are `async def`
- Use `asyncio.create_task()` and `asyncio.as_completed()` for concurrent operations
- `ConcurrencyManager.run_with_limit()` enforces max concurrent requests
- Main entry points use `asyncio.run()` to execute async pipelines

### Error Handling
- Comprehensive logging via `src/logger.py` (uses Python's logging module)
- LLM client errors include fallback/retry logic with `tenacity` library
- Fallback prompts in `DetailedDevPlanGenerator` if initial generation fails
- State checkpoints allow recovery from failures

### Environment Variables
Key environment variables (loaded via python-dotenv):
- `OPENAI_API_KEY` - OpenAI API key
- `GENERIC_API_KEY`, `GENERIC_BASE_URL` - Generic OpenAI-compatible provider
- `REQUESTY_API_KEY`, `REQUESTY_BASE_URL` - Requesty router
- `AETHER_API_KEY`, `AETHER_BASE_URL` - Aether AI
- `AGENTROUTER_API_KEY`, `AGENTROUTER_BASE_URL` - AgentRouter
- `DEVUSSY_NO_SPLASH` - Disable startup splash screen (set to "1" or "true")

Per-stage API keys (optional):
- `DESIGN_API_KEY`, `DEVPLAN_API_KEY`, `HANDOFF_API_KEY`

### Project Structure
```
src/
  clients/         # LLM provider implementations
  pipeline/        # Stage generators (design, devplan, handoff)
  ui/              # Interactive menu system
  prompts/         # (Appears unused - templates/ is primary)
  *.py            # Core modules (config, models, state, etc.)
templates/         # Jinja2 prompt templates
config/            # YAML configuration files
tests/
  unit/           # Unit tests
  integration/    # Integration tests
docs/             # Generated output (project_design.md, devplan.md, phase*.md, handoff_prompt.md)
scripts/          # Utility scripts (build_docs.py, regenerate_from_checkpoint.py)
logs/             # Application logs
.devussy_state/   # Checkpoint persistence
```

## Tips for Working with Devussy

### Adding New LLM Providers
1. Create new client in `src/clients/` implementing the base `LLMClient` interface
2. Update `src/clients/factory.py` to handle the new provider
3. Add configuration section to `config/config.yaml`
4. Add environment variable template to `.env.example`

### Modifying Pipeline Stages
- Each stage has a dedicated generator class in `src/pipeline/`
- Generators use Jinja2 templates from `templates/` directory
- Response parsing logic is in `_parse_response()` methods
- Test changes with unit tests in `tests/unit/test_pipeline_generators.py`

### Debugging LLM Responses
- Set `log_level: DEBUG` in `config/config.yaml` for verbose logging
- Check `logs/devussy.log` for detailed prompt/response traces
- Use `--verbose` flag on CLI commands
- Response previews are logged at INFO level

### Customizing Templates
- Edit Jinja2 templates in `templates/` directory
- Test template rendering with `src/templates.py:render_template()`
- Context variables are documented in each generator's `generate()` method

### Working with Checkpoints
- Checkpoints save to `.devussy_state/checkpoint_<key>.json`
- Include full stage data, timestamp, and metadata
- Use `--resume-from <key>` to continue from a checkpoint
- Checkpoint keys typically follow pattern: `<project_name>_pipeline`
