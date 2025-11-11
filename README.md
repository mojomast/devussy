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

## Why Devussy
- Multi-stage pipeline: Design → Basic DevPlan → Detailed DevPlan (per-phase files) → Handoff
- Provider-agnostic: OpenAI and OpenAI-compatible endpoints (plus “Requesty”)
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
devussy version
```

## Configure API keys
Create a .env file (or set env vars directly):
```bash
OPENAI_API_KEY=sk-...
# Optional for custom endpoints:
# GENERIC_API_KEY=...
# GENERIC_BASE_URL=https://api.your-openai-compatible.com/v1
# REQUESTY_API_KEY=...
```
You can also set per-stage keys in config or via env if desired.

## Quick start

Interactive interview (LLM-driven):
```bash
devussy interactive-design
```
- Type answers or use slash-commands like /done, /help, /settings.
- The bottom status line shows model and token usage and remains active through generation.

Full pipeline (non-interactive):
```bash
devussy run-full-pipeline \
  --name "My Web App" \
  --languages "Python,TypeScript" \
  --requirements "Build a REST API with auth" \
  --frameworks "FastAPI,React"
```
Outputs (in docs/ by default):
- project_design.md
- devplan.md (+ phase1.md … phaseN.md)
- handoff_prompt.md

## What you’ll see (UX)
- Stage spinners while each phase runs
- A per-phase progress bar during detailed plan generation (updates as phases finish)
- A persistent bottom status line showing current stage, model, and token usage (prompt/completion/total + accumulated)

## Launch (0.1 Requesty-focused)

This 0.1 release is tailored for Requesty. If a Requesty key isn’t detected, you’ll be prompted at startup.

Run the interview with Requesty in one command:
```bash
devussy launch
```
Or via Python module entry:
```bash
python -m src.entry
```
Options:
- `--provider` to override (defaults to requesty for 0.1)

The launcher will:
- ensure REQUESTY_API_KEY is set (prompts if missing)
- open the LLM-driven interview

## Core commands

Initialize a new repo with a docs/ folder and templates:
```bash
devussy init-repo ./my-project
```

Interactive design interview (recommended):
```bash
devussy interactive-design
```

One-shot full pipeline:
```bash
devussy run-full-pipeline --name "My App" --languages "Python" --requirements "Build an API"
```

Only design:
```bash
devussy generate-design --name "My App" --languages "Python" --requirements "Build an API"
```

Only devplan from an in-memory design (advanced) or resume via checkpoints (see below).

## Providers & models
You can override provider/model on the CLI or via config:
```bash
# OpenAI default
--provider openai --model gpt-4

# OpenAI-compatible
export GENERIC_BASE_URL="https://api.example.com/v1"
export GENERIC_API_KEY=...
--provider generic --model gpt-4o-mini
```
You can also align stages or set stage-specific models in config; Devussy will create stage clients accordingly.

## Checkpoints
Devussy saves checkpoints between stages so you can resume.
```bash
devussy list-checkpoints
# Resume using a key printed by the pipeline, e.g. <project>_pipeline
# devussy run-full-pipeline --resume-from "myproj_pipeline"

devussy delete-checkpoint <key>
devussy cleanup-checkpoints --keep 5
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
- No output files? Ensure OPENAI_API_KEY (or your provider’s key) is set.
- Status line missing? Make sure your terminal supports ANSI; non-TTY environments will still print stage lines and progress.
- Custom endpoints: confirm GENERIC_BASE_URL and GENERIC_API_KEY are set and the server is OpenAI-compatible.

## License
MIT
