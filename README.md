# DevPlan Orchestrator (devussy)

[![PyPI version](https://badge.fury.io/py/devussy.svg)](https://badge.fury.io/py/devussy)
[![Tests](https://github.com/mojomast/devussy-fresh/workflows/Tests/badge.svg)](https://github.com/mojomast/devussy-fresh/actions/workflows/test.yml)
[![Code Quality](https://github.com/mojomast/devussy-fresh/workflows/Code%20Quality/badge.svg)](https://github.com/mojomast/devussy-fresh/actions/workflows/quality.yml)
[![codecov](https://codecov.io/gh/mojomast/devussy-fresh/branch/master/graph/badge.svg)](https://codecov.io/gh/mojomast/devussy-fresh)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> 🚀 **An AI-powered development planning tool that transforms your ideas into detailed, executable development plans**

DevPlan Orchestrator is a Python-based LLM orchestration tool that automatically generates and maintains comprehensive development plans by coordinating multiple AI providers. Perfect for developers, project managers, and teams who want to accelerate their planning process with AI.

## Overview

DevPlan Orchestrator accepts user inputs (project requirements, languages, frameworks) and generates detailed, executable development plans. It supports multiple LLM providers (OpenAI, Requesty, generic OpenAI-compatible APIs) and integrates with Git for automatic documentation and version control.

## ✨ Features

- 🎭 **Multi-LLM Configuration**: Use different models/providers for each pipeline stage - optimize costs and performance
- 🔌 **Provider-Agnostic**: Support for OpenAI, Generic OpenAI-compatible APIs, and custom providers
- ⚡ **Async Performance**: Efficient concurrent API calls with configurable rate limiting
- 🔄 **Multi-Phase Pipeline**: project design → basic plan → detailed plan → handoff prompt
- 💾 **State Persistence**: Resumable workflows with checkpoint system - never lose progress
- 🎯 **Git Integration**: Automatic commits and version control for all generated artifacts
- 📝 **Documentation Generation**: Beautiful, structured documentation with Jinja2 templates
- 🧪 **Battle-Tested**: 414 passing tests with 73% code coverage
- 🛡️ **Robust**: Exponential backoff retry logic and comprehensive error handling
- 🎨 **Flexible**: Customizable templates and configuration for your workflow
- 🎨 **Interactive Mode**: Guided questionnaire for easy project setup

## Installation

### From PyPI (Recommended)

```bash
pip install devussy
```

### From Source

1. **Clone the repository**
   ```bash
   git clone https://github.com/mojomast/devussy-fresh.git
   cd devussy-fresh
   ```

2. **Install in development mode**
   ```bash
   pip install -e .
   ```

   Or with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Configure environment variables**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

   Required environment variables:
   - `OPENAI_API_KEY` - Your OpenAI API key (for OpenAI provider)
   - `GENERIC_API_KEY` - API key for generic OpenAI-compatible providers
   - `GENERIC_API_BASE_URL` - Base URL for generic provider
   - `REQUESTY_API_KEY` - API key for Requesty provider (optional)
   
   **NEW: Per-Stage API Keys** (optional):
   - `DESIGN_API_KEY` - API key specifically for design stage
   - `DEVPLAN_API_KEY` - API key specifically for devplan stage
   - `HANDOFF_API_KEY` - API key specifically for handoff stage
   
   See [Multi-LLM Configuration Guide](MULTI_LLM_GUIDE.md) for details on using different models per stage.

### Verify Installation

After installation, verify that the CLI is working:

```bash
devussy version
```

You should see version `0.3.2` and the tool information.

## Quick Start

### Option 1: Interactive CLI Mode

The easiest way to get started is with the interactive questionnaire:

```bash
devussy interactive-design
```

You'll be guided through a series of questions to define your project, and the tool will generate a complete design for you.

### Option 2: Command-Line Mode (For Automation)

Initialize a new project:
```bash
devussy init-repo ./my-project
```

Generate a complete development plan:
```bash
devussy run-full-pipeline \
  --name "My Web App" \
  --languages "Python,TypeScript" \
  --requirements "Build a REST API with authentication" \
  --frameworks "FastAPI,React"
```

## CLI Commands

### `init-repo` - Initialize Repository

Initialize a new project repository with DevPlan Orchestrator structure.

```bash
devussy init-repo [PATH] [OPTIONS]
```

**Arguments:**
- `PATH` - Path to initialize (defaults to current directory)

**Options:**
- `--remote, -r` - Git remote URL to add
- `--force, -f` - Force initialization even if directory not empty

**Example:**
```bash
devussy init-repo ./my-project --remote https://github.com/mojomast/devussy.git
```

### `generate-design` - Generate Project Design

Generate a project design from user inputs.

```bash
devussy generate-design [OPTIONS]
```

**Required Options:**
- `--name, -n` - Project name
- `--languages, -l` - Comma-separated programming languages
- `--requirements, -r` - Project requirements

**Optional Options:**
- `--frameworks, -f` - Comma-separated frameworks
- `--apis, -a` - Comma-separated external APIs
- `--config, -c` - Path to config file
- `--provider, -p` - LLM provider override (openai, generic, requesty)
- `--model, -m` - Model override
- `--output-dir, -o` - Output directory
- `--output-path` - Specific output file path
- `--streaming` - Enable token streaming
- `--verbose, -v` - Enable verbose logging
- `--debug` - Enable debug mode with full tracebacks

**Example:**
```bash
devussy generate-design \
  --name "E-commerce API" \
  --languages "Python,JavaScript" \
  --requirements "Build a scalable e-commerce backend" \
  --frameworks "FastAPI,PostgreSQL" \
  --apis "Stripe,SendGrid" \
  --verbose
```

### `interactive-design` - Interactive Project Design (✨ NEW!)

Generate a project design through an interactive guided questionnaire. Perfect for users who prefer a conversational experience over command-line flags.

```bash
devussy interactive-design [OPTIONS]
```

**Features:**
- 🎯 Guided questionnaire with helpful prompts
- 💡 Smart conditional questions based on your answers
- 📝 Examples and help text for each question
- 💾 Save and resume sessions
- 🎨 Beautiful CLI interface with progress indicators

**Options:**
- `--config, -c` - Path to config file
- `--provider, -p` - LLM provider override
- `--model, -m` - Model override
- `--output-dir, -o` - Output directory
- `--save-session` - Save session to file (path)
- `--resume-session` - Resume from saved session (path)
- `--streaming` - Enable token streaming
- `--verbose, -v` - Enable verbose logging
- `--debug` - Enable debug mode

#### Interactive Settings Menu (Phase 2)
When you start `devussy interactive-design`, a keyboard-navigable settings menu opens first (uses prompt_toolkit). You can adjust:

- Provider (openai, generic, requesty)
- Interview model and final-stage model (devplan/handoff)
- Temperature and max tokens
- Enable/disable streaming
- API key for this session (masked input)

You can re-open the menu anytime during the interview via slash commands:

- `/settings` - Open the full settings menu
- `/model` - Quick set interview/final-stage models
- `/temp` - Quick set temperature
- `/tokens` - Show last token usage snapshot (if provided by provider)

All settings are applied in-memory for the current run and flow through to the pipeline (design → devplan → handoff) without persisting keys to disk.

**Example - Basic Interactive Session:**
```bash
devussy interactive-design
# Follow the prompts to answer questions about your project
```

**Example - Save Session:**
```bash
devussy interactive-design --save-session my-project-session.json
```

**Example - Resume Previous Session:**
```bash
devussy interactive-design --resume-session my-project-session.json
```

**Questions Asked:**
The interactive questionnaire covers:
- Project name and type (Web App, API, CLI, etc.)
- Programming languages
- Frameworks (frontend/backend)
- Database requirements
- Authentication needs
- External API integrations
- Deployment platform
- Testing and CI/CD requirements
- Documentation level

Questions adapt based on your answers - for example, frontend framework questions only appear if you're building a web application.

---

### `generate-devplan` - Generate Development Plan

Generate a development plan from an existing project design.

```bash
devussy generate-devplan DESIGN_FILE [OPTIONS]
```

**Arguments:**
- `DESIGN_FILE` - Path to project design JSON file

**Options:**
- `--config, -c` - Path to config file
- `--provider, -p` - LLM provider override
- `--model, -m` - Model override
- `--output-dir, -o` - Output directory
- `--output-path` - Specific output file path
- `--max-concurrent` - Maximum concurrent API requests
- `--streaming` - Enable token streaming
- `--verbose, -v` - Enable verbose logging
- `--debug` - Enable debug mode with full tracebacks

**Example:**
```bash
devussy generate-devplan docs/design.json --max-concurrent 10 --verbose
```

### `generate-handoff` - Generate Handoff Prompt

Generate a handoff prompt from a development plan.

```bash
devussy generate-handoff DEVPLAN_FILE [OPTIONS]
```

**Arguments:**
- `DEVPLAN_FILE` - Path to devplan JSON file

**Required Options:**
- `--name, -n` - Project name

**Options:**
- `--config, -c` - Path to config file
- `--output-dir, -o` - Output directory
- `--output-path` - Specific output file path
- `--verbose, -v` - Enable verbose logging
- `--debug` - Enable debug mode with full tracebacks

**Example:**
```bash
devussy generate-handoff docs/devplan.json --name "My Project"
```

### `run-full-pipeline` - Complete Pipeline

Run the complete pipeline from inputs to handoff prompt.

```bash
devussy run-full-pipeline [OPTIONS]
```

**Required Options:**
- `--name, -n` - Project name
- `--languages, -l` - Comma-separated programming languages
- `--requirements, -r` - Project requirements

**Optional Options:**
- `--frameworks, -f` - Comma-separated frameworks
- `--apis, -a` - Comma-separated external APIs
- `--config, -c` - Path to config file
- `--provider, -p` - LLM provider override
- `--model, -m` - Model override
- `--output-dir, -o` - Output directory
- `--max-concurrent` - Maximum concurrent API requests
- `--streaming` - Enable token streaming
- `--verbose, -v` - Enable verbose logging
- `--debug` - Enable debug mode with full tracebacks

**Example:**
```bash
devussy run-full-pipeline \
  --name "ML Pipeline" \
  --languages "Python" \
  --requirements "Build a machine learning training pipeline" \
  --frameworks "PyTorch,FastAPI,Docker" \
  --provider openai \
  --model gpt-4 \
  --max-concurrent 5 \
  --verbose
```

### `version` - Display Version

Display version information.

```bash
devussy version
```

## Example Workflows

### Workflow 1: New Project from Scratch

```bash
# Step 1: Initialize repository
devussy init-repo ./my-app

# Step 2: Navigate to directory
cd my-app

# Step 3: Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# Step 4: Generate complete plan
devussy run-full-pipeline \
  --name "My App" \
  --languages "Python,JavaScript" \
  --requirements "Build a web application with user auth" \
  --frameworks "FastAPI,React"

# Step 5: Review generated files
ls docs/
# Output: project_design.md  devplan.md  handoff_prompt.md
```

### Workflow 2: Incremental Generation

```bash
# Step 1: Generate project design
devussy generate-design \
  --name "Data Pipeline" \
  --languages "Python" \
  --requirements "ETL pipeline for processing data" \
  --output-path ./design.json

# Step 2: Review and modify design.json if needed
cat design.json

# Step 3: Generate devplan from design
devussy generate-devplan design.json --output-path ./devplan.json

# Step 4: Generate handoff prompt
devussy generate-handoff devplan.json --name "Data Pipeline"
```

### Workflow 3: Using Different LLM Providers

```bash
# Using OpenAI (default)
devussy run-full-pipeline \
  --name "Project" \
  --languages "Python" \
  --requirements "Build an API" \
  --provider openai \
  --model gpt-4

# Using a custom OpenAI-compatible API
export GENERIC_BASE_URL="https://api.example.com/v1"
export GENERIC_API_KEY="your-key"

devussy run-full-pipeline \
  --name "Project" \
  --languages "Python" \
  --requirements "Build an API" \
  --provider generic
```

## Configuration

Configuration is managed through `config/config.yaml`. Key settings include:

### Global LLM Settings
- `llm_provider`: Choose from "openai", "generic", or "requesty"
- `model`: Model identifier (e.g., "gpt-4")
- `temperature`: Sampling temperature (0.0-2.0)
- `max_tokens`: Maximum tokens to generate
- `api_key`: API key (can also be set via environment variables)

### Per-Stage LLM Settings (NEW! 🎭)
Override global settings for specific pipeline stages:
- `design_model`: Model for project design generation
- `devplan_model`: Model for devplan generation
- `handoff_model`: Model for handoff prompt generation

**Example - Cost Optimization:**
```yaml
# Use GPT-4 for complex design, GPT-3.5-turbo for structured devplan
model: gpt-4
devplan_model: gpt-3.5-turbo
```

**Example - Different API Keys:**
```bash
export DESIGN_API_KEY="sk-design-account-..."
export DEVPLAN_API_KEY="sk-devplan-account-..."
```

### Other Settings
- `max_concurrent_requests`: Limit concurrent API calls
- `retry`: Retry settings for failed requests
- `streaming_enabled`: Enable/disable token streaming

See `config/config.yaml` for all available options, or read the [Multi-LLM Configuration Guide](MULTI_LLM_GUIDE.md) for detailed usage.

## Documentation

- **[Multi-LLM Configuration Guide](MULTI_LLM_GUIDE.md)** - Use different models per pipeline stage
- **[Multi-LLM Quick Start](MULTI_LLM_QUICKSTART.md)** - Quick reference for multi-LLM setup
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and module descriptions
- [Provider Guide](docs/PROVIDERS.md) - How to add new LLM providers
- [Testing Guide](docs/TESTING.md) - Testing strategy and coverage
- [API Documentation](docs/api/) - Auto-generated API docs

## Project Structure

```
devussy/
├── src/                    # Source code
│   ├── clients/            # LLM client implementations
│   │   ├── factory.py      # Client factory for provider selection
│   │   ├── openai_client.py    # OpenAI API client
│   │   ├── generic_client.py   # Generic OpenAI-compatible client
│   │   └── requesty_client.py  # Requesty API client
│   ├── pipeline/           # Pipeline stages
│   │   ├── project_design.py   # Project design generation
│   │   ├── basic_devplan.py    # Basic devplan generation
│   │   ├── detailed_devplan.py # Detailed devplan generation
│   │   ├── handoff_prompt.py   # Handoff prompt generation
│   │   └── compose.py      # Pipeline orchestration
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── llm_client.py       # Abstract LLM client interface
│   ├── concurrency.py      # Concurrency control
│   ├── retry.py            # Retry logic with exponential backoff
│   ├── templates.py        # Template loading and rendering
│   ├── citations.py        # Citation embedding
│   ├── git_manager.py      # Git operations
│   ├── file_manager.py     # File operations
│   ├── doc_logger.py       # Documentation logging
│   ├── doc_index.py        # Documentation indexing
│   ├── models.py           # Data models
│   ├── logger.py           # Logging configuration
│   ├── run_scheduler.py    # Task scheduling
│   └── state_manager.py    # State persistence
├── tests/                  # Tests (117+ comprehensive tests)
│   └── unit/               # Unit tests
│       ├── test_config.py      # Configuration tests (34 tests)
│       ├── test_llm_clients.py # LLM client tests (29 tests)
│       ├── test_concurrency.py # Concurrency tests (13 tests)
│       ├── test_retry.py       # Retry logic tests (18 tests)
│       ├── test_templates.py   # Template tests (23 tests)
│       ├── test_documentation.py # Documentation tests
│       └── test_git_manager.py # Git integration tests (17 tests)
├── templates/              # Jinja2 prompt templates
│   ├── docs/               # Documentation templates
│   ├── project_design.jinja    # Project design prompt
│   ├── basic_devplan.jinja     # Basic devplan prompt
│   ├── detailed_devplan.jinja  # Detailed devplan prompt
│   └── handoff_prompt.jinja    # Handoff prompt template
├── config/                 # Configuration files
│   └── config.yaml         # Main configuration
├── docs/                   # Generated documentation
│   └── update_log.md       # Documentation update log
├── scripts/                # Build and utility scripts
│   └── build_docs.py       # API documentation generator
└── examples/               # Example projects (future)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Check style
flake8 src/

# Sort imports
isort src/
```

### Running with Coverage

```bash
pytest --cov=src --cov-report=html tests/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Setting up development environment
- Running tests and linting
- Submitting pull requests
- Code style expectations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [x] Phase 1: Project Initialization
- [x] Phase 2: Core Abstractions  
- [x] Phase 3: Prompt Generation Pipeline
- [x] Phase 4: Command-Line Interface
- [x] Phase 5: Git Integration
- [x] Phase 6: Documentation Generation
- [x] Phase 7: Testing (414 comprehensive tests, 73% coverage) ✅
- [x] Phase 8: CI/CD (GitHub Actions workflows, coverage reporting, automated releases)
- [x] Phase 9: Multi-LLM Support (Different models per stage with stage-specific configuration) ✅
- [x] Phase 10: Packaging and Distribution (v0.3.2 ready for PyPI - Oct 21, 2025) ✅
- [ ] Phase 11: Production Deployment (PyPI publish, documentation site)
- [ ] Phase 12: Enhanced Features (Advanced configuration, output formats)
- [ ] Phase 13: Performance Optimization (Caching, parallel processing improvements)

## Support

For questions, issues, or feature requests, please open an issue on the GitHub repository.
