# Project Structure

## Top-Level Organization

```
devussy/
├── src/                    # Main source code
├── tests/                  # Test suite (unit + integration)
├── templates/              # Jinja2 templates for prompts
├── config/                 # Configuration files
├── docs/                   # Generated documentation output
├── scripts/                # Utility scripts
├── logs/                   # Application logs
└── .devussy_state/         # State persistence (checkpoints)
```

## Source Code Layout (src/)

### Core Modules

- **cli.py**: Typer-based CLI with all commands (generate-design, generate-devplan, run-full-pipeline, etc.)
- **entry.py**: Lightweight entry point for interactive interview mode
- **config.py**: Configuration loading with Pydantic models (AppConfig, LLMConfig, etc.)
- **models.py**: Core data models (ProjectDesign, DevPlan, DevPlanPhase, HandoffPrompt)
- **llm_client.py**: LLM provider abstraction layer

### Pipeline Components (src/pipeline/)

- **compose.py**: PipelineOrchestrator - main orchestration logic
- **project_design.py**: ProjectDesignGenerator
- **basic_devplan.py**: BasicDevPlanGenerator
- **detailed_devplan.py**: DetailedDevPlanGenerator
- **design_review.py**: DesignReviewGenerator (pre-review feature)
- **handoff_prompt.py**: HandoffPromptGenerator

### Client Implementations (src/clients/)

- **factory.py**: LLM client factory for provider selection
- Provider-specific clients (OpenAI, Aether, AgentRouter, Requesty, Generic)

### Interview System (src/interview/)

- **repository_analyzer.py**: RepositoryAnalyzer for existing project analysis
- **llm_interview.py**: LLM-driven interview flow

### UI Components (src/ui/)

- **menu.py**: Interactive menu system with settings management
- Session preferences and provider configuration

### Supporting Modules

- **state_manager.py**: Checkpoint management for resumable pipelines
- **file_manager.py**: Safe file writing with validation
- **git_manager.py**: Git integration for automatic commits
- **concurrency.py**: ConcurrencyManager for parallel phase generation
- **streaming.py**: Token streaming handlers
- **progress_reporter.py**: Terminal progress indicators
- **rate_limiter.py**: API rate limiting
- **retry.py**: Retry logic with exponential backoff
- **logger.py**: Logging configuration
- **feedback_manager.py**: Feedback collection for iterative refinement

## Templates (templates/)

- **project_design.jinja**: Project design generation prompt
- **basic_devplan.jinja**: Basic devplan structure prompt
- **detailed_devplan.jinja**: Detailed phase expansion prompt
- **design_review.jinja**: Design review and validation prompt
- **handoff_prompt.jinja**: Handoff document generation prompt
- **docs/**: Documentation-specific templates

## Tests (tests/)

```
tests/
├── unit/                   # Unit tests for individual modules
├── integration/            # Integration tests for full workflows
├── conftest.py            # Pytest fixtures and configuration
└── __pycache__/
```

## Configuration Files

- **pyproject.toml**: Package metadata, dependencies, tool configs (black, isort, pytest, coverage)
- **pytest.ini**: Pytest configuration (markers, coverage settings)
- **.flake8**: Flake8 linting rules
- **requirements.txt**: Pinned dependencies
- **config/config.yaml**: Application configuration (LLM settings, pipeline options)
- **config/questions.yaml**: Interview question definitions

## Architecture Patterns

### Pipeline Pattern

The core architecture follows a multi-stage pipeline:
1. ProjectDesignGenerator → ProjectDesign
2. BasicDevPlanGenerator → DevPlan (structure)
3. DetailedDevPlanGenerator → DevPlan (expanded phases)
4. HandoffPromptGenerator → HandoffPrompt

Each generator is async and uses the LLMClient abstraction.

### State Management

- **StateManager**: Handles checkpoint persistence to .devussy_state/
- **PhaseStateManager**: Manages individual phase states during generation
- Checkpoints enable resume functionality via `--resume-from` flag

### Concurrency

- **ConcurrencyManager**: Controls parallel phase generation
- Default: 5 concurrent requests/phases
- Configurable via `max_concurrent_requests` in config or `MAX_CONCURRENT_REQUESTS` env var

### Provider Abstraction

- **LLMClient**: Base interface for all providers
- **ClientFactory**: Creates provider-specific clients
- Supports: OpenAI, Aether, AgentRouter, Requesty, Generic (OpenAI-compatible)
- Per-stage model overrides via design_llm, devplan_llm, handoff_llm configs

## Key Conventions

- **Async-first**: All LLM interactions and I/O operations use async/await
- **Pydantic models**: Strict validation for all data structures
- **Jinja2 templates**: All prompts are templated for maintainability
- **Rich console**: Terminal UI uses rich library for formatting
- **Checkpoint keys**: Format `<project>_pipeline` for full pipeline runs
- **Output determinism**: Files written to docs/ with consistent naming
- **Error handling**: Graceful degradation with informative error messages
