# Changelog

All notable changes to the DevPlan Orchestrator (devussy) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Next Steps
- Frontend UI for configuration management (Phase 11.3 frontend)
- Complete web interface components (project list, file viewer)
- End-to-end testing for web interface

---

## [0.2.3] - 2025-10-21

### Added - Configuration System (Phase 11.3 Backend - COMPLETED)
- **Web Configuration Management System:**
  - `src/web/security.py` - Secure API key encryption using Fernet symmetric encryption
  - `src/web/config_models.py` - Complete Pydantic data models for configuration
  - `src/web/config_storage.py` - JSON file-based storage with file locking
  - `src/web/routes/config.py` - Full REST API for configuration management (15+ endpoints)
  - Built-in configuration presets (cost-optimized, max-quality, anthropic-claude, balanced)
  - Credential CRUD operations with encryption
  - Global configuration management
  - Project-specific configuration overrides
  - API key validation/testing endpoint
  - Cost estimation system
  - Model discovery per provider

- **New Dependencies:**
  - `cryptography>=41.0.0` for API key encryption
  - `filelock>=3.12.0` for safe concurrent file access

- **Comprehensive Testing:**
  - `tests/unit/test_web_security.py` - 13 tests for encryption/masking
  - `tests/unit/test_config_storage.py` - 14 tests for storage operations
  - **Total new tests: 27** (387 → 414 tests, +7%)
  - All configuration tests passing ✅

### Changed
- **Test Coverage:** 71% → 73% (+2 percentage points)
- **Total Tests:** 387 → 414 (+27 tests)
- Updated `src/web/app.py` to include configuration routes
- Auto-create config directories on application startup
- Fixed datetime deprecation warnings (datetime.utcnow → datetime.now(timezone.utc))

### Documentation
- Updated `HANDOFF.md` with Phase 11.3 completion status
- Updated `devplan.md` tracking configuration system implementation
- `WEB_CONFIG_DESIGN.md` - Complete technical specification (600+ lines)
- `IMPLEMENTATION_GUIDE.md` - Step-by-step implementation guide (400+ lines)

### Security
- API keys encrypted at rest using Fernet (AES 128-bit)
- Keys never exposed in API responses (always masked: "sk-t...789")
- Support for environment variable encryption key
- File locking prevents concurrent access corruption

---

## [0.2.2] - 2025-10-20

### Added
- **Test Coverage Improvement (Phase 10.5 - COMPLETED):**
  - Created comprehensive test suite for all pipeline generators (27 tests)
  - Added `tests/unit/test_rate_limiter.py` with 41 new tests for rate limiting functionality
  - Added `tests/unit/test_streaming.py` with 34 new tests for streaming handlers
  - Added `tests/unit/test_pipeline_generators.py` with 27 new tests
  - Expanded `tests/unit/test_cli.py` with 16 additional tests
  - **Total new tests: 118** (269 → 387 tests, +44%)
  - Test coverage for ProjectDesignGenerator, BasicDevPlanGenerator, DetailedDevPlanGenerator, HandoffPromptGenerator
  - Comprehensive rate limiter testing (exponential backoff, retry-after headers, adaptive rate limiting)
  - Complete streaming functionality testing (handlers, simulators, integration)
  
### Fixed
- Fixed Jinja2 template error by adding `enumerate` and `len` to template environment globals
- All handoff prompt template tests now pass

### Changed
- **Major Test Coverage Improvements (Phase 10.5):**
  - `src/streaming.py`: **27% → 98%** (+71 percentage points) 🎉
  - `src/rate_limiter.py`: **34% → 92%** (+58 percentage points) ✅
  - `src/pipeline/project_design.py`: **17% → 100%** (+83 percentage points) ✅
  - `src/pipeline/basic_devplan.py`: **25% → 100%** (+75 percentage points) ✅
  - `src/pipeline/detailed_devplan.py`: **26% → 95%** (+69 percentage points) ✅
  - `src/pipeline/handoff_prompt.py`: **30% → 100%** (+70 percentage points) ✅
  - `src/cli.py`: **26% → 43%** (+17 percentage points)
  - `src/templates.py`: Now 100% coverage
  - **Overall coverage: 56% → 71%** (+15 percentage points - 70% goal EXCEEDED!) 🎉
  - **Total tests: 269 → 387** (+118 tests, +44%)
  - **Test Status:** All 387 tests passing (362 unit + 25 integration)

### Documentation
- Updated `devplan.md` with Phase 10.5 complete progress tracking
- Updated `HANDOFF.md` with final coverage metrics (71%) and test count (387)
- Updated `TESTING.md` with comprehensive coverage analysis and all new test files
- Created `SESSION_SUMMARY_OCT20_PHASE10_5.md` documenting the test coverage improvement initiative

### Achievements
- ✅ **71% test coverage achieved** - exceeded 70% goal!
- ✅ **387 tests passing** - up from 269 (+44%)
- ✅ **Production ready** - comprehensive test suite covering all critical components
- ✅ **Streaming module** - near-perfect coverage (98%)
- ✅ **Rate limiter** - comprehensive coverage (92%)
- ✅ **Pipeline generators** - complete coverage (95-100%)

## [0.2.1] - 2025-10-20

### Fixed
- **Critical:** Fixed CLI import errors by upgrading Typer from 0.9.0 to 0.20.0
- Removed secondary flags (`-c`, `-o`, `-k`, `-f`) from non-boolean CLI options
- All 244 unit tests now pass (previously 15 failures in CLI tests)

### Changed
- Updated `requirements.txt` to require `typer>=0.20.0` (was 0.12.0)
- Updated `requirements.txt` to require `rich>=13.0.0` (was missing)

## [0.2.0] - 2025-10-19 

### Added

#### Multi-LLM Configuration
- Per-stage LLM configuration support
- Cost optimization through different models per pipeline stage
- Billing separation with per-stage API keys
- Provider mixing capabilities (e.g., GPT-4 for design, GPT-3.5 for devplan)
- Interactive API key prompting and validation

### Fixed
- Interactive mode spinner no longer blocks terminal input
- Better progress indicators in CLI

## [0.1.0] - 2025-10-19

### Added

#### Core Features
- Multi-phase LLM orchestration pipeline: project design → basic devplan → detailed devplan → handoff prompt
- Provider-agnostic LLM client system supporting OpenAI, Generic (OpenAI-compatible), and Requesty providers
- Factory pattern for dynamic LLM client instantiation
- Async execution with configurable concurrency control using asyncio and semaphores
- Comprehensive retry logic with exponential backoff using tenacity
- Jinja2-based template system for prompt generation

#### CLI Interface
- `devussy generate-design` - Generate project design from requirements
- `devussy generate-devplan` - Create development plan from project design
- `devussy generate-handoff` - Generate handoff prompt from devplan
- `devussy run-full-pipeline` - Execute complete pipeline end-to-end
- `devussy init-repo` - Initialize new project repositories
- `devussy list-checkpoints` - View all saved checkpoints
- `devussy delete-checkpoint` - Remove specific checkpoint
- `devussy cleanup-checkpoints` - Remove old/stale checkpoints
- `devussy version` - Display version information

#### State Management & Recovery
- JSON-based state persistence in `.devussy_state/` directory
- Checkpoint system for resumable workflows
- `--resume-from` flag for recovering from interruptions
- Intelligent stage detection and resumption logic
- Support for concurrent pipeline executions with isolated states

#### Git Integration
- Automatic Git commits after each pipeline stage
- Repository initialization with remote support
- GitManager class for all Git operations
- Commit message standardization

#### Documentation System
- Automated documentation generation from templates
- Documentation indexing with cross-references
- Citation management for external sources
- Update logging with timestamps
- Markdown report generation
- API documentation generation with pdoc

#### Runtime Features
- Real-time streaming output support with StreamingHandler
- StreamingSimulator for testing streaming functionality
- Rate limiting with token bucket algorithm
- Adaptive rate adjustment based on API responses
- User feedback integration for iterative refinement
- Dynamic provider switching during pipeline execution

#### Configuration
- YAML-based configuration system (`config/config.yaml`)
- Environment variable support via python-dotenv
- Pydantic-based validation for all configuration
- Support for custom templates and provider settings

#### Testing
- 242 comprehensive tests (57% coverage)
- Unit tests for all core modules
- Integration tests for pipeline orchestration
- Async test support with pytest-asyncio
- Shared fixtures in conftest.py
- Coverage reporting with pytest-cov

#### CI/CD
- GitHub Actions workflow for automated testing
- Code quality checks (black, flake8, isort)
- Documentation deployment workflow
- Release automation workflow

#### Development Tools
- Pre-commit hooks for code formatting
- Black formatter configuration (88 char line length)
- Flake8 linting rules
- isort import sorting
- Cross-platform support (Windows, macOS, Linux)

### Technical Details

#### Dependencies
- Python 3.9+ support
- OpenAI SDK for OpenAI provider integration
- aiohttp for generic HTTP client
- Pydantic v2 for data validation
- Jinja2 for templating
- Typer for CLI framework
- GitPython for Git operations
- tenacity for retry logic
- pytest ecosystem for testing

#### Architecture
- Fully asynchronous core using asyncio
- Modular pipeline architecture
- Provider-agnostic design pattern
- Separation of concerns: clients, pipeline, state, documentation
- Extensible plugin system for custom providers

### Known Issues
- Test coverage at 57% (target: 80%+)
- Some Windows path handling edge cases
- Limited error recovery in certain scenarios
- Performance optimization opportunities for large devplans

### Documentation
- Comprehensive README.md with usage examples
- Architecture documentation in docs/ARCHITECTURE.md
- Testing guide in docs/TESTING.md
- Update log tracking in docs/update_log.md
- API documentation generation support
- Template documentation for custom prompts

---

## [Unreleased]

### Planned for 0.2.0
- FastAPI-based web interface
- WebSocket streaming for real-time updates
- Web UI for devplan generation
- Plugin system for custom LLM providers
- Export devplan to PDF/HTML/JSON
- Enhanced progress bars with ETA
- Interactive CLI prompts
- Improved test coverage (target: 80%+)

---

## Version History

- **0.1.0** (2025-10-19) - Initial release with core features

[0.1.0]: https://github.com/mojomast/devussy-fresh/releases/tag/v0.1.0
[Unreleased]: https://github.com/mojomast/devussy-fresh/compare/v0.1.0...HEAD
