"""Version information for DevPlan Orchestrator."""

__version__ = "0.1.1"
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

__title__ = "devussy"
__description__ = (
    "A Python-based LLM orchestration tool that automatically generates "
    "and maintains development plans"
)
__author__ = "DevPlan Orchestrator Team"
__license__ = "MIT"
__url__ = "https://github.com/mojomast/devussy-fresh"

# Version history
VERSION_HISTORY = {
    "0.1.1": {
        "date": "2025-11-11",
        "changes": [
            "Provider & Models menu now includes API Key and Base URL for the active provider",
            "Unified model picker aggregates models across configured providers and auto-switches provider on selection",
            "Per-provider API keys and base URLs persist across sessions via StateManager",
            "Aether endpoint normalized to /v1/chat/completions; default base URL https://api.aetherapi.dev",
            "Only Generic prompts for Base URL; others auto-populate defaults",
            "Last-used provider/keys/base URLs are auto-applied on startup before client creation",
        ],
    },
    "0.2.3": {
        "date": "2025-10-21",
        "changes": [
            "Phase 11.3 backend complete: Configuration management system",
            "Web configuration API with 15+ REST endpoints",
            "Secure API key storage with Fernet encryption",
            "Configuration presets (cost-optimized, max-quality, etc.)",
            "Global config and per-project overrides",
            "27 new configuration tests (414 total tests)",
            "Coverage improved to 73% (from 71%)",
            "Fixed datetime deprecation warnings",
            "Production ready backend for web configuration",
        ],
    },
    "0.2.2": {
        "date": "2025-10-20",
        "changes": [
            "Phase 10.5 complete: Test coverage improvement initiative",
            "Overall coverage: 56% → 71% (+15 percentage points)",
            "Total tests: 269 → 387 (+118 tests, +44%)",
            "Streaming module coverage: 27% → 98%",
            "Rate limiter coverage: 34% → 92%",
            "Pipeline generators coverage: 17-30% → 95-100%",
            "CLI tests expanded with 16 additional tests",
            "All 387 tests passing (362 unit + 25 integration)",
            "Production ready with comprehensive test suite",
        ],
    },
    "0.2.1": {
        "date": "2025-10-20",
        "changes": [
            "Fixed critical CLI import errors",
            "Upgraded Typer from 0.9.0 to 0.20.0",
            "Removed problematic secondary flags from CLI",
            "All 244 unit tests now passing",
        ],
    },
    "0.2.0": {
        "date": "2025-10-19",
        "changes": [
            "Multi-LLM configuration support",
            "Per-stage LLM configuration",
            "Cost optimization through different models",
            "Billing separation with per-stage API keys",
            "Interactive API key prompting",
            "Fixed interactive mode spinner blocking",
        ],
    },
    "0.1.0": {
        "date": "2025-10-19",
        "changes": [
            "Initial release with core orchestration features",
            "Support for OpenAI, Generic, and Requesty LLM providers",
            "Multi-phase pipeline: design → basic → detailed → handoff",
            "CLI with 6+ commands including checkpoint management",
            "Async execution with concurrency control",
            "State persistence and resumable workflows",
            "Git integration with auto-commits",
            "Documentation generation with templates",
            "Rate limiting and retry logic",
            "User feedback integration",
            "242 passing tests with 57% coverage",
        ],
    },
}


def get_version() -> str:
    """Return the current version string."""
    return __version__


def get_version_info() -> dict:
    """Return detailed version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "title": __title__,
        "description": __description__,
        "author": __author__,
        "license": __license__,
        "url": __url__,
    }
