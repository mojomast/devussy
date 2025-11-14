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

Interactive interview (LLM-driven):
```bash
python -m src.entry
```
- Type answers or use slash-commands like /done, /help, /settings.
- The bottom status line shows model and token usage and remains active through generation.
- After design is generated, confirm the prompt to continue and you'll see streaming progress
  for DevPlan (including a per-phase progress bar with ✓ as phases complete) and Handoff.

Full pipeline (non-interactive):
```bash
python -m src.cli run-full-pipeline \
  --name "My Web App" \
  --languages "Python,TypeScript" \
  --requirements "Build a REST API with auth" \
  --frameworks "FastAPI,React"
```
Outputs (in docs/ by default):
- project_design.md
- devplan.md (+ phase1.md … phaseN.md)
- handoff_prompt.md

### Mandatory update ritual (after every N tasks)

To keep all models in sync, Devussy enforces a simple update ritual. After completing a group of tasks, pause to update the artifacts, then continue.

- Task group size: configurable; defaults to 3 for devplan generation and 5 for handoff prompts
- After each group, update all three locations before proceeding:
  1) devplan.md — add progress and next tasks
  2) phaseX.md (the active phase file) — summarize outcomes and blockers
  3) handoff_prompt.md — brief status and next steps

Use these anchors so any model can reliably update the right sections:

- In devplan.md:
  - <!-- PROGRESS_LOG_START --> ... <!-- PROGRESS_LOG_END -->
  - <!-- NEXT_TASK_GROUP_START --> ... <!-- NEXT_TASK_GROUP_END -->
- In the current phase file (phaseX.md):
  - <!-- PHASE_PROGRESS_START --> ... <!-- PHASE_PROGRESS_END -->
- In handoff_prompt.md:
  - <!-- HANDOFF_NOTES_START --> ... <!-- HANDOFF_NOTES_END -->

If a file doesn’t exist, create it and include the anchors.

Example (devplan.md):

```
<!-- PROGRESS_LOG_START -->
- Completed 2.1 Implement DB schema – added tables, indexes, migration file
- Completed 2.2 Connection manager – pooled connections, retry, logging
<!-- PROGRESS_LOG_END -->

<!-- NEXT_TASK_GROUP_START -->
- 2.3: Write unit tests for DB layer
- 2.4: Code quality checks (black/flake8/isort)
- 2.5: Commit changes (feat: db layer)
<!-- NEXT_TASK_GROUP_END -->
```

### Configure task group size

Programmatic API:
- Basic plan generation: BasicDevPlanGenerator.generate(..., task_group_size=3)
- Detailed plan generation: DetailedDevPlanGenerator.generate(..., task_group_size=3)
- Handoff prompt: HandoffPromptGenerator.generate(..., task_group_size=5)

CLI: the default group sizes apply unless you integrate a flag in your own wrapper.

## What you’ll see (UX)
- Stage spinners while each phase runs
- A per-phase progress bar during detailed plan generation (updates as phases finish)
- A persistent bottom status line showing current stage, model, and token usage (prompt/completion/total + accumulated)
- The interactive “continue” flow uses the same streaming UI for DevPlan and Handoff

## Launch

From a clone (no pip install):
```bash
git clone https://github.com/mojomast/devussy.git
cd devussy
python -m src.entry
```

At startup, Devussy applies your last-used preferences automatically (provider, per-provider API keys, base URLs). You can change them anytime under Settings → Provider & Models. Only the Generic provider prompts for a Base URL; others use safe defaults.

## Interview Mode ✅ COMPLETE

Devussy can analyze your existing codebase and conduct an LLM-driven interview to generate a context-aware devplan:

```bash
python -m src.cli interview .
```

This will:
1. Analyze your project structure, dependencies, and patterns (supports Python, Node, Go, Rust, Java)
2. Display a summary of your repository (files, lines, dependencies, frameworks)
3. Conduct an interactive interview about your development goals
4. Extract relevant code samples from your codebase (architecture, patterns, tests)
5. Generate a devplan that respects your existing architecture

The interview uses natural conversation with an LLM, making it easy to describe what you want to build. Code samples and repository context are automatically included in the generated devplan.

**Features:**
- Automatic project type detection
- Dependency parsing for all major ecosystems
- Smart code sample extraction (entry points, patterns, tests, goal-relevant files)
- Repository context threaded through entire pipeline
- Backward compatible (works without repo analysis)

**Test it:**
```bash
# Analyze a repository
python -m src.cli analyze-repo . --json

# Full interview flow
python scripts/test_full_interview_flow.py
```

## Terminal UI 🚧 IN PROGRESS

Phases 4 & 5 are complete! The terminal UI provides:
- ✅ Responsive grid layout (5 cols / 3x2 / 1x5 based on terminal width)
- ✅ Phase state management with full lifecycle support
- ✅ Color-coded status indicators (idle, streaming, complete, interrupted, error, regenerating)
- ✅ Scrollable content areas for each phase
- ✅ Built with Textual for a modern, async-first TUI experience
- ✅ **Real-time token streaming from LLM to terminal (Phase 5 - NEW!)**
- ✅ **Phase cancellation with abort support**
- ✅ **Concurrent generation of multiple phases**
- 🚧 Interactive steering: cancel, feedback, regenerate (Phase 7)
- 🚧 Fullscreen viewer for detailed phase content (Phase 6)

Try the demos:
```bash
# Basic UI demo with simulated streaming
python scripts/demo_terminal_ui.py

# Real LLM streaming integration test
python scripts/test_streaming_integration.py
```

**Current Status (Session 5):**
- All 63 tests passing (56 unit + 7 integration)
- Phase 5 token streaming fully implemented and tested
- Real-time LLM streaming to terminal UI working end-to-end
- Phase cancellation with clean abort handling
- Concurrent phase generation with asyncio
- UI with keybindings (q=Quit, ?=Help, c=Cancel, f=Fullscreen)
- Ready for rendering enhancements and fullscreen viewer

## Core commands

Initialize a new repo with a docs/ folder and templates:
```bash
python -m src.cli init-repo ./my-project
```

Optional pre‑review (fix design before planning):
```bash
python -m src.cli run-full-pipeline \
  --name "My App" \
  --languages "Python" \
  --requirements "Build an API" \
  --pre-review
```
This sends the freshly generated design to the DevPlan (phase 2) model to detect and fix compatibility/workflow/backend/efficiency issues before generating the devplan. A report is saved to docs/design_review.md and improvements are applied automatically if returned.

Interactive design interview (recommended):
```bash
python -m src.cli interactive-design
```
After the interview, confirm the “Proceed to run full pipeline now?” prompt to stream
DevPlan and Handoff progress live in your terminal.

One-shot full pipeline:
```bash
python -m src.cli run-full-pipeline --name "My App" --languages "Python" --requirements "Build an API"
```

Only design:
```bash
python -m src.cli generate-design --name "My App" --languages "Python" --requirements "Build an API"
```

Only devplan from an in-memory design (advanced) or resume via checkpoints (see below).

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
- streaming_enabled
- git.* (optional behaviors if you add automation)

### Concurrency & phase parallelism
- `max_concurrent_requests` controls both how many API calls are in flight and how many DevPlan phases are generated in parallel during the detailed-devplan stage.
- Default is `5`, which means up to five phases are expanded at once after the design is nailed.
- You can change this via:
  - config: `config/config.yaml` → `max_concurrent_requests`
  - environment: `MAX_CONCURRENT_REQUESTS=8 python -m src.cli ...`
  - interactive settings: open **Settings → Concurrency / Parallel Phases** and set *Max concurrent API requests / phases*.

## Developing
```bash
# run tests
pytest -q

# lint/format
black src && isort src && flake8 src
```

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
