```text
████████████      ██████████████    ████      ████    ████      ████      ██████████        ██████████      ████      ████    
████      ████    ████              ████      ████    ████      ████    ████              ████              ████      ████    
████      ████    ████              ████      ████    ████      ████    ████              ████                ████  ████      
████      ████    ████████████        ████  ████      ████      ████      ██████████        ██████████          ██████        
████      ████    ████                  ██████        ████      ████              ████              ████          ██          
████      ████    ████                  ██████        ████      ████              ████              ████          ██          
████████████      ██████████████          ██            ██████████        ██████████        ██████████            ██          
```

# Devussy

compose. code. conduct.

Devussy turns a short project idea into a complete, actionable development plan. It interviews you (or reads flags), drafts a project design, expands it into a detailed multi-phase DevPlan with per-step tasks, and produces a handoff document—saving everything as markdown you can check in.

• Repo: https://github.com/mojomast/devussy
• Python: 3.9+
• Version: 0.2.0 (Release 01)

## What's New in Release 01

**🎉 Major Milestones Achieved:**

1. **Interview Mode (Phases 1-3)** ✅
   - Repository analysis engine for existing codebases
   - LLM-driven interview with context-aware questioning
   - Code sample extraction (architecture, patterns, tests)
   - Context-aware devplan generation with repo insights
   - Real-world validation with GPT-5 mini via Requesty

2. **Terminal UI Foundation (Phase 4)** ✅
   - Textual-based modern TUI with responsive grid layout
   - Phase state management with full lifecycle support
   - Color-coded status indicators and scrollable content
   - Async-first architecture for smooth performance

3. **Token Streaming (Phase 5)** ✅
   - Real-time LLM token streaming to terminal UI
   - Phase cancellation with clean abort handling
   - Concurrent generation of multiple phases
   - Regeneration with steering feedback support
   - **Phase-specific streaming control** - users can now enable/disable streaming per phase (Design, DevPlan, Handoff)
   - 63 tests passing (56 unit + 7 integration)

**📊 Project Status:**
- 5 of 11 phases complete (45% of terminal UI roadmap)
- Production-ready interview mode and streaming foundation
- Comprehensive test coverage with zero diagnostics
- Ready for rendering enhancements and fullscreen viewer

## Why Devussy
- Multi-stage pipeline: Design → Basic DevPlan → Detailed DevPlan (per-phase files) → Handoff
- Interview mode: Analyzes existing codebases and generates context-aware devplans through LLM-driven conversation
- Provider-agnostic: OpenAI, Generic OpenAI-compatible, Requesty, Aether AI, AgentRouter
- Fast: Async concurrency for phase generation
- Resumable: Checkpoints you can list/resume/clean
- Great UX: Live spinners, per-phase progress bar, persistent status line with model & token usage
- Terminal UI (in progress): Real-time streaming of 5 phases with live token output and cancellation support
- **Phase-Specific Streaming**: Control streaming per phase (Design, DevPlan, Handoff) with intelligent fallback behavior
- Git-friendly: Write artifacts deterministically to docs/, optionally commit with your own workflow

## Install (from GitHub)

Option A: clone + editable install
```bash
git clone https://github.com/mojomast/devussy.git
cd devussy
pip install -e .
```

Option B: direct from Git
```bash
pip install "git+https://github.com/mojomast/devussy.git#egg=devussy"
```

Then verify:
```bash
python -m src.cli version
```

## Configure API keys
Create a .env file (or set env vars directly). Keys can also be set in-app via Settings → Provider & Models and are persisted per provider.

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Generic OpenAI-compatible
GENERIC_API_KEY=...
GENERIC_BASE_URL=https://api.your-openai-compatible.com/v1

# Requesty
REQUESTY_API_KEY=...
# Optional (default: https://router.requesty.ai/v1)
# REQUESTY_BASE_URL=https://router.requesty.ai/v1

# Aether AI
AETHER_API_KEY=...
# Optional (default: https://api.aetherapi.dev)
# AETHER_BASE_URL=https://api.aetherapi.dev

# AgentRouter
AGENTROUTER_API_KEY=...
# Optional (default: https://agentrouter.org/)
# AGENTROUTER_BASE_URL=https://agentrouter.org/
```
You can also set per-stage keys in config or via env if desired.

## Quick start

Interactive single-window workflow (recommended):
```bash
python -m src.cli interactive
```
- Runs fully in your current terminal.
- Step 1: console-based LLM interview (type /done when finished).
- Step 2: project design streams live to the console (prefix "[design] ").
- Step 3: basic devplan streams live to the console (prefix "[devplan] ").
- Step 4: a Textual terminal UI opens and streams all five phases (plan, design, implement, test, review) in parallel.

Interview-only launcher (legacy LLM-driven interview):
```bash
python -m src.entry
```
- Runs the original interactive design interview and pipeline in a more traditional flow.
- Streaming for design/devplan is controlled by config.streaming_enabled; for the full streaming UX, prefer the interactive command above.

Full pipeline (non-interactive):
```bash
python -m src.cli run-full-pipeline \
  --name "My Web App" \
  --languages "Python,TypeScript" \
  --requirements "Build a REST API with auth" \
  --frameworks "FastAPI,React"
```

## Providers & models
You can override provider/model on the CLI or via config. You can also manage them in the app via Settings → Provider & Models.
```bash
# OpenAI default
--provider openai --model gpt-4

# OpenAI-compatible
export GENERIC_BASE_URL="https://api.example.com/v1"
export GENERIC_API_KEY=...
--provider generic --model gpt-4o-mini

# Aether AI
export AETHER_API_KEY=...
--provider aether --model gpt-4o

# AgentRouter
export AGENTROUTER_API_KEY=...
--provider agentrouter --model gpt-4o
```
You can also align stages or set stage-specific models in config; Devussy will create stage clients accordingly.

### Unified model picker
- Devussy aggregates available models from all configured providers that have API keys.
- Picking a model automatically switches the active provider.
- Aether and other OpenAI-compatible providers use `GET /v1/models` for discovery.

### Base URLs and defaults
- OpenAI: `https://api.openai.com/v1`
- Requesty: `https://router.requesty.ai/v1`
- Aether: `https://api.aetherapi.dev` (client appends `/v1` automatically for API calls)
- AgentRouter: `https://agentrouter.org/`
- Generic: you must provide a base URL.

## Checkpoints
Devussy saves checkpoints between stages so you can resume.
```bash
python -m src.cli list-checkpoints
# Resume using a key printed by the pipeline, e.g. <project>_pipeline
# python -m src.cli run-full-pipeline --resume-from "myproj_pipeline"

python -m src.cli delete-checkpoint <key>
python -m src.cli cleanup-checkpoints --keep 5
```

## Configuration (basics)
Main defaults live in config/config.yaml when generated by init-repo. Useful fields:
- llm.provider, llm.model, llm.temperature, llm.max_tokens
- max_concurrent_requests
- streaming_enabled (global)
- git.* (optional behaviors if you add automation)

### Phase-Specific Streaming Options 🎯
Devussy now supports **granular streaming control** for each phase of the development pipeline:

#### How It Works
Each phase (Design, DevPlan, Handoff) can have streaming enabled or disabled independently. The system uses intelligent fallback behavior:

**Priority Order:**
1. **Phase-specific setting** (if explicitly set)
2. **Global streaming setting** (fallback)
3. **Config file setting** (fallback)
4. **Disabled** (default)

#### Accessing Streaming Options
- **Settings Menu**: Go to **Settings → Streaming Options** for interactive configuration
- **Individual Phase Control**: Configure streaming separately for:
  - Design Phase Streaming
  - DevPlan Phase Streaming
  - Handoff Phase Streaming
  - Global Streaming (affects all phases)

#### Environment Variables
You can also control streaming via environment variables:
```bash
# Phase-specific streaming
STREAMING_DESIGN_ENABLED=true
STREAMING_DEVPLAN_ENABLED=false
STREAMING_HANDOFF_ENABLED=true

# Global streaming (fallback)
STREAMING_ENABLED=true
```

#### When to Use Streaming
- **Design Phase**: Recommended enabled (fast, good UX feedback)
- **DevPlan Phase**: Optional (depends on preference for real-time progress)
- **Handoff Phase**: Recommended enabled (typically fast generation)

### Concurrency & phase parallelism
- `max_concurrent_requests` controls both how many API calls are in flight and how many DevPlan phases are generated in parallel during the detailed-devplan stage.
- Default is `5`, which means up to five phases are expanded at once after the design is nailed.
- You can change this via:
  - config: `config/config.yaml` → `max_concurrent_requests`
  - environment: `MAX_CONCURRENT_REQUESTS=8 python -m src.cli ...`
  - interactive settings: open **Settings → Concurrency / Parallel Phases** and set *Max concurrent API requests / phases*.

## Developing

### Test layout

All tests now live under the `tests/` directory:

- `tests/unit/` – unit tests for core pipeline and helpers
- `tests/integration/` – end-to-end and higher-level tests
- `tests/legacy/` – top-level tests that previously lived in the repo root (e.g. `test_complete_fix.py`, `test_streaming_duplication_fix.py`, etc.)

When adding new tests, prefer placing them in `tests/unit/` or `tests/integration/` rather than the repository root.

### Running tests

```bash
# run tests
pytest -q

# lint/format
black src && isort src && flake8 src
```

### Dev archive

Legacy Devussy docs, handoff summaries, and helper scripts have been moved into `devarchive/` to keep the repo root clean. This includes files like:

- `DEVUSSYPLAN.md`, `devussy-complete-plan.md`, `devussyhandoff.md`
- `INTERACTIVE_FIXES_SUMMARY.md`, `INTERACTIVE_IMPLEMENTATION.md`, `RELEASE-01-SUMMARY.md`
- `SINGLE_WINDOW_MODE.md`, `handoff-cleanup-guide.md`, `devplan.md.bak`
- Setup and helper scripts: `setup-new-repo.ps1`, `start-backend.ps1`, `sitecustomize.py`

These are kept for historical reference but are not required for the current 0.3 workflow.

## Recent Updates (Session 11)

- Hardened interactive single-window streaming:
  - Fixed coroutine-not-awaited warnings by using synchronous token callbacks in project design and basic devplan generators.
  - Ensured console streaming for design and devplan via StreamingHandler (token prefixes [design] and [devplan]).
  - Fixed nested asyncio.run() errors by running the Textual terminal UI from interactive in a background thread.
- Updated docs (README, DEVUSSYPLAN.md, devussyhandoff.md) to describe the console-based interview + streaming design/devplan + terminal UI phases workflow.

## Recent Updates (Session 5)

**Phase 5: Token Streaming Integration ✅**
- Implemented real-time LLM token streaming to terminal UI
- Created `TerminalPhaseGenerator` for streaming phase generation
- Added phase cancellation support with abort events
- Implemented concurrent generation of multiple phases
- Added regeneration with steering feedback support
- Created 12 comprehensive unit tests (all passing)
- Created integration test script for end-to-end validation
- Installed Textual library (v6.6.0) for terminal UI
- All 63 tests passing (56 unit + 7 integration)

**Previous Updates (Session 3):**

**Bug Fixes:**
- Fixed LLM client config access bug (all clients were incorrectly accessing `self._config.llm` instead of `self._config`)
- Corrected timeout and parameter access in OpenAI, Requesty, Aether, AgentRouter, and Generic clients
- All 51 tests passing with no diagnostics

**Testing:**
- Added comprehensive integration test script (`scripts/test_full_interview_flow.py`)
- Validates repository analysis, code extraction, interview manager, and LLM integration
- Confirms project context feature works end-to-end

**Documentation:**
- Updated README with current status and bug fixes
- Marked Interview Mode as complete
- Updated Terminal UI status with Phase 4 completion details

## Complete Feature List

### Interview Mode (Phases 1-3) ✅
**Repository Analysis Engine:**
- Detects project type (Python, Node, Go, Rust, Java)
- Analyzes directory structure (src, tests, config, CI)
- Parses dependencies from manifest files
- Calculates code metrics (files, lines, complexity)
- Detects patterns (test frameworks, build tools)
- Extracts configuration files

**LLM-Driven Interview:**
- Context-aware questioning based on repo analysis
- Project summary display before interview
- Interactive conversation with natural language
- Slash commands (/done, /help, /settings)
- Persistent settings per provider

**Code Sample Extraction:**
- Architecture samples (key structural files)
- Pattern examples (coding conventions)
- Relevant files based on stated goals
- Representative test files
- Integrated into all pipeline stages

**Context-Aware DevPlan Generation:**
- Repo context threaded through all generators
- Interview answers incorporated into prompts
- Code samples included for LLM context
- Backward compatible (works without repo analysis)

### Terminal UI (Phases 4-5) ✅
**Foundation (Phase 4):**
- Responsive grid layout (5 cols / 3x2 / 1x5)
- Phase state management with full lifecycle
- Color-coded status indicators
- Scrollable content areas
- Built with Textual (async-first)
- Keybindings (q=Quit, ?=Help, c=Cancel, f=Fullscreen)

**Token Streaming (Phase 5):**
- Real-time LLM token streaming to UI
- Phase cancellation with abort events
- Concurrent generation of multiple phases
- Regeneration with steering feedback
- Periodic UI updates (100ms interval)
- Integration with all LLM providers

### Core Pipeline Features ✅
- Multi-stage pipeline (Design → DevPlan → Handoff)
- Provider-agnostic (OpenAI, Requesty, Aether, AgentRouter, Generic)
- Async concurrency for phase generation
- Resumable with checkpoint system
- Live progress indicators and status line
- Per-phase progress bar with token usage
- Deterministic artifact generation to docs/
- Optional git integration
- Pre-review option for design validation

### Testing & Quality ✅
- 63 tests passing (56 unit + 7 integration)
- Comprehensive test coverage
- Zero diagnostics or syntax errors
- Integration tests for full workflows
- Real-world validation with actual APIs

## Troubleshooting
- No output files? Ensure the appropriate provider key is set (OPENAI_API_KEY, AETHER_API_KEY, REQUESTY_API_KEY, AGENTROUTER_API_KEY, or GENERIC_API_KEY).
- Status line missing? Make sure your terminal supports ANSI; non-TTY environments will still print stage lines and progress.
- Aether 404 for `/chat/completions`? Ensure Base URL is `https://api.aetherapi.dev` (the client automatically calls `/v1/chat/completions`).
- Model not found? Use the unified model picker to select a valid model for the active provider.
- LLM client errors? All clients have been updated to correctly access config parameters (fixed in Session 3)

## Release branches
- `release-0.1`: initial circular-dev and anchor-based optimization work.
- `release-01`: tracked release branch for the first public cut of the optimized pipeline and docs.

## License
MIT
