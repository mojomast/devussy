<div align="center">
  <img src="docs/assets/devussy_logo.png" alt="Devussy Logo" width="100%">
</div>

# Devussy

compose. code. conduct.

Devussy turns a short project idea into a complete, actionable development plan. It interviews you (or reads flags), drafts a project design, expands it into a detailed multi-phase DevPlan with per-step tasks, and produces a handoff document—saving everything as markdown you can check in.

• Repo: https://github.com/mojomast/devussy
• Python: 3.9+
• Version: 0.3.0 (Commit Stage)

## At a Glance

- **CLI / TUI pipeline**
  - `python -m src.cli interactive` for single-window interactive workflows (interview → design → devplan → handoff).
  - `python -m src.cli run-full-pipeline` for non-interactive, scriptable runs.
- **Repo-aware interview**
  - Automatically analyzes existing repositories and feeds structure, dependencies, and patterns into the LLM-driven interview.
  - Code samples and repo context are threaded through all generators.
- **Phase-specific streaming & concurrency**
  - Fine-grained streaming toggles for Design / DevPlan / Handoff, with a clear priority model.
  - `max_concurrent_requests` controls both API concurrency and how many phases are expanded in parallel.
- **Checkpoint & resume support**
  - Checkpoints between stages; list, resume, and clean them from the CLI.
- **Web UI (Next.js desktop-in-browser)**
  - Multi-window pipeline UI with AppRegistry, EventBus, IRC integration, and share links.
- **Provider-agnostic LLM layer**
  - OpenAI, Generic OpenAI-compatible, Requesty, Aether AI, AgentRouter; unified model picker and per-stage LLM configs.
- **UI preferences & settings**
  - Last-used provider, models, streaming flags, and experimental toggles are stored in `.devussy_state/ui_prefs.json` and applied automatically on startup.

## What's New in Commit Stage 0.3.0

**� Interview experience: real design review, not a second interview**

- Added a dedicated **Design Review mode** to `LLMInterviewManager`.
- The "Design Review Opportunity" in the interactive flow now:
  - Loads the generated design (and optional devplan / repo summary) as **markdown context**.
  - Starts a focused **design-review conversation** instead of re-asking basic questions.
  - Guides the user to refine architecture, constraints, tech stack, and risks.
- At the end of the review, Devussy extracts a **compact JSON summary** (updated requirements, new constraints, tech changes, risks, notes).
- That summary is merged back into the design inputs and the design is **regenerated with the adjustments applied**.

**🧭 Single-window interactive workflow polish**

- "Start" → interview → design → design-review (optional) → devplan now runs as a **single, progress-aware flow**.
- Streaming handlers prefix tokens in the console (`[design]`, `[devplan]`) for easy scanning.
- The Textual terminal UI still runs in its own thread to avoid nested `asyncio.run()` issues on Windows.

**📡 Streaming and configuration improvements**

- Phase-specific streaming flags for **Design / DevPlan / Handoff** with a clear priority model:
  1. Phase-specific flag
  2. Global streaming flag
  3. Config fallback
  4. Disabled
- New **Streaming Options** menu in Settings lets you toggle phases individually without touching config files.
- Concurrency controls now live in Settings as well (max concurrent API requests / phases).

**📊 Backend web analytics (server-side, opt-out supported)**

- Added a lightweight **server-side analytics module** behind the FastAPI streaming server.
- Tracks anonymized sessions (hashed IP + user-agent), API calls (endpoint, method, status, latency, sizes), and design inputs for the web UI.
- All analytics are kept **on the server only** (SQLite), with a simple `/api/analytics/overview` endpoint for internal inspection.
- Users can set a **“Disable anonymous usage analytics for this browser”** toggle in the Help window, which writes a `devussy_analytics_optout` cookie; when set, both the middleware and design endpoint completely skip analytics logging.

**🧱 Under-the-hood fixes**

- Hardened `LLMInterviewManager` to be explicitly mode-aware (`initial` vs `design_review`).
- Added helpers to safely parse the LLM's JSON feedback from the conversation history.
- Reduced emoji usage in low-level console banners to avoid Windows encoding issues.

**📊 Project Status (CLI / TUI engine)**

- Interview mode and design-review loop are **production-ready** for day-to-day use.
- Streaming and terminal UI foundations are in place; remaining work is mostly visual and workflow polish.

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

## Frontend Web UI (Next.js) 🆕

Devussy now includes a **Next.js-based web frontend** (`devussy-web/`) that provides a multi-window streaming interface for the entire pipeline.

### Features
- **Multi-Window Architecture**: Each pipeline phase spawns its own draggable, minimizable window
- **Real-Time Streaming**: Design and Plan generation stream in real-time using Server-Sent Events (SSE)
- **Premium UI**: Built with Tailwind CSS, Shadcn UI components, and Framer Motion animations
- **Model Configuration**: Per-stage model selection with global defaults
- **Direct Backend Integration**: Bypasses Next.js proxy for optimal streaming performance

### Quick Start
```bash
# Terminal 1: Start Python backend
cd devussy-testing
python devussy-web/dev_server.py

# Terminal 2: Start Next.js frontend
cd devussy-web
npm run dev
```
Then visit `http://localhost:3000` to access the web interface.

**Web UI Features:**
- **Interactive Pipeline**: Full visual flow from Interview to Handoff.
- **HiveMind**: Multi-agent swarm generation for robust planning.
- **Checkpoints**: Save and load your progress at any stage directly from the toolbar.
- **Live Streaming**: Real-time token streaming for all generation phases.
- **GitHub Integration**: Push your generated design, plan, and documentation directly to a new private GitHub repository.

### Recent Updates (2025-11-19)
- ✅ HiveMind UI streaming integration complete (multi-agent swarm generation)
- ✅ Fixed "Approve & Plan" button enablement after Design generation
- ✅ Implemented SSE streaming for Plan generation to prevent connection timeouts
- ✅ Direct backend connection (port 8000) bypasses Next.js buffering
- ✅ **Window Management**: Auto-open New Project, improved default sizes, Help system integration
- ✅ **Handoff Fixes**: Resolved 500 errors, fixed async/await issues, ensured full design content in zip
- ✅ **Checkpoint Loading**: Fixed issue where loading 'handoff' stage reset to start screen
- ✅ **App Framework**: `AppRegistry` now drives default window sizes, Start menu entries, and registry-driven apps (IRC, Help, Model Settings) in the web UI.
- ✅ **Event Bus (MVP)**: A frontend `EventBus` + React context is wired into the window manager; the pipeline emits a `planGenerated` event that the IRC app listens to and posts into `#devussy-chat`.
- See `devussy-web/handoff.md` for detailed status and next steps

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
# Optional: Spoof as a specific model/provider
# AGENTROUTER_SPOOF_AS=claude-code
```
You can also set per-stage keys (e.g., `DESIGN_API_KEY`, `DEVPLAN_API_KEY`) in config or via env if desired.

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

### UI Preferences & Settings

- Devussy persists interactive settings (provider, interview / final-stage models, streaming flags, repository tools, and various experimental toggles) via a small JSON blob managed by `StateManager`:
  - Location by default: `.devussy_state/ui_prefs.json` or the directory pointed to by `DEVUSSY_STATE_DIR`.
  - Loaded on startup in `_apply_last_prefs_to_config` and applied with `apply_settings_to_config`.
- This means:
  - The **Settings → Models & Provider / Streaming / Concurrency** menus act as the primary source of truth for future runs.
  - CLI commands like `interactive_design` and `interactive` automatically respect your last-used provider, base URLs, and timeouts unless explicitly overridden by flags.

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

Additional integration tests for the **web app framework & IRC integration** live under `tests/integration/` and can be run individually, for example:

```bash
pytest tests/integration/test_compose_generator.py -v
pytest tests/integration/test_share_links_flow.py -v
pytest tests/integration/test_event_bus_notifications.py -v
pytest tests/integration/test_window_manager_registry.py -v
```

These tests exercise the `devussy-web` app framework features end-to-end, including the compose/nginx generator, share link helpers and `/share` route wiring, typed EventBus/AppContext notifications, and AppRegistry/window manager invariants.

### Dev archive

Legacy Devussy docs, handoff summaries, and helper scripts have been moved into `devarchive/` to keep the repo root clean. This includes files like:

- `DEVUSSYPLAN.md`, `devussy-complete-plan.md`, `devussyhandoff.md`
- `INTERACTIVE_FIXES_SUMMARY.md`, `INTERACTIVE_IMPLEMENTATION.md`, `RELEASE-01-SUMMARY.md`
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
