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
• Version: 0.1.1

## Why Devussy
- Multi-stage pipeline: Design → Basic DevPlan → Detailed DevPlan (per-phase files) → Handoff
- Provider-agnostic: OpenAI, Generic OpenAI-compatible, Requesty, Aether AI, AgentRouter
- Fast: Async concurrency for phase generation
- Resumable: Checkpoints you can list/resume/clean
- Great UX: Live spinners, per-phase progress bar, persistent status line with model & token usage
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
  2) phase.md (the active phase file) — summarize outcomes and blockers
  3) handoff (handoff_prompt.md or prompt content) — brief status and next steps

Use these anchors so any model can reliably update the right sections:

- In devplan.md:
  - <!-- PROGRESS_LOG_START --> ... <!-- PROGRESS_LOG_END -->
  - <!-- NEXT_TASK_GROUP_START --> ... <!-- NEXT_TASK_GROUP_END -->
- In the current phase file (phaseX.md):
  - <!-- PHASE_PROGRESS_START --> ... <!-- PHASE_PROGRESS_END -->
- In handoff (handoff_prompt.md or the generated prompt):
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

## Core commands

Initialize a new repo with a docs/ folder and templates:
```bash
python -m src.cli init-repo ./my-project
```

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

## Developing
```bash
# run tests
pytest -q

# lint/format
black src && isort src && flake8 src
```

## Troubleshooting
- No output files? Ensure the appropriate provider key is set (OPENAI_API_KEY, AETHER_API_KEY, REQUESTY_API_KEY, AGENTROUTER_API_KEY, or GENERIC_API_KEY).
- Status line missing? Make sure your terminal supports ANSI; non-TTY environments will still print stage lines and progress.
- Aether 404 for `/chat/completions`? Ensure Base URL is `https://api.aetherapi.dev` (the client automatically calls `/v1/chat/completions`).
- Model not found? Use the unified model picker to select a valid model for the active provider.

## License
MIT
